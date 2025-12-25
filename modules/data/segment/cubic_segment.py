from dataclasses import dataclass, field
import math
from AutoCAD.point2d import Point2d
from curvedirection import CurveDirection
from data.alignment.geometry.spiral.params import TransitionCurveParams
from data.segment.segment import Segment
from data.alignment.geometry.spiral.spiral_geometry import SpiralGeometry


@dataclass
class CubicSegment(Segment):
    """
    3차포물선 완화곡선 세그먼트
    Attributes:
        isstarted: 시작 완화곡선 여부
        geom: 지오메트리 정보
        params: 완화곡선 파라메터 정보
        start_coord: 시작 좌표
        end_coord: 끝 좌표
        start_azimuth: 시작 각도
        end_azimuth: 끝 각도
    """

    isstarted: bool = False
    geom: SpiralGeometry = SpiralGeometry
    params: TransitionCurveParams = TransitionCurveParams
    start_azimuth: float = 0.0
    end_azimuth: float = 0.0
    start_coord: Point2d = field(default_factory=lambda: Point2d(0, 0))
    end_coord: Point2d = field(default_factory=lambda: Point2d(0, 0))

    @property
    def length(self):
        """완화곡선 길이L"""
        return self.geom.params.l

    @property
    def a(self):
        """완화곡선 매개변수 A"""
        return self.geom.params.a

    @property
    def delta(self):
        """완화곡선 접선각"""
        return self.geom.params.theta_pc

    @property
    def direction(self):
        return self.geom.direction

    def distance_to_point(self, point: Point2d) -> float:
        pass

    def point_at_station(self, station: float, offset: float = 0.0) -> tuple[Point2d, float]:
        # --- 1) Station 비율 계산 ---
        if station < self.start_sta or station > self.end_sta:
            raise ValueError("Station이 세그먼트 범위를 벗어남")
        s = station - self.start_sta
        if self.isstarted:
            theta = self.start_azimuth #H1
            pt = self.global_xy(s, self.start_coord, self.start_azimuth, isexit=False)
            azimuth = self.global_tangent(s , self.start_azimuth, isexit=False)
        else:
            theta = self.end_azimuth #h2
            rev_s = self.length - s
            pt = self.global_xy(rev_s, self.end_coord, theta, isexit=True)
            azimuth = self.global_tangent(rev_s, theta, isexit=True)
        return pt, azimuth

    def station_at_point(self, coord: Point2d) -> tuple[float, float]:
        pass

    def is_contains_station(self, station: float) -> bool:
        pass

    def is_contains_point(self, point: Point2d) -> bool:
        pass

    def reverse(self):
        pass

    def create_offset(self, offset_distance: float):
        raise NotImplementedError

    def split_to_segment(self, coord: Point2d):
        raise NotImplementedError

    #전역좌표
    def global_xy(self, s, origin: Point2d, origin_az: float, isexit=False) -> Point2d:
        """로컬좌표(x,y)를 글로벌 좌표로 변환하여 실제 점 반환"""
        pt = self.geom.local_xy(s)
        if isexit:
            pt.x = -pt.x
        if self.direction == CurveDirection.RIGHT:
            pt.y = -pt.y

        ca = math.cos(origin_az)
        sa = math.sin(origin_az)

        gx = origin.x + pt.x * ca - pt.y * sa
        gy = origin.y + pt.x * sa + pt.y * ca

        return Point2d(gx, gy)

    #전역접선각
    def global_tangent(self, s, origin_az: float, isexit=False) -> float:
        t = self.geom.local_tangent(s)
        if isexit:
            t = -t

        return origin_az + t