from dataclasses import dataclass
import math
from AutoCAD.point2d import Point2d
from curvedirection import CurveDirection
from data.alignment.geometry.segmentgeometry import SegmentGeometry
from data.alignment.geometry.spiral.params import TransitionCurveParams


@dataclass
class SpiralGeometry(SegmentGeometry):
    """완화곡선 지오메트리 엔진
    Attributes:
        direction: 곡선방향
        params: 완화곡선 파라메터
    """
    direction: CurveDirection = CurveDirection
    params: TransitionCurveParams = TransitionCurveParams

    @property
    def a(self):
        return self.params.a

    @property
    def delta(self):
        """완화곡선 전체 각도"""
        return self.params.theta_pc

    @property
    def total_x(self):
        """완화곡선 전체 X"""
        return self.params.x1

    @property
    def total_y(self):
        """완화곡선 전체 Y"""
        return self.params.y1

    def tangent_at(self, s: float) -> float:
        return self.local_tangent(s)

    def point_at(self, s: float, offset: float = 0.0) -> Point2d:
        return self.local_xy(s)

    def project_at(self, p: Point2d) -> tuple[Point2d, float]:
        pass

    def distance_at(self, p: Point2d) -> float:
        pass

    def reversed(self):
        pass

    def get_offset(self, offset: float):
        pass

    def local_xy(self, s: float) -> Point2d:
        """완화곡선 로컬좌표 (x, y) 계산"""
        r = self.params.radius
        l = self.params.l
        x1 = self.params.x1

        x = s - (s**5) / (40 * r * r * (l**2))
        y = (x**3) / (6 * r * x1) if x1 != 0 else 0

        return Point2d(x, y)

    def local_tangent(self, s):
        pt = self.local_xy(s)

        r = self.params.radius
        l = self.params.l
        x1 = self.params.x1

        x = pt.x
        dx = 1 - (s ** 4) / (8 * r * r * l * l)

        if x1 != 0:
            dy = (x * x * dx) / (2 * r * x1)
        else:
            dy = 0

        return math.atan2(dy, dx)