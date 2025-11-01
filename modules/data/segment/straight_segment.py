from dataclasses import dataclass, field
import math

from AutoCAD.point2d import Point2d
from data.segment.segment import Segment
from math_utils import calculate_bearing, calculate_distance

@dataclass
class StraightSegment(Segment):
    """직선 세그먼트"""
    start_coord: Point2d = field(default_factory=lambda: Point2d(0, 0))
    end_coord: Point2d = field(default_factory=lambda: Point2d(0, 0))

    @property
    def start_azimuth(self):
        return calculate_bearing(self.start_coord, self.end_coord)

    @property
    def end_azimuth(self):
        return self.start_azimuth

    @property
    def length(self):
        return calculate_distance(self.start_coord, self.end_coord)

    def distance_to_point(self, point: Point2d) -> float:
        """
        점과 직선 세그먼트 간 최단 거리 (수학적 계산)
        Shapely 없이 순수 벡터 기반
        """
        px, py = point.x, point.y
        ax, ay = self.start_coord.x, self.start_coord.y
        bx, by = self.end_coord.x, self.end_coord.y

        # 벡터 AB, AP
        dx, dy = bx - ax, by - ay
        seg_len_sq = dx * dx + dy * dy

        if seg_len_sq == 0:
            # 시작점과 끝점이 동일한 경우
            return math.hypot(px - ax, py - ay)

        # 투영 비율 t (0 ≤ t ≤ 1)
        t = ((px - ax) * dx + (py - ay) * dy) / seg_len_sq
        t = max(0, min(1, t))

        # 투영점 좌표
        proj_x = ax + t * dx
        proj_y = ay + t * dy

        # 거리 계산

        return math.hypot(px - proj_x, py - proj_y)

    #추상메서드
    def point_at_station(self, station: float, offset: float) -> tuple[Point2d, float]:
        """지정한 측점의 좌표와 방위각 반환"""
        pass

    def station_at_point(self, coord: Point2d) -> tuple[float, float]:
        """지정한 좌표의 측점 및 거리 반환"""
        pass

    def is_contains_station(self, station: float) -> bool:
        """지정한 측점이 세그먼트에 보함되는지 여부"""
        pass

    def is_contains_point(self, point: Point2d) -> bool:
        """지정한 점이 세그먼트에 보함되는지 여부"""
        pass

    def reverse(self):
        """세그먼트 뒤집기"""
        pass

    def create_offset(self, offset_distance: float):
        """세그먼트 객체의 평행(오프셋) 복제본을 생성"""
        pass

    def split_to_segment(self, coord: Point2d):
        """지정한 점으로 세그먼트 객체 분할"""
        #다음 세그먼트 생성
        new_seg = StraightSegment(
            start_coord=coord,
            end_coord=self.end_coord,
        )
        self.end_coord = coord
        return new_seg