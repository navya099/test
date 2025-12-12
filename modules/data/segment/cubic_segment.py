from dataclasses import dataclass, field
import math
from AutoCAD.point2d import Point2d
from curvedirection import CurveDirection
from data.segment.segment import Segment
from math_utils import find_curve_direction, calculate_destination_coordinates


@dataclass
class CubicSegment(Segment):
    """
    3차포물선 완화곡선 세그먼트
    Attributes:
        m: 캔트배수
        z: 캔트
        start_azimuth: 시각 각도
        end_azimuth: 끝 각도
        internal_angle: 교각
        radius: 곡선반경
        isstarted: 시작 완화곡선 여부
    """
    m: int = 0
    z: float = 0.0
    start_azimuth: float = 0.0
    end_azimuth: float = 0.0
    internal_angle: float = 0.0
    radius: float = 0.0
    isstarted: bool = False

    @property
    def start_coord(self) -> Point2d:
        x, y = calculate_destination_coordinates(self.ip_coordinate, bearing=self.start_azimuth + math.pi,
                                                 distance=self.tangent_length)
        return Point2d(x, y)

    @property
    def end_coord(self) -> Point2d:
        x, y = calculate_destination_coordinates(self.ip_coordinate, bearing=self.end_azimuth,
                                                 distance=self.tangent_length)
        return Point2d(x, y)

    @property
    def center_coord(self) -> Point2d:
        if self.direction == CurveDirection.RIGHT:
            x, y = calculate_destination_coordinates(self.start_coord, bearing=self.start_azimuth - math.pi / 2,
                                                     distance=self.radius)
        else:
            x, y = calculate_destination_coordinates(self.start_coord, bearing=self.start_azimuth + math.pi / 2,
                                                     distance=self.radius)
        return Point2d(x, y)

    @property
    def tangent_length(self):
        """접선장 TL"""
        return self.radius * math.tan(self.internal_angle / 2)

    @property
    def length(self):
        """원곡선 길이 CL"""
        return self.radius * self.internal_angle

    @property
    def external_secant(self):
        """외선장 SL"""
        return self.radius * (1 / math.cos(self.internal_angle / 2) - 1)

    @property
    def middle_oridante(self):
        """중앙종거 M"""
        return self.radius * (1 - math.cos(self.internal_angle / 2))

    @property
    def direction(self):
        """곡선 방향"""
        return find_curve_direction(self.start_coord, self.ip_coordinate, self.end_coord)


    def distance_to_point(self, point: Point2d) -> float:
        """
        점과 원호(곡선 세그먼트) 사이의 최단 거리 계산
        (Shapely 사용하지 않음, 순수 수학 기반)
        """
        pass

    def point_at_station(self, station: float, offset: float = 0.0) -> tuple[Point2d, float]:
        """
        단곡선(Simple Circular Curve) station 기반 좌표 계산
        반환값: (Point2d, tangent_angle)
        """
        pass

    def station_at_point(self, coord: Point2d) -> tuple[float, float]:
        """지정한 좌표의 측점 및 거리 반환"""
        pass

    def is_contains_station(self, station: float) -> bool:
        """지정한 측점이 세그먼트에 포함되는지 여부"""
        pass

    def is_contains_point(self, point: Point2d) -> bool:
        """지정한 점이 세그먼트에 포함되는지 여부"""
        pass

    def reverse(self):
        """세그먼트 뒤집기"""
        pass

    def create_offset(self, offset_distance: float):
        """세그먼트 객체의 평행(오프셋) 복제본을 생성"""
        pass

    def split_to_segment(self, coord: Point2d):
        """"""
        pass