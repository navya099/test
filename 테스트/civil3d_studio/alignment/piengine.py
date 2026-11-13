import math
from typing import List, Any

from alignment.arc import ArcSegment
from alignment.japancubic import JapaneseCubicSpiralSegment
from alignment.line import LineSegment

class PIAlignmentEngine:
    """
    실무 설계 방식(PI 좌표 + R, L 또는 A 제원)으로 전체 선형을 자동 계산/생성하는 통합 엔진
    - IP 제원표(IA, TL, CL, SL, Xc, Yc, dR, 주요측점 BP/TS/SC/CS/ST/EP) 자동 산출
    - 임의 좌표의 StationOffset 및 PointLocation 1e-12m 정밀도 계산
    """

    def __init__(self, name: str, pi_list: List[Any], start_station: float = 0.0):
        if len(pi_list) < 2:
            raise ValueError("선형을 생성하려면 최소 2개 이상의 점(BP, EP)이 필요합니다.")
        self.name = name
        self.pi_list = pi_list
        self.start_station = float(start_station)
        self.entities: List[Any] = []
        self.ip_table = []  # 실무 선형 계산서(IP 제원표) 저장용
        self._build_from_pis()

    @staticmethod
    def _normalize_angle(rad: float) -> float:
        return (rad + math.pi) % (2.0 * math.pi) - math.pi

    def _compute_spiral_geometry(self, R: float, L: float):
        """주어진 R과 L에 대한 완화곡선 끝점(Xc, Yc, tau) 및 원곡선 이정(dR), 접선거리(Xm) 계산"""
        if L <= 0.0:
            return 0.0, 0.0, 0.0, 0.0, 0.0
        temp = JapaneseCubicSpiralSegment(0.0, 0.0, 0.0, 0.0, R, L, turn_direction=1)
        Xc, Yc, tau = temp.Xc, temp.Yc, temp.tau
        dR = Yc - R * (1.0 - math.cos(tau))
        Xm = Xc - R * math.sin(tau)
        return Xc, Yc, tau, dR, Xm

    def _build_from_pis(self):
        n = len(self.pi_list)
        # 1. 각 PI 구간의 방위각과 직선 거리 계산
        bearings = []
        seg_lengths = []
        for i in range(n - 1):
            de = self.pi_list[i + 1].easting - self.pi_list[i].easting
            dn = self.pi_list[i + 1].northing - self.pi_list[i].northing
            dist = math.hypot(de, dn)
            if dist < 1e-9:
                raise ValueError(f"{self.pi_list[i].name}와 {self.pi_list[i+1].name}의 좌표가 중복됩니다.")
            bearings.append(math.atan2(dn, de))
            seg_lengths.append(dist)

        # 2. 각 중간 PI별 곡선 제원(TL, CL, SL, 회전방향 등) 계산
        curve_params = []
        for i in range(1, n - 1):
            pi = self.pi_list[i]
            R = float(pi.R)
            # L 또는 A 입력값 상호 자동 변환 (A^2 = R * L)
            if R <= 0.0:
                L, A = 0.0, 0.0
            elif pi.L is not None:
                L = float(pi.L)
                A = math.sqrt(R * L)
            elif pi.A is not None:
                A = float(pi.A)
                L = (A * A) / R
            else:
                L, A = 0.0, 0.0

            delta_theta = self._normalize_angle(bearings[i] - bearings[i - 1])
            IA = abs(delta_theta)
            turn_dir = 1 if delta_theta >= 0 else -1  # 좌회전(+1), 우회전(-1)

            if R > 0.0 and IA > 1e-12:
                Xc, Yc, tau, dR, Xm = self._compute_spiral_geometry(R, L)
                if IA < 2.0 * tau:
                    raise ValueError(
                        f"[{pi.name}] 교각(IA={math.degrees(IA):.4f}°)이 완화곡선 편각 합(2τ={math.degrees(2*tau):.4f}°)보다 작아 원곡선을 배치할 수 없습니다."
                    )
                TL = Xm + (R + dR) * math.tan(IA * 0.5)
                CL = R * (IA - 2.0 * tau)
                SL = (R + dR) / math.cos(IA * 0.5) - R  # 외할(Secant Length)
            else:
                Xc = Yc = tau = dR = Xm = TL = CL = SL = 0.0

            curve_params.append({
                "pi": pi, "R": R, "L": L, "A": A,
                "IA": IA, "turn_dir": turn_dir,
                "Xc": Xc, "Yc": Yc, "tau": tau, "dR": dR, "Xm": Xm,
                "TL": TL, "CL": CL, "SL": SL
            })

        # 3. 직선 구간 길이 검증 및 전체 기하 세그먼트 순차 조립
        curr_e = self.pi_list[0].easting
        curr_n = self.pi_list[0].northing
        curr_sta = self.start_station

        for i in range(n - 1):
            prev_tl = curve_params[i - 1]["TL"] if i > 0 else 0.0
            next_tl = curve_params[i]["TL"] if i < n - 2 else 0.0
            straight_len = seg_lengths[i] - prev_tl - next_tl
            if straight_len < -1e-7:
                raise ValueError(
                    f"[{self.pi_list[i].name} ~ {self.pi_list[i+1].name}] 구간 직선 거리({seg_lengths[i]:.3f}m)보다 "
                    f"앞뒤 접선장 합({prev_tl + next_tl:.3f}m)이 더 큽니다. 반경(R) 또는 완화곡선 길이(L)를 줄이세요."
                )

            # 3-1. 직선 구간(Line) 추가
            if straight_len > 1e-9:

                line_seg = LineSegment(curr_e, curr_n, bearings[i], curr_sta, straight_len)
                self.entities.append(line_seg)
                curr_e, curr_n, _, curr_sta = line_seg.end_pose

            # 3-2. 다음 교점(PI)에 곡선부가 있으면 [진입완화 -> 원곡선 -> 진출완화] 추가
            if i < n - 2:
                cp = curve_params[i]
                ts_sta = curr_sta

                # 진입 완화곡선 (TS -> SC)
                if cp["L"] > 1e-9:
                    sp_in = JapaneseCubicSpiralSegment(
                        curr_e, curr_n, bearings[i], curr_sta,
                        cp["R"], cp["L"], cp["turn_dir"], is_exit_spiral=False
                    )
                    self.entities.append(sp_in)
                    curr_e, curr_n, curr_angle, curr_sta = sp_in.end_pose
                else:
                    curr_angle = bearings[i]
                sc_sta = curr_sta

                # 중앙 원곡선 (SC -> CS)
                if cp["CL"] > 1e-9:
                    arc_seg = ArcSegment(
                        curr_e, curr_n, curr_angle, curr_sta,
                        cp["R"], cp["CL"], cp["turn_dir"]
                    )
                    self.entities.append(arc_seg)
                    curr_e, curr_n, curr_angle, curr_sta = arc_seg.end_pose
                cs_sta = curr_sta

                # 진출 완화곡선 (CS -> ST)
                if cp["L"] > 1e-9:
                    sp_out = JapaneseCubicSpiralSegment(
                        curr_e, curr_n, curr_angle, curr_sta,
                        cp["R"], cp["L"], cp["turn_dir"], is_exit_spiral=True
                    )
                    self.entities.append(sp_out)
                    curr_e, curr_n, _, curr_sta = sp_out.end_pose
                st_sta = curr_sta

                # IP 제원표 기록
                self.ip_table.append({
                    "Name": cp["pi"].name,
                    "Easting": cp["pi"].easting,
                    "Northing": cp["pi"].northing,
                    "Dir": "좌(L)" if cp["turn_dir"] > 0 else "우(R)",
                    "IA_deg": math.degrees(cp["IA"]),
                    "R": cp["R"],
                    "A": cp["A"],
                    "L": cp["L"],
                    "TL": cp["TL"],
                    "CL": cp["CL"],
                    "SL": cp["SL"],
                    "TS_STA": ts_sta,
                    "SC_STA": sc_sta,
                    "CS_STA": cs_sta,
                    "ST_STA": st_sta
                })

    def print_ip_report(self):
        """실무 설계용 선형 계산서(IP 제원표) 콘솔 출력"""
        print(f"\n==================== [{self.name}] 실무 선형 계산서 (IP 제원표) ====================")
        print(f"시점(BP) STA: {self.start_station:.3f} m  |  종점(EP) STA: {self.entities[-1].end_sta:.3f} m")
        print("-" * 105)
        header = f"{'IP':<6} | {'방향':<5} | {'교각(IA°)':<10} | {'R(m)':<8} | {'A(m)':<8} | {'L(m)':<8} | {'TL(m)':<9} | {'CL(m)':<9} | {'TS ~ ST 측점 범위'}"
        print(header)
        print("-" * 105)
        for row in self.ip_table:
            sta_range = f"{row['TS_STA']:.3f} ~ {row['ST_STA']:.3f}"
            print(
                f"{row['Name']:<6} | {row['Dir']:<5} | {row['IA_deg']:<10.4f} | "
                f"{row['R']:<8.2f} | {row['A']:<8.2f} | {row['L']:<8.2f} | "
                f"{row['TL']:<9.3f} | {row['CL']:<9.3f} | {sta_range}"
            )
        print("=" * 105)

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
                _, off, _, _ = res
                if abs(off) < min_off:
                    min_off = abs(off)
                    best_res = res
        return best_res