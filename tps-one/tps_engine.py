import math
from collections import deque
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple, Union

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
    # 실제 차량 F-v 견인력 곡선 테이블: [(속도_kmh, 견인력_kN), ...]
    # 지정 시 base_power_kw / max_accel_ms2 대신 이 테이블을 선형 보간하여 가속도 산출
    tractive_effort_table: Optional[List[Tuple[float, float]]] = None


def build_vvvf_tractive_table(
    mass_ton: float,
    rotational_factor: float = 1.08,
    max_accel_ms2: float = 0.83,
    base_power_kw: float = 2200.0,
    weak_field_start_kmh: float = 70.0,
    max_speed_kmh: float = 100.0,
    step_kmh: float = 5.0,
) -> List[Tuple[float, float]]:
    """
    표준 3영역 VVVF 전동차 F-v 견인력 테이블 생성 헬퍼:
    1) 정토크 영역 (0 ~ v_base): 기동 가속도 기반 일정 견인력
    2) 정출력 영역 (v_base ~ v_weak): F = P / v
    3) 특성영역/약계자 (v_weak ~ v_max): F ∝ 1 / v^2 (고속 가속력 저감 반영)
    """
    eff_mass_ton = mass_ton * rotational_factor
    f_max_kn = eff_mass_ton * max_accel_ms2
    v_weak_ms = weak_field_start_kmh / 3.6
    f_at_weak_kn = min(f_max_kn, base_power_kw / max(0.1, v_weak_ms))

    table: List[Tuple[float, float]] = []
    v_kmh = 0.0
    while v_kmh <= max_speed_kmh + 1e-6:
        if v_kmh < 0.5:
            f_kn = f_max_kn
        else:
            v_ms = v_kmh / 3.6
            if v_kmh <= weak_field_start_kmh:
                f_kn = min(f_max_kn, base_power_kw / v_ms)
            else:
                f_kn = min(f_max_kn, f_at_weak_kn * ((weak_field_start_kmh / v_kmh) ** 2))
        table.append((round(v_kmh, 1), round(f_kn, 2)))
        v_kmh += step_kmh

    return table


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
        self._sorted_fv_table: Optional[List[Tuple[float, float]]] = (
            sorted(train.tractive_effort_table, key=lambda p: p[0])
            if train.tractive_effort_table else None
        )

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

    def set_speed_limit_zone(
        self, start_m: int, end_m: int, limit_kmh: float, override: bool = True
    ):
        """특정 거리 구간의 제한속도를 직접 변경 (override=True면 기존 제한속도 덮어쓰기)"""
        capped = min(limit_kmh, self.train.max_speed_kmh)
        for x in range(max(0, start_m), min(self.length + 1, end_m + 1)):
            if override:
                self.speed_limit[x] = capped
            else:
                self.speed_limit[x] = min(self.speed_limit[x], capped)
        self._invalidate_cache()

    def apply_curve_speed_limits(
        self,
        factor: Optional[float] = 4.5,
        cant_sum_mm: Optional[float] = None,
        speed_table: Optional[Union[Dict[float, float], List[Tuple[float, float]]]] = None,
        round_step_kmh: Optional[float] = 5.0,
        reset_to_train_max: bool = False,
    ):
        """
        곡선반경(self.curve_r) 기반 제한속도 일괄 자동계산/적용.
        우선순위: speed_table > cant_sum_mm(V=sqrt(R*(C+Cd)/11.8)) > factor(V=factor*sqrt(R))
        """
        if reset_to_train_max:
            self.speed_limit = [self.train.max_speed_kmh] * (self.length + 1)

        sorted_table: Optional[List[Tuple[float, float]]] = None
        if speed_table is not None:
            items = speed_table.items() if isinstance(speed_table, dict) else speed_table
            sorted_table = sorted(items, key=lambda pair: pair[0])

        for x in range(self.length + 1):
            r = self.curve_r[x]
            if math.isinf(r) or r <= 0:
                continue

            v_curve: Optional[float] = None
            if sorted_table is not None:
                for r_max, v_lim in sorted_table:
                    if r <= r_max:
                        v_curve = float(v_lim)
                        break
            elif cant_sum_mm is not None:
                v_curve = math.sqrt((r * cant_sum_mm) / 11.8)
            elif factor is not None:
                v_curve = factor * math.sqrt(r)

            if v_curve is not None:
                if round_step_kmh and round_step_kmh > 0:
                    v_curve = math.floor((v_curve + 1e-6) / round_step_kmh) * round_step_kmh
                self.speed_limit[x] = min(self.speed_limit[x], v_curve)

        self._invalidate_cache()

    def get_curve_summary(self, min_radius_threshold: float = 1e6) -> List[Dict]:
        """노선 내 곡선(완화곡선 포함) 구간별 최소 반경 및 적용된 제한속도 요약 반환"""
        zones: List[Dict] = []
        in_curve = False
        start_x = 0
        min_r = float("inf")
        min_lim = float("inf")

        for x in range(self.length + 1):
            r = self.curve_r[x]
            is_c = (not math.isinf(r)) and (r < min_radius_threshold)
            if is_c:
                if not in_curve:
                    in_curve = True
                    start_x = x
                    min_r = r
                    min_lim = self.speed_limit[x]
                else:
                    min_r = min(min_r, r)
                    min_lim = min(min_lim, self.speed_limit[x])
            elif in_curve:
                zones.append({
                    "start_m": start_x,
                    "end_m": x - 1,
                    "min_radius_m": round(min_r, 1),
                    "speed_limit_kmh": round(min_lim, 1),
                })
                in_curve = False

        if in_curve:
            zones.append({
                "start_m": start_x,
                "end_m": self.length,
                "min_radius_m": round(min_r, 1),
                "speed_limit_kmh": round(min_lim, 1),
            })
        return zones

    def _invalidate_cache(self):
        self._eff_gradient = None
        self._eff_inv_r = None
        self._eff_speed_limit = None

    def prepare_track(self):
        """
        열차 편성 길이(train.length_m)를 반영한 실효 구배, 실효 곡률(1/R), 실효 제한속도 사전 계산.
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
        """상·하행 반전된 선형(x' = length - x, 구배 부호 반전)을 가지는 새 TPS 객체 반환"""
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
        r_run = 9.81 * (1.5 + 0.03 * v_kmh + 0.0005 * (v_kmh ** 2))
        r_grad = 9.81 * self._eff_gradient[x]
        r_curve = 9.81 * (600.0 * self._eff_inv_r[x])
        return (r_run + r_grad + r_curve) / (1000.0 * self.train.rotational_factor)

    def get_tractive_force_kn(self, v_ms: float) -> float:
        """현재 속도에서의 견인력(kN) 반환 (F-v 테이블 우선, 미지정 시 정출력 모델)"""
        eff_mass_ton = self.train.mass_ton * self.train.rotational_factor
        if self._sorted_fv_table:
            v_kmh = max(0.0, v_ms * 3.6)
            tbl = self._sorted_fv_table
            if v_kmh <= tbl[0][0]:
                return tbl[0][1]
            if v_kmh >= tbl[-1][0]:
                return tbl[-1][1]
            for i in range(len(tbl) - 1):
                v0, f0 = tbl[i]
                v1, f1 = tbl[i + 1]
                if v0 <= v_kmh <= v1:
                    if abs(v1 - v0) < 1e-6:
                        return f0
                    ratio = (v_kmh - v0) / (v1 - v0)
                    return f0 + ratio * (f1 - f0)
            return tbl[-1][1]

        f_max_kn = eff_mass_ton * self.train.max_accel_ms2
        if v_ms < 0.1:
            return f_max_kn
        f_power_kn = self.train.base_power_kw / v_ms
        return min(f_max_kn, f_power_kn)

    def get_tractive_acc(self, v_ms: float) -> float:
        f_kn = self.get_tractive_force_kn(v_ms)
        return (f_kn * 1000.0) / (self.train.mass_ton * 1000.0 * self.train.rotational_factor)

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