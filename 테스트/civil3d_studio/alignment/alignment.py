from alignment.alignment_entity import AlignmentEntity
from alignment.arc import ArcSegment
from alignment.calculator import get_shift
from alignment.japancubic import JapaneseCubicSpiralSegment
from alignment.line import LineSegment
from alignment.pipoint import PIPoint
import math

class Alignment:
    """
    직선(Line) -> 진입 완화곡선(TS-SC) -> 원곡선(SC-CS) -> 진출 완화곡선(CS-ST) -> 직선
    순서로 요소를 자동 연결하여 전체 선형의 PointLocation 및 StationOffset을 처리하는 통합 클래스
    """

    def __init__(
        self,
        name: str,
        entities: list[AlignmentEntity],
    ):
        self.name = name
        self.entities = entities

    @property
    def starting_station(self) -> float:
        if not self.entities:
            raise RuntimeError("선형 엔티티가 없습니다.")
        return self.entities[0].start_sta

    @property
    def ending_station(self) -> float:
        if not self.entities:
            raise RuntimeError("선형 엔티티가 없습니다.")
        return self.entities[-1].end_sta

    @classmethod
    def create(
            cls,
            name: str,
            pi_list: list[PIPoint],
            start_station: float = 0.0,
    ) -> "Alignment":

        if len(pi_list) < 2:
            raise ValueError("PI는 최소 2개 이상 필요합니다.")

        entities: list[AlignmentEntity] = []

        # -----------------------------
        # Bearing / Tangent Length 계산
        # -----------------------------
        bearings: list[float] = []
        seg_lengths: list[float] = []

        for i in range(len(pi_list) - 1):
            de = pi_list[i + 1].easting - pi_list[i].easting
            dn = pi_list[i + 1].northing - pi_list[i].northing

            bearings.append(math.atan2(dn, de))
            seg_lengths.append(math.hypot(de, dn))

        # -----------------------------
        # 곡선 제원 계산
        # -----------------------------
        curve_params = []

        for i in range(1, len(pi_list) - 1):

            pi = pi_list[i]

            R = float(pi.R)

            L1 = (
                float(pi.L1)
                if pi.L1 is not None
                else ((pi.A1 ** 2) / R if pi.A1 and R > 0 else 0.0)
            )

            L2 = (
                float(pi.L2)
                if pi.L2 is not None
                else ((pi.A2 ** 2) / R if pi.A2 and R > 0 else L1)
            )

            d_theta = (
                    (bearings[i] - bearings[i - 1] + math.pi)
                    % (2.0 * math.pi)
                    - math.pi
            )

            IA = abs(d_theta)
            turn_dir = 1 if d_theta >= 0 else -1



            tau1, dR1, Xm1 = get_shift(R, L1)
            tau2, dR2, Xm2 = get_shift(R, L2)

            TL1 = (
                    Xm1
                    + (R + dR1) * math.tan(IA * 0.5)
                    + (dR2 - dR1) / math.sin(IA)
            )

            TL2 = (
                    Xm2
                    + (R + dR2) * math.tan(IA * 0.5)
                    + (dR1 - dR2) / math.sin(IA)
            )

            CL = R * (IA - tau1 - tau2)

            curve_params.append(
                {
                    "R": R,
                    "L1": L1,
                    "L2": L2,
                    "TL1": TL1,
                    "TL2": TL2,
                    "CL": CL,
                    "turn_dir": turn_dir,
                }
            )

        # -----------------------------
        # 엔티티 생성
        # -----------------------------
        curr_e = pi_list[0].easting
        curr_n = pi_list[0].northing
        curr_sta = start_station

        for i in range(len(pi_list) - 1):

            prev_tl2 = curve_params[i - 1]["TL2"] if i > 0 else 0.0
            next_tl1 = curve_params[i]["TL1"] if i < len(pi_list) - 2 else 0.0

            tangent_length = seg_lengths[i] - prev_tl2 - next_tl1

            if tangent_length > 1e-9:
                line = LineSegment(
                    curr_e,
                    curr_n,
                    bearings[i],
                    curr_sta,
                    tangent_length,
                )

                entities.append(line)

                curr_e, curr_n, _, curr_sta = line.end_pose

            if i >= len(pi_list) - 2:
                continue

            cp = curve_params[i]

            curr_angle = bearings[i]

            # 진입 완화곡선
            if cp["L1"] > 1e-9:
                spiral_in = JapaneseCubicSpiralSegment(
                    curr_e,
                    curr_n,
                    curr_angle,
                    curr_sta,
                    cp["R"],
                    cp["L1"],
                    cp["turn_dir"],
                    False,
                )

                entities.append(spiral_in)

                curr_e, curr_n, curr_angle, curr_sta = spiral_in.end_pose

            # 원곡선
            if cp["CL"] > 1e-9:
                arc = ArcSegment(
                    curr_e,
                    curr_n,
                    curr_angle,
                    curr_sta,
                    cp["R"],
                    cp["CL"],
                    cp["turn_dir"],
                )

                entities.append(arc)

                curr_e, curr_n, curr_angle, curr_sta = arc.end_pose

            # 진출 완화곡선
            if cp["L2"] > 1e-9:
                spiral_out = JapaneseCubicSpiralSegment(
                    curr_e,
                    curr_n,
                    curr_angle,
                    curr_sta,
                    cp["R"],
                    cp["L2"],
                    cp["turn_dir"],
                    True,
                )

                entities.append(spiral_out)

                curr_e, curr_n, _, curr_sta = spiral_out.end_pose

        return cls(
            name=name,
            entities=entities,
        )

    def point_location(self, station: float, offset: float = 0.0):
        """전체 선형 기준 측점(Station)과 오프셋(Offset) -> 글로벌 (Easting, Northing)"""
        if not self.entities:
            raise RuntimeError("선형에 등록된 기하 요소가 없습니다.")
        if station < self.starting_station - 1e-9 or station > self.ending_station + 1e-9:
            raise ValueError(f"입력 측점({station})이 선형 범위({self.starting_station} ~ {self.ending_station})를 벗어났습니다.")

        # 수정: 각 요소를 순회하며 해당 측점이 포함된 세그먼트 탐색
        for idx, ent in enumerate(self.entities):

            if idx == len(self.entities) - 1:
                if ent.start_sta - 1e-9 <= station <= ent.end_sta + 1e-9:
                    return ent.point_location(station, offset)

            elif ent.start_sta - 1e-9 <= station < ent.end_sta:
                return ent.point_location(station, offset)

        return self.entities[-1].point_location(station, offset)

    def station_offset(self, easting: float, northing: float):
        """
        전체 선형 기준 글로벌 (Easting, Northing) -> (station, signed_offset, proj_e, proj_n)
        모든 기하 요소에 수선을 내려 가장 가까운 최단 투영 결과를 반환
        """
        best_result = None
        min_abs_offset = float("inf")

        for ent in self.entities:
            res = ent.station_offset(easting, northing)
            if res is not None:
                sta, off, pe, pn = res
                # 수정: 더 가까운 오프셋을 가진 세그먼트 결과로 안전하게 갱신
                if abs(off) < min_abs_offset:
                    min_abs_offset = abs(off)
                    best_result = res

        return best_result