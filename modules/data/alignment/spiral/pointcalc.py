from AutoCAD.point2d import Point2d
from curvedirection import CurveDirection
from data.alignment.spiral.params import TransitionCurveParams
import math

class SpiralPointCalculator:
    """완화곡선 내 임의 지점 계산기 (SP/PS 공용)"""

    def __init__(self, params: TransitionCurveParams, direction: CurveDirection):
        self.p = params
        self.dir = direction

    def local_xy(self, s: float) -> tuple:
        """완화곡선 로컬좌표 (x, y) 계산"""
        R = self.p.radius
        L = self.p.l  # 전체 완화곡선장
        X1 = self.p.x1

        x = s - (s**5) / (40 * R * R * (L**2))
        y = (x**3) / (6 * R * X1) if X1 != 0 else 0

        # 회전방향 부호
        if self.dir == CurveDirection.RIGHT:
            y = -y

        return x, y

    def global_xy(self, origin: Point2d, origin_az: float, s: float) -> Point2d:
        """로컬좌표(x,y)를 글로벌 좌표로 변환하여 실제 점 반환"""
        x, y = self.local_xy(s)


        ca = math.cos(origin_az)
        sa = math.sin(origin_az)

        gx = origin.x + x * ca - y * sa
        gy = origin.y + x * sa + y * ca

        return Point2d(gx, gy)

    def tangent_bearing(self, s: float, origin_az: float, isexit=False):

        R = self.p.radius
        L = self.p.l
        X1 = self.p.x1

        x = s - (s ** 5) / (40 * R * R * (L ** 2))
        dx = 1 - (s ** 4) / (8 * R * R * L * L)

        if X1 != 0:
            dy = (x * x * dx) / (2 * R * X1)
        else:
            dy = 0

        if self.dir == CurveDirection.RIGHT:
            dy = -dy

        theta_local = math.atan2(dy, dx)

        # 🔥 핵심: 끝 완화곡선은 접선각 부호 반전
        if isexit:
            theta_local = -theta_local

        return origin_az + theta_local


