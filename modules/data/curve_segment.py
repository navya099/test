from dataclasses import dataclass, field
import math

from PIL.ImageCms import Direction

from AutoCAD.point2d import Point2d
from curvedirection import CurveDirection
from data.segment import Segment
from math_utils import calculate_bearing, calculate_destination_coordinates, find_curve_direction


@dataclass
class CurveSegment(Segment):
    """
    구간별 곡선 세그먼트 저장용 클래스 (단곡선).
    Attributes:
        start_azimuth: 시작 각도
        end_azimuth: 끝 각도
        internal_angle(float): 교각 IA
        radius(float): 원곡선 반경 R
        ip_coordinate: IP좌표
    """
    start_azimuth: float = 0.0
    end_azimuth: float = 0.0
    internal_angle: float = 0.0
    radius: float = 0.0
    ip_coordinate: Point2d = field(default_factory=lambda: Point2d(0, 0))

    @property
    def start_coord(self) -> Point2d:
        x, y =calculate_destination_coordinates(self.ip_coordinate, bearing=self.start_azimuth + math.pi, distance=self.tangent_length)
        return Point2d(x, y)

    @property
    def end_coord(self) -> Point2d:
        x, y= calculate_destination_coordinates(self.ip_coordinate, bearing=self.end_azimuth, distance=self.tangent_length)
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