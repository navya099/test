from dataclasses import dataclass, field
from AutoCAD.point2d import Point2d
from data.alignment.spiral.pointcalc import SpiralPointCalculator
from data.segment.segment import Segment
from data.alignment.spiral.geometry import TransitionCurvatureCalculator
import math

@dataclass
class CubicSegment(Segment):
    """
    3차포물선 완화곡선 세그먼트
    Attributes:
        start_azimuth: 시각 각도
        end_azimuth: 끝 각도
        radius: 곡선반경
        isstarted: 시작 완화곡선 여부
        start_coord: 시작 각도
        end_coord: 끝 각도
        geom: 지오메트리 정보
    """
    start_azimuth: float = 0.0
    end_azimuth: float = 0.0
    radius: float = 0.0
    isstarted: bool = False
    start_coord:  Point2d = field(default_factory=lambda: Point2d(0, 0))
    end_coord:  Point2d = field(default_factory=lambda: Point2d(0, 0))
    geom: TransitionCurvatureCalculator | None = None

    @property
    def length(self):
        """완화곡선 길이L"""
        return self.geom.params.l

    @property
    def a(self):
        """완화곡선 매개변수 A"""
        return self.geom.params.a

    def distance_to_point(self, point: Point2d) -> float:
        """
        점과 원호(곡선 세그먼트) 사이의 최단 거리 계산
        (Shapely 사용하지 않음, 순수 수학 기반)
        """
        pass

    def point_at_station(self, station: float, offset: float = 0.0) -> tuple[Point2d, float]:
        """
        station 기반 좌표 계산
        반환값: (Point2d, tangent_angle)
        """
        # --- 1) Station 비율 계산 ---
        if station < self.start_sta or station > self.end_sta:
            raise ValueError("Station이 세그먼트 범위를 벗어남")
        s = station - self.start_sta
        sp_calc = SpiralPointCalculator(self.geom.params, self.geom.dir)
        if self.isstarted:
            theta = self.geom.h1
            pt = sp_calc.global_xy(self.start_coord, theta, s)
            azimuth = sp_calc.tangent_bearing(s, theta)
        else:
            theta = self.geom.h2 + math.pi
            pt = sp_calc.global_xy(self.end_coord, theta, s)
            azimuth = sp_calc.tangent_bearing(s, self.geom.h2, isexit=True)
        return pt, azimuth

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
        raise NotImplementedError

    def split_to_segment(self, coord: Point2d):
        """세그먼트 분할(완화곡선은 미지원"""
        raise NotImplementedError