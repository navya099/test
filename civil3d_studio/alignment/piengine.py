import math
from typing import List, Optional, Any

from alignment.arc import ArcSegment
from alignment.japancubic import JapaneseCubicSpiralSegment
from alignment.line import LineSegment

class PIAlignmentEngine:
    """
    Civil 3D와 동일하게 대칭/비대칭/단측 완화곡선(L1 != L2, A1 != A2)을 모두 지원하는 선형 생성 엔진
    """

    def __init__(self, name: str, pi_list: List[Any], start_station: float = 0.0):
        if len(pi_list) < 2:
            raise ValueError("선형을 생성하려면 최소 2개 이상의 점(BP, EP)이 필요합니다.")
        self.name = name
        self.pi_list = pi_list
        self.start_station = float(start_station)
        self.entities: List[Any] = []
        self.ip_table = []
        self._build_from_pis()

    @staticmethod
    def _normalize_angle(rad: float) -> float:
        return (rad + math.pi) % (2.0 * math.pi) - math.pi

    @staticmethod
    def _resolve_spiral_pair(R: float, L1: Optional[float], L2: Optional[float], A1: Optional[float],
                             A2: Optional[float]):
        """입력된 (L1, A1) 및 (L2, A2)로부터 진입/진출 (L1, A1, L2, A2) 확정"""
        if R <= 0.0:
            return 0.0, 0.0, 0.0, 0.0

        # 진입부(1) 계산
        if L1 is not None:
            res_L1 = float(L1)
            res_A1 = math.sqrt(R * res_L1) if res_L1 > 0 else 0.0
        elif A1 is not None:
            res_A1 = float(A1)
            res_L1 = (res_A1 * res_A1) / R if res_A1 > 0 else 0.0
        else:
            res_L1, res_A1 = 0.0, 0.0

        # 진출부(2) 계산 (미입력 시 진입부 제원을 승계하여 대칭 처리)
        if L2 is not None:
            res_L2 = float(L2)
            res_A2 = math.sqrt(R * res_L2) if res_L2 > 0 else 0.0
        elif A2 is not None:
            res_A2 = float(A2)
            res_L2 = (res_A2 * res_A2) / R if res_A2 > 0 else 0.0
        else:
            res_L2, res_A2 = res_L1, res_A1

        return res_L1, res_A1, res_L2, res_A2

    def _compute_spiral_shift(self, R: float, L: float):
        """단일 완화곡선의 끝점 편각(tau), 원곡선 이정(dR), 접선 보정거리(Xm) 산출"""
        if L <= 0.0:
            return 0.0, 0.0, 0.0
        temp = JapaneseCubicSpiralSegment(0.0, 0.0, 0.0, 0.0, R, L, turn_direction=1)
        Xc, Yc, tau = temp.Xc, temp.Yc, temp.tau
        dR = Yc - R * (1.0 - math.cos(tau))
        Xm = Xc - R * math.sin(tau)
        return tau, dR, Xm

    def _build_from_pis(self):
        n = len(self.pi_list)
        bearings = []
        seg_lengths = []

        for i in range(n - 1):
            de = self.pi_list[i + 1].easting - self.pi_list[i].easting
            dn = self.pi_list[i + 1].northing - self.pi_list[i].northing
            dist = math.hypot(de, dn)
            if dist < 1e-9:
                raise ValueError(f"{self.pi_list[i].name}와 {self.pi_list[i + 1].name}의 좌표가 중복됩니다.")
            bearings.append(math.atan2(dn, de))
            seg_lengths.append(dist)

        curve_params = []
        for i in range(1, n - 1):
            pi = self.pi_list[i]
            R = float(pi.R)
            L1, A1, L2, A2 = self._resolve_spiral_pair(R, pi.L1, pi.L2, pi.A1, pi.A2)

            delta_theta = self._normalize_angle(bearings[i] - bearings[i - 1])
            IA = abs(delta_theta)
            turn_dir = 1 if delta_theta >= 0 else -1

            if R > 0.0 and IA > 1e-12:
                tau1, dR1, Xm1 = self._compute_spiral_shift(R, L1)
                tau2, dR2, Xm2 = self._compute_spiral_shift(R, L2)
                if IA < (tau1 + tau2):
                    raise ValueError(
                        f"[{pi.name}] 교각(IA={math.degrees(IA):.4f}°)이 진입·진출 완화곡선 편각 합"
                        f"(τ1+τ2={math.degrees(tau1 + tau2):.4f}°)보다 작아 원곡선을 배치할 수 없습니다."
                    )

                # 비대칭 전접선장(TL1) 및 후접선장(TL2) 엄밀 계산
                sin_ia = math.sin(IA)
                tan_half_ia = math.tan(IA * 0.5)
                TL1 = Xm1 + (R + dR1) * tan_half_ia + (dR2 - dR1) / sin_ia
                TL2 = Xm2 + (R + dR2) * tan_half_ia + (dR1 - dR2) / sin_ia
                CL = R * (IA - tau1 - tau2)
            else:
                tau1 = dR1 = Xm1 = tau2 = dR2 = Xm2 = TL1 = TL2 = CL = 0.0

            curve_params.append({
                "pi": pi, "R": R,
                "L1": L1, "A1": A1, "L2": L2, "A2": A2,
                "IA": IA, "turn_dir": turn_dir,
                "TL1": TL1, "TL2": TL2, "CL": CL
            })

        # 직선 구간 길이 계산 시 이전 PI의 후접선장(TL2)과 다음 PI의 전접선장(TL1)을 차감
        curr_e = self.pi_list[0].easting
        curr_n = self.pi_list[0].northing
        curr_sta = self.start_station

        for i in range(n - 1):
            prev_tl2 = curve_params[i - 1]["TL2"] if i > 0 else 0.0
            next_tl1 = curve_params[i]["TL1"] if i < n - 2 else 0.0
            straight_len = seg_lengths[i] - prev_tl2 - next_tl1

            if straight_len < -1e-7:
                raise ValueError(
                    f"[{self.pi_list[i].name} ~ {self.pi_list[i + 1].name}] 구간 직선 거리({seg_lengths[i]:.3f}m)보다 "
                    f"앞 PI의 후접선장(TL2={prev_tl2:.3f}m) + 뒤 PI의 전접선장(TL1={next_tl1:.3f}m) 합이 큽니다."
                )

            if straight_len > 1e-9:

                line_seg = LineSegment(curr_e, curr_n, bearings[i], curr_sta, straight_len)
                self.entities.append(line_seg)
                curr_e, curr_n, _, curr_sta = line_seg.end_pose

            if i < n - 2:
                cp = curve_params[i]
                ts_sta = curr_sta

                # 1. 진입 완화곡선 (L1)
                if cp["L1"] > 1e-9:
                    sp_in = JapaneseCubicSpiralSegment(
                        curr_e, curr_n, bearings[i], curr_sta,
                        cp["R"], cp["L1"], cp["turn_dir"], is_exit_spiral=False
                    )
                    self.entities.append(sp_in)
                    curr_e, curr_n, curr_angle, curr_sta = sp_in.end_pose
                else:
                    curr_angle = bearings[i]
                sc_sta = curr_sta

                # 2. 중앙 원곡선 (CL)
                if cp["CL"] > 1e-9:
                    arc_seg = ArcSegment(
                        curr_e, curr_n, curr_angle, curr_sta,
                        cp["R"], cp["CL"], cp["turn_dir"]
                    )
                    self.entities.append(arc_seg)
                    curr_e, curr_n, curr_angle, curr_sta = arc_seg.end_pose
                cs_sta = curr_sta

                # 3. 진출 완화곡선 (L2)
                if cp["L2"] > 1e-9:
                    sp_out = JapaneseCubicSpiralSegment(
                        curr_e, curr_n, curr_angle, curr_sta,
                        cp["R"], cp["L2"], cp["turn_dir"], is_exit_spiral=True
                    )
                    self.entities.append(sp_out)
                    curr_e, curr_n, _, curr_sta = sp_out.end_pose
                st_sta = curr_sta

                is_asym = abs(cp["L1"] - cp["L2"]) > 1e-6
                self.ip_table.append({
                    "Name": cp["pi"].name,
                    "Type": "비대칭" if is_asym else "대칭",
                    "Dir": "좌(L)" if cp["turn_dir"] > 0 else "우(R)",
                    "IA_deg": math.degrees(cp["IA"]),
                    "R": cp["R"],
                    "L1": cp["L1"], "A1": cp["A1"],
                    "L2": cp["L2"], "A2": cp["A2"],
                    "TL1": cp["TL1"], "TL2": cp["TL2"],
                    "CL": cp["CL"],
                    "TS_STA": ts_sta, "SC_STA": sc_sta,
                    "CS_STA": cs_sta, "ST_STA": st_sta
                })

    def print_ip_report(self):
        """비대칭 전·후접선장(TL1, TL2)이 포함된 실무 선형 계산서 출력"""
        print(f"\n========================== [{self.name}] 비대칭 지원 선형 계산서 ==========================")
        print(f"시점(BP) STA: {self.start_station:.3f} m  |  종점(EP) STA: {self.entities[-1].end_sta:.3f} m")
        print("-" * 125)
        header = (
            f"{'IP':<6} | {'구분':<4} | {'방향':<5} | {'교각(IA°)':<9} | {'R(m)':<7} | "
            f"{'L1/L2(m)':<13} | {'A1/A2(m)':<13} | {'TL1(m)':<8} | {'TL2(m)':<8} | {'CL(m)':<8} | {'TS ~ ST 측점'}"
        )
        print(header)
        print("-" * 125)
        for r in self.ip_table:
            l_pair = f"{r['L1']:.1f}/{r['L2']:.1f}"
            a_pair = f"{r['A1']:.1f}/{r['A2']:.1f}"
            sta_str = f"{r['TS_STA']:.2f}~{r['ST_STA']:.2f}"
            print(
                f"{r['Name']:<6} | {r['Type']:<4} | {r['Dir']:<5} | {r['IA_deg']:<9.4f} | {r['R']:<7.1f} | "
                f"{l_pair:<13} | {a_pair:<13} | {r['TL1']:<8.3f} | {r['TL2']:<8.3f} | {r['CL']:<8.3f} | {sta_str}"
            )
        print("=" * 125)

    def point_location(self, station: float, offset: float = 0.0):
        for idx, ent in enumerate(self.entities):
            if idx == len(self.entities) - 1:
                if ent.start_sta - 1e-9 <= station <= ent.end_sta + 1e-9:
                    return ent.point_location(station, offset)
            else:
                if ent.start_sta - 1e-9 <= station < ent.end_sta:
                    return ent.point_location(station, offset)
        raise ValueError(f"측점({station})이 선형 범위를 벗어났습니다.")

    def station_offset(self, easting: float, northing: float):
        best_res = None
        min_off = float("inf")
        for ent in self.entities:
            res = ent.station_offset(easting, northing)
            if res is not None:
                _, off, _, _ = res  # 튜플 언패킹 수정 완료
                if abs(off) < min_off:
                    min_off = abs(off)
                    best_res = res
        return best_res