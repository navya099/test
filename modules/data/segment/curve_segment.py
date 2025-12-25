from dataclasses import dataclass

from AutoCAD.point2d import Point2d
from curvedirection import CurveDirection
from data.alignment.geometry.simplecurve.curvegeometry import CurveGeometry
from data.segment.segment import Segment


@dataclass
class CurveSegment(Segment):
    """
    구간별 곡선 세그먼트 저장용 클래스 (단곡선).
    """
    _geom: CurveGeometry = CurveGeometry

    @property
    def start_azimuth(self) -> float:
        """시작 각도"""
        return self._geom.start_angle

    @property
    def end_azimuth(self) -> float:
        """끝 각도"""
        return self._geom.end_angle

    @property
    def delta(self):
        return self._geom.delta

    @property
    def radius(self) -> float:
        """곡선반경"""
        return self._geom.radius

    @property
    def start_coord(self) -> Point2d:
        """시작 좌표"""
        return self._geom.start_coord

    @property
    def end_coord(self) -> Point2d:
        """끝 좌표"""
        return self._geom.end_coord

    @property
    def center_coord(self) -> Point2d:
        """중심 좌표"""
        return self._geom.center

    @property
    def direction(self) -> CurveDirection:
        """방향"""
        return self._geom.direction

    @property
    def tangent_length(self):
        """접선장 TL"""
        return self._geom.tangent_length

    @property
    def length(self):
        """원곡선 길이 CL"""
        return self._geom.length

    @property
    def external_secant(self):
        """외선장 SL"""
        return self._geom.external_secant

    @property
    def middle_oridante(self):
        """중앙종거 M"""
        return self._geom.middle_oridante

    @property
    def midpoint(self) -> Point2d:
        """중점 반환"""
        mid_sta = (self.start_sta + self.end_sta) / 2
        pt, _ = self.point_at_station(mid_sta, 0)
        return pt

    def distance_to_point(self, point):
        return self._geom.distance_at(point)

    def point_at_station(self, station: float, offset: float = 0.0) -> tuple[Point2d, float]:
        # --- 1) Station 비율 계산 ---
        if station < self.start_sta or station > self.end_sta:
            raise ValueError("Station이 세그먼트 범위를 벗어남")
        #거리 s
        s = station - self.start_sta # 곡선 시작점으로부터의 곡선상 거리
        return self._geom.point_at(s, offset), self._geom.tangent_at(s)

    def station_at_point(self, coord: Point2d) -> tuple[float, float]:
        # 1) 곡선으로 투영
        pt, of  = self._geom.project_at(coord)
        # 2) 시작점 → 투영점까지의 호 길이
        s = self._geom.arc_length_between(p1=self.start_coord,p2=pt)
        station = s + self.start_sta
        if not (self.start_sta <= station <= self.end_sta):
            raise ValueError("station out of range")
        return station, of

    def is_contains_station(self, station: float) -> bool:
        return self.start_sta <= station <= self.end_sta

    def is_contains_point(self, point: Point2d, tol: float = 1e-3) -> bool:
        sta, offset = self.station_at_point(point)
        return self.is_contains_station(sta) and abs(offset) <= tol

    def reverse(self):
        self._geom.reversed()

    def create_offset(self, offset_distance: float):
        self._geom.get_offset(offset_distance)

    def split_to_segment(self, coord: Point2d):
        # 다음 세그먼트 생성
        s = self._geom.arc_length_between(p1=self.start_coord,p2=coord)
        new_seg = CurveSegment.create(
                radius= self.radius,
                start_angle= s / self.radius,  # l = r * θ , θ = l / r
                end_angle= self.end_azimuth,     # rad
                direction= self.direction,
                center= self.center_coord
            )

        return new_seg