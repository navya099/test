from dataclasses import dataclass, field
import math

from AutoCAD.point2d import Point2d
from curvedirection import CurveDirection
from data.segment.segment import Segment
from math_utils import calculate_destination_coordinates, find_curve_direction


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

    @property
    def midpoint(self) -> Point2d:
        mid_sta = (self.start_sta + self.end_sta) / 2
        pt, _ = self.point_at_station(mid_sta, 0)
        return pt

    def distance_to_point(self, point: Point2d) -> float:
        """
        점과 원호(곡선 세그먼트) 사이의 최단 거리 계산
        (Shapely 사용하지 않음, 순수 수학 기반)
        """
        px, py = point.x, point.y
        cx, cy = self.center_coord.x, self.center_coord.y
        r = self.radius

        # 중심-점 벡터
        dx = px - cx
        dy = py - cy
        dist_cp = math.hypot(dx, dy)
        theta_p = math.atan2(dy, dx)

        # 시작/끝 각도 계산
        theta_start = self.start_azimuth
        theta_end = self.end_azimuth

        # 곡선 방향에 따라 각도 보정
        if self.direction == CurveDirection.RIGHT and theta_end > theta_start:
            theta_end -= 2 * math.pi
        elif self.direction == CurveDirection.LEFT and theta_end < theta_start:
            theta_end += 2 * math.pi

        # θp를 같은 범위로 보정
        theta_norm = theta_p
        while theta_norm < min(theta_start, theta_end):
            theta_norm += 2 * math.pi
        while theta_norm > max(theta_start, theta_end):
            theta_norm -= 2 * math.pi

        # 투영 각도가 호 범위 내에 있으면 → 원 위로 수직 투영 가능
        if min(theta_start, theta_end) <= theta_norm <= max(theta_start, theta_end):
            return abs(dist_cp - r)
        else:
            # 범위 밖이면 시작점 or 끝점 거리 중 최소값
            sx, sy = self.start_coord.x, self.start_coord.y
            ex, ey = self.end_coord.x, self.end_coord.y
            dist_start = math.hypot(px - sx, py - sy)
            dist_end = math.hypot(px - ex, py - ey)
            return min(dist_start, dist_end)

    def point_at_station(self, station: float, offset: float = 0.0) -> tuple[Point2d, float]:
        """
        단곡선(Simple Circular Curve) station 기반 좌표 계산
        반환값: (Point2d, tangent_angle)
        """
        # --- 1) Station 비율 계산 ---
        if station < self.start_sta or station > self.end_sta:
            raise ValueError("Station이 세그먼트 범위를 벗어남")

        arclength = self.end_sta - self.start_sta              # 곡선 길이
        s = station - self.start_sta                  # 곡선 시작점으로부터의 곡선상 거리

        # --- 2) 곡률각(θ) 계산 ---
        theta = s / self.radius                       # 라디안 (arc length = R * θ)

        # 방향이 Left면 +, Right면 - 회전
        if self.direction == CurveDirection.RIGHT:
            theta = -theta

        # --- 3) 곡선 시작점의 중심각 계산 ---
        # 벡터 from center → start
        dx = self.start_coord.x - self.center_coord.x
        dy = self.start_coord.y - self.center_coord.y
        start_angle = math.atan2(dy, dx)                   # 라디안

        # --- 4) 목표 각도 ---
        target_angle = start_angle + theta

        # --- 5) 중심 기준 회전하여 좌표 계산 ---
        x = self.center_coord.x + self.radius * math.cos(target_angle)
        y = self.center_coord.y + self.radius * math.sin(target_angle)
        pt = Point2d(x, y)

        # --- 6) Offset 적용 (곡선의 법선 방향으로) ---
        # 곡선 tangent는 ±90° 회전한 방향
        # tangent angle = target_angle + 90°(Left), -90°(Right)
        if self.direction == CurveDirection.LEFT:
            tangent_angle = target_angle + math.pi / 2
        else:
            tangent_angle = target_angle - math.pi / 2

        if offset != 0:
            ox = offset * math.cos(tangent_angle)
            oy = offset * math.sin(tangent_angle)
            pt = Point2d(pt.x + ox, pt.y + oy)

        # --- 7) 반환: (좌표, 방위각(진행 방향)) ---
        # tangent_angle 자체가 곡선의 진행 방향
        #정규화
        tangent_angle = math.atan2(math.sin(tangent_angle), math.cos(tangent_angle))
        return pt, tangent_angle

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