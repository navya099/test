from dataclasses import dataclass

from AutoCAD.point2d import Point2d
from data.alignment.geometry.straight.straightgeometry import StraightGeometry
from data.segment.segment import Segment


@dataclass
class StraightSegment(Segment):
    """직선 세그먼트"""
    _geom: StraightGeometry = StraightGeometry

    @classmethod
    def from_coord(cls, start_point: Point2d, end_point: Point2d):
        """두 점으로부터 직선 세그먼트 생성"""
        return cls(
            _geom=StraightGeometry(start_coord=start_point, end_coord=end_point)
        )
    @property
    def start_azimuth(self):
        """시작 각도"""
        return self._geom.tangent_at(0.0)

    @property
    def end_azimuth(self):
        """끝 각도"""
        return self.start_azimuth

    @property
    def length(self):
        """길이"""
        return self._geom.length

    @property
    def start_coord(self):
        return self._geom.start_coord

    @property
    def end_coord(self):
        return self._geom.end_coord

    def distance_to_point(self, point: Point2d) -> float:
        return self._geom.distance_at(point)

    def point_at_station(self, station: float, offset: float) -> tuple[Point2d, float]:
        if not (self.start_sta <= station <= self.end_sta):
            raise ValueError("station out of range")
        s = station - self.start_sta
        return self._geom.point_at(s, offset), self._geom.tangent_at(s)

    def station_at_point(self, coord: Point2d) -> tuple[float, float]:
        pt, of  = self._geom.project_at(coord)
        s = pt.distance_to(self.start_coord)
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
        #다음 세그먼트 생성
        new_seg = StraightSegment.from_coord(start_point=coord,end_point=self.end_coord)
        self._geom.end_coord = coord
        return new_seg