import math
from collections import deque
from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class TrainSpec:
    name: str = "Standard_EMU_6Car"
    mass_ton: float = 180.0          # 공차+승객 중량 (ton)
    length_m: float = 120.0          # 열차 편성 길이 (m, 예: 6량 약 120m)
    rotational_factor: float = 1.08  # 회전 질량 계수
    max_speed_kmh: float = 80.0      # 영업 최고속도 (km/h)
    max_accel_ms2: float = 0.83      # 기동 가속도 (3.0 km/h/s)
    service_decel_ms2: float = 0.97  # 상용 최대 감속도 (3.5 km/h/s)
    base_power_kw: float = 1400.0    # 정격 출력 (kW)
    motor_efficiency: float = 0.88   # 견인전동기/인버터 효율
    regen_efficiency: float = 0.35   # 회생제동 회수율

class AdvancedUrbanTPS:
    def __init__(self, train: TrainSpec, total_length_m: int):
        self.train = train
        self.length = total_length_m
        self.gradient = [0.0] * (total_length_m + 1)
        self.curve_r = [float('inf')] * (total_length_m + 1)
        self.speed_limit = [train.max_speed_kmh] * (total_length_m + 1)

        # 열차 길이를 반영한 실효 선형 캐시
        self._eff_gradient: Optional[List[float]] = None
        self._eff_inv_r: Optional[List[float]] = None
        self._eff_speed_limit: Optional[List[float]] = None

    def set_track_segment(
        self, start_m: int, end_m: int,
        grad: float = 0.0, radius: float = float('inf'), limit: Optional[float] = None
    ):
        for x in range(max(0, start_m), min(self.length + 1, end_m + 1)):
            self.gradient[x] = grad
            self.curve_r[x] = radius
            if limit is not None:
                self.speed_limit[x] = min(self.speed_limit[x], limit)
        self._invalidate_cache()

    def _invalidate_cache(self):
        self._eff_gradient = None
        self._eff_inv_r = None
        self._eff_speed_limit = None

    def prepare_track(self):
        """
        열차 편성 길이(train.length_m)를 반영한 실효 구배, 실효 곡률(1/R), 실효 제한속도 사전 계산.
        선두부 위치 x 기준 [max(0, x - L), x] 구간에 대해 구배·곡률은 평균, 제한속도는 최솟값을 적용.
        """
        n = self.length + 1
        train_len = max(0, int(round(self.train.length_m)))

        if train_len <= 1:
            self._eff_gradient = list(self.gradient)
            self._eff_inv_r = [
                (1.0 / r if (not math.isinf(r) and r > 0) else 0.0)
                for r in self.curve_r
            ]
            self._eff_speed_limit = list(self.speed_limit)
            return

        # 1) 누적합(Prefix Sum)으로 [max(0, x - L), x] 구배·곡률 평균 O(N) 계산
        pref_grad = [0.0] * (n + 1)
        pref_inv_r = [0.0] * (n + 1)
        for i in range(n):
            pref_grad[i + 1] = pref_grad[i] + self.gradient[i]
            r = self.curve_r[i]
            inv_r = (1.0 / r) if (not math.isinf(r) and r > 0) else 0.0
            pref_inv_r[i + 1] = pref_inv_r[i] + inv_r

        eff_grad = [0.0] * n
        eff_inv_r = [0.0] * n
        for x in range(n):
            lo = max(0, x - train_len)
            cnt = x - lo + 1
            eff_grad[x] = (pref_grad[x + 1] - pref_grad[lo]) / cnt
            eff_inv_r[x] = (pref_inv_r[x + 1] - pref_inv_r[lo]) / cnt

        # 2) 슬라이딩 윈도우 최솟값(Deque)으로 [max(0, x - L), x] 실효 제한속도 O(N) 계산
        eff_limit = [0.0] * n
        dq = deque()
        for x in range(n):
            lo = max(0, x - train_len)
            while dq and dq[0] < lo:
                dq.popleft()
            v = self.speed_limit[x]
            while dq and self.speed_limit[dq[-1]] >= v:
                dq.pop()
            dq.append(x)
            eff_limit[x] = self.speed_limit[dq[0]]

        self._eff_gradient = eff_grad
        self._eff_inv_r = eff_inv_r
        self._eff_speed_limit = eff_limit

    def _ensure_prepared(self):
        if self._eff_gradient is None or self._eff_inv_r is None or self._eff_speed_limit is None:
            self.prepare_track()

    def create_reversed(self, new_train: Optional[TrainSpec] = None) -> "AdvancedUrbanTPS":
        """
        상·하행 반전된 선형(x' = length - x, 구배 부호 반전)을 가지는 새 TPS 객체 반환
        """
        rev_train = new_train if new_train is not None else self.train
        rev = AdvancedUrbanTPS(rev_train, self.length)
        rev.gradient = [-g for g in reversed(self.gradient)]
        rev.curve_r = list(reversed(self.curve_r))
        rev.speed_limit = [min(lim, rev_train.max_speed_kmh) for lim in reversed(self.speed_limit)]
        rev.prepare_track()
        return rev

    def get_resistance_acc(self, x: int, v_ms: float) -> float:
        self._ensure_prepared()
        v_kmh = v_ms * 3.6
        # Davis 식(kgf/ton) -> 9.81을 곱해 N/ton으로 단위 통일
        r_run = 9.81 * (1.5 + 0.03 * v_kmh + 0.0005 * (v_kmh ** 2))
        r_grad = 9.81 * self._eff_gradient[x]
        r_curve = 9.81 * (600.0 * self._eff_inv_r[x])
        return (r_run + r_grad + r_curve) / (1000.0 * self.train.rotational_factor)

    def get_tractive_acc(self, v_ms: float) -> float:
        if v_ms < 0.1:
            return self.train.max_accel_ms2
        power_limit_force_n = (self.train.base_power_kw * 1000.0) / v_ms
        power_limit_acc = power_limit_force_n / (self.train.mass_ton * 1000.0 * self.train.rotational_factor)
        return min(self.train.max_accel_ms2, power_limit_acc)

    def compute_braking_profile(self, start_x: int, stop_x: int) -> List[float]:
        """start_x ~ stop_x 구간에 대한 역산 제동 속도 프로파일"""
        self._ensure_prepared()
        v_limit_ms = [v / 3.6 for v in self._eff_speed_limit]
        v_limit_ms[stop_x] = 0.0
        for x in range(stop_x - 1, start_x - 1, -1):
            v_next = v_limit_ms[x + 1]
            res_acc = self.get_resistance_acc(x, v_next)
            effective_decel = max(0.2, self.train.service_decel_ms2 + res_acc)
            v_allow = math.sqrt(v_next ** 2 + 2 * effective_decel * 1.0)
            v_limit_ms[x] = min(v_limit_ms[x], v_allow)
        return v_limit_ms

    def simulate_with_coast_point(
        self, start_x: int, stop_x: int, coast_start_x: float,
        min_remotoring_kmh: float = 35.0, record_history: bool = False
    ) -> Optional[Dict]:
        self._ensure_prepared()
        brake_profile = self.compute_braking_profile(start_x, stop_x)
        dt = 0.1
        t = 0.0
        x = float(start_x)
        v = 0.0
        energy_joules = 0.0
        effective_mass_kg = self.train.mass_ton * 1000.0 * self.train.rotational_factor
        history = []
        is_coasting = False

        while x < stop_x and t < 1800:
            idx = min(int(x), stop_x)
            v_brake_limit = brake_profile[idx]
            v_track_limit = self._eff_speed_limit[idx] / 3.6
            is_braking_zone = (v_brake_limit < v_track_limit - 1e-3) or ((stop_x - x) < 10.0)

            if is_braking_zone and v >= v_brake_limit - 0.05:
                state = "BRAKE"
                res_acc = self.get_resistance_acc(idx, v)
                if idx + 1 <= stop_x:
                    target_v = brake_profile[idx + 1]
                    dx_rem = max(0.2, (idx + 1) - x)
                    acc = (target_v ** 2 - v ** 2) / (2.0 * dx_rem)
                    acc = max(-(self.train.service_decel_ms2 + max(0.0, res_acc)), min(0.0, acc))
                else:
                    acc = -(self.train.service_decel_ms2 + res_acc)
            elif x >= coast_start_x:
                # 히스테리시스: 35km/h 미만에서 재역행 후 45km/h 이상에서 다시 타행 진입
                if not is_coasting:
                    if v >= (min_remotoring_kmh + 10.0) / 3.6 or (stop_x - x) <= 150.0:
                        is_coasting = True
                else:
                    if v < (min_remotoring_kmh / 3.6) and (stop_x - x) > 150.0:
                        is_coasting = False

                if is_coasting:
                    state = "COAST"
                    acc = -self.get_resistance_acc(idx, v)
                else:
                    state = "POWER"
                    acc = self.get_tractive_acc(v) - self.get_resistance_acc(idx, v)
            else:
                if v >= v_track_limit - 0.05:
                    state = "CRUISE"
                    acc = 0.0
                else:
                    state = "POWER"
                    acc = self.get_tractive_acc(v) - self.get_resistance_acc(idx, v)

            v_next = max(0.0, v + acc * dt)
            dx = ((v + v_next) / 2.0) * dt
            x_next = x + dx

            res_acc_curr = self.get_resistance_acc(idx, v)
            if state in ("POWER", "CRUISE"):
                net_force = (acc + res_acc_curr) * effective_mass_kg
                if net_force > 0:
                    energy_joules += (net_force * dx) / self.train.motor_efficiency
                elif net_force < 0:
                    energy_joules += (net_force * dx) * self.train.regen_efficiency
            elif state == "BRAKE":
                brake_force = max(0.0, (-acc - res_acc_curr) * effective_mass_kg)
                energy_joules -= (brake_force * dx) * self.train.regen_efficiency

            if record_history:
                history.append((round(t, 1), round(x, 2), round(v * 3.6, 2), state))

            t += dt
            x = x_next
            v = v_next

            if v < 0.01 and t > 2.0 and (stop_x - x) > 2.0:
                return None
            if state == "BRAKE" and v < 0.05 and (stop_x - x) < 1.0:
                break

        if x < stop_x - 2.0:
            return None

        return {
            "travel_time_sec": round(t, 1),
            "coast_start_x": round(coast_start_x, 1),
            "energy_kwh": round(max(0.0, energy_joules / 3_600_000.0), 3),
            "avg_speed_kmh": round(((stop_x - start_x) / t) * 3.6, 1) if t > 0 else 0,
            "history": history
        }

    def optimize_coasting_for_target_time(
        self, start_x: int, stop_x: int, target_time_sec: Optional[float] = None,
        margin_ratio: float = 0.05, record_history: bool = False
    ) -> Dict:
        min_run = self.simulate_with_coast_point(start_x, stop_x, coast_start_x=stop_x, record_history=False)
        if min_run is None:
            raise ValueError(f"구간 ({start_x}m ~ {stop_x}m) 주행 시뮬레이션에 실패했습니다.")
        min_time = min_run["travel_time_sec"]

        if target_time_sec is None:
            target_time_sec = round(min_time * (1.0 + margin_ratio), 1)

        if target_time_sec <= min_time:
            if record_history:
                min_run = self.simulate_with_coast_point(start_x, stop_x, coast_start_x=stop_x, record_history=True)
            min_run["min_possible_time_sec"] = min_time
            min_run["target_time_sec"] = target_time_sec
            min_run["energy_saved_pct"] = 0.0
            return min_run

        low = float(start_x + 30.0)
        high = float(stop_x)
        best_res = min_run

        for _ in range(25):
            mid = (low + high) / 2.0
            res = self.simulate_with_coast_point(start_x, stop_x, coast_start_x=mid, record_history=False)
            if res is None or res["travel_time_sec"] > target_time_sec:
                low = mid
            else:
                high = mid
                best_res = res

        final_run = self.simulate_with_coast_point(
            start_x, stop_x, coast_start_x=best_res["coast_start_x"], record_history=record_history
        )
        saved_pct = round((1.0 - final_run["energy_kwh"] / min_run["energy_kwh"]) * 100.0, 1) if min_run["energy_kwh"] > 0 else 0.0
        final_run["min_possible_time_sec"] = min_time
        final_run["target_time_sec"] = target_time_sec
        final_run["energy_saved_pct"] = saved_pct
        return final_run