from alignment.alignment_entity import AlignmentEntity
from alignment.arc import ArcSegment
from alignment.japancubic import JapaneseCubicSpiralSegment
from alignment.line import LineSegment


class CompositeAlignment:
    """
    직선(Line) -> 진입 완화곡선(TS-SC) -> 원곡선(SC-CS) -> 진출 완화곡선(CS-ST) -> 직선
    순서로 요소를 자동 연결하여 전체 선형의 PointLocation 및 StationOffset을 처리하는 통합 클래스
    """

    def __init__(self, name: str, start_easting: float, start_northing: float, start_angle_rad: float,
                 start_station: float = 0.0):
        self.name = name
        self.curr_e = float(start_easting)
        self.curr_n = float(start_northing)
        self.curr_angle = float(start_angle_rad)
        self.curr_sta = float(start_station)
        self.entities: list[AlignmentEntity] = []

    @property
    def starting_station(self) -> float:
        # 수정: 리스트 자체 대신 첫 번째 요소의 시점 측점 참조
        return self.entities[0].start_sta if self.entities else self.curr_sta

    @property
    def ending_station(self) -> float:
        return self.entities[-1].end_sta if self.entities else self.curr_sta

    def add_line(self, length: float):
        """현재 끝점에서 이어지는 직선(Line) 요소 추가"""
        seg = LineSegment(self.curr_e, self.curr_n, self.curr_angle, self.curr_sta, length)
        self._append_entity(seg)
        return self

    def add_arc(self, R: float, length: float, turn_direction: int = 1):
        """현재 끝점에서 이어지는 원곡선(Arc) 요소 추가 (+1: 우회전, -1: 좌회전)"""
        seg = ArcSegment(self.curr_e, self.curr_n, self.curr_angle, self.curr_sta, R, length, turn_direction)
        self._append_entity(seg)
        return self

    def add_japanese_cubic_spiral(self, R: float, L: float, turn_direction: int = 1, is_exit_spiral: bool = False):
        """현재 끝점에서 이어지는 일본 3차 포물선 완화곡선 추가"""
        seg = JapaneseCubicSpiralSegment(
            self.curr_e, self.curr_n, self.curr_angle, self.curr_sta,
            R, L, turn_direction, is_exit_spiral
        )
        self._append_entity(seg)
        return self

    def _append_entity(self, entity: AlignmentEntity):
        self.entities.append(entity)
        self.curr_e, self.curr_n, self.curr_angle, self.curr_sta = entity.end_pose

    def point_location(self, station: float, offset: float = 0.0):
        """전체 선형 기준 측점(Station)과 오프셋(Offset) -> 글로벌 (Easting, Northing)"""
        if not self.entities:
            raise RuntimeError("선형에 등록된 기하 요소가 없습니다.")
        if station < self.starting_station - 1e-9 or station > self.ending_station + 1e-9:
            raise ValueError(f"입력 측점({station})이 선형 범위({self.starting_station} ~ {self.ending_station})를 벗어났습니다.")

        # 수정: 각 요소를 순회하며 해당 측점이 포함된 세그먼트 탐색
        for ent in self.entities:
            if ent.start_sta - 1e-9 <= station <= ent.end_sta + 1e-9:
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