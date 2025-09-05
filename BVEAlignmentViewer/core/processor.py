from copy import deepcopy

from model.model import BVERouteData, Curve, Pitch
from vector2 import Vector2

class RouteProcessor:
    """
    BVERouteData 전처리를 위한 프로세서 클래스
    Attributes:
        current_route(BVERouteData): BVERouteData 객체
    """
    def __init__(self, current_route: BVERouteData):
        self.current_route = current_route
        self._station_coord_map: dict[float, Vector2] = {}  # 캐시용 속성

    def run(self):
        """
        전처리 실행 메소드
        1. 라스트블럭 인덱스만큼 각 리스트들 자르기
        2. bve좌표계 변환 xyz -> xzy
        3. 좌표맵 생성
        4. 각도맵 생성
        5. 정거장 좌표할당
        6. 곡선에 좌표할당
        7. 중복 R 제거
        8. 중복 구배 제거
        """

        self._slice_to_lastblock()
        self._convert_bve_coordinatesystem()
        self._build_station_coord_map()
        self._build_station_direction_map()
        self.set_station_coord()
        self.set_curve_coord_and_direction()

        self._remove_duplicate_radius()
        self._remove_duplicate_pitchs()

    def _slice_to_lastblock(self):
        """
        마지막 블럭 인덱스만큼 리스트를 자르는 매소드
        첫 인덱스가 0이 아닌 경우에도 정상 동작하도록 수정
        """

        # 슬라이싱
        self.current_route.curves = self.current_route.curves[0:self.current_route.lastindex + 1 - self.current_route.firstindex]
        self.current_route.pitchs = self.current_route.pitchs[0:self.current_route.lastindex + 1 - self.current_route.firstindex]
        self.current_route.coords = self.current_route.coords[0:self.current_route.lastindex + 1 -  self.current_route.firstindex]
        self.current_route.directions = self.current_route.directions[0:self.current_route.lastindex + 1 - self.current_route.firstindex]

    def _remove_duplicate_radius(self):
        """
        블록내 중복된 반경을 제거하는 메소드
        """
        curves = self.current_route.curves
        last_curve = curves[-1]
        for i in range(len(curves) - 1, 0, -1):
            if curves[i].radius == curves[i - 1].radius:
                del curves[i]
        #마지막 CURVE가 곡선인경우 마지막 블록 추가
        if curves[-1].radius != 0:
            curves.append(last_curve)
            #곡선반경을 0으로
            last_curve.radius = 0

    def _remove_duplicate_pitchs(self):
        """
        블록내 중복된 구배를 제거하는 메소드
        """
        pitchs = self.current_route.pitchs
        i = 1
        while i < len(pitchs):
            if pitchs[i].pitch == pitchs[i - 1].pitch:
                del pitchs[i]
            else:
                i += 1

    def get_coord(self, station_value: float) -> Vector2 | None:
        """
        특정 station의 좌표 반환
        없으면 None 반환
        """
        if not self._station_coord_map:
            self._build_station_coord_map()

        return self._station_coord_map.get(station_value, None)

    def set_station_coord(self):
        """정거장 좌표를 station 정보에 매핑"""
        if not self._station_coord_map:
            self._build_station_coord_map()

        for station in self.current_route.stations:
            coord = self._station_coord_map.get(station.station)
            if coord:
                station.coord = Vector2(coord.x, coord.y)

    def get_direction(self, station_value: float):
        if not self._station_direction_map:
            self._build_station_direction_map()

        return self._station_direction_map.get(station_value, None)

    def set_station_directions(self):
        """정거장 좌표를 station 정보에 매핑"""
        if not self._station_direction_map:
            self._build_station_direction_map()

        for station in self.current_route.stations:
            direction = self._station_direction_map.get(station.station)
            if direction:
                station.direction = direction

    def _convert_bve_coordinatesystem(self):
        """
        bve좌표계의 y와 z를 변환
        변환대상- coord와 direction
        """
        for coord in self.current_route.coords:
            coord.x = coord.x
            coord.y = coord.z
            coord.z = coord.y

        for direction in self.current_route.directions:
            direction.x = direction.x
            direction.y = direction.z
            direction.z = direction.y

    def _build_station_coord_map(self):
        """곡선 station → 좌표 매핑 딕셔너리 생성"""
        curves = self.current_route.curves
        coords = self.current_route.coords

        self._station_coord_map = {r.station: Vector2(c.x, c.y) for r, c in zip(curves, coords)}

    def _build_station_direction_map(self):
        """곡선 station → 각도 매핑 딕셔너리 생성"""
        curves = self.current_route.curves
        directions = self.current_route.directions

        self._station_direction_map = {r.station: Vector2(c.x, c.y).toradian() for r, c in zip(curves, directions)}

    def set_curve_coord_and_direction(self):
        """좌표를 곡선 정보에 매핑"""
        if not self._station_direction_map:
            self._build_station_direction_map()
        if not self._station_coord_map:
            self._build_station_coord_map()

        curves = self.current_route.curves
        for curve in curves:
            if curve.station in self._station_coord_map:
                curve.coord = self._station_coord_map[curve.station]
                # 방향 매핑
                direction = self._station_direction_map.get(curve.station)
                if direction:
                    curve.direction = direction