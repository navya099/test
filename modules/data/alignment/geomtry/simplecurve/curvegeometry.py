from dataclasses import dataclass
import math
from AutoCAD.point2d import Point2d
from curvedirection import CurveDirection
from data.alignment.geometry.segmentgeometry import SegmentGeometry


@dataclass
class CurveGeometry(SegmentGeometry):
    """단곡선 지오메트리 엔진"""
    center: Point2d
    radius: float
    start_angle: float   # rad
    end_angle: float     # rad
    direction: CurveDirection

    @property
    def delta(self) -> float:
        """중심각 (양수)"""
        return abs(self.end_angle - self.start_angle)

    @property
    def length(self) -> float:
        """호의 길이"""
        return self.radius * self.delta

    @property
    def tangent_length(self) -> float:
        """접선장 TL"""
        return self.radius * math.tan(self.delta / 2)

    @property
    def start_coord(self) -> Point2d:
        """시작 좌표"""
        return self.center.moved(self.start_angle, self.radius)

    @property
    def end_coord(self) -> Point2d:
        """끝 좌표"""
        return self.center.moved(self.end_angle, self.radius)

    @property
    def external_secant(self) -> float:
        """외선장 SL"""
        return self.radius * (1 / math.cos(self.delta / 2) - 1)

    @property
    def middle_oridante(self):
        """중앙종거 M"""
        return self.radius * (1 - math.cos(self.delta / 2))

    def tangent_at(self, s: float) -> float:
        #반지름 각도
        angle = self._angle_at(s)

        # 접선각 = 반지름각 ± 90°
        if self.direction == CurveDirection.LEFT:
            tangent = angle + math.pi / 2
        else:
            tangent = angle - math.pi / 2

        # 정규화
        return math.atan2(math.sin(tangent), math.cos(tangent))

    def point_at(self, s: float, offset: float = 0.0) -> Point2d:
        # 반지름 각도
        angle = self._angle_at(s)

        # 원 위 점
        pt = self.center.moved(angle, self.radius)

        if offset != 0.0:
            tan = self.tangent_at(s)
            # 좌(-), 우(+): 진행방향 기준
            pt.move(tan - math.pi / 2, offset)

        return pt

    def project_at(self, p: Point2d) -> tuple[Point2d, float]:
        cx, cy = self.center.x, self.center.y
        px, py = p.x, p.y

        # 중심 → 점
        vx = px - cx
        vy = py - cy
        d = math.hypot(vx, vy)

        if d == 0:
            # 중심점인 경우 (degenerate)
            proj = self.start_coord
            return proj, 0.0

        # 점의 극각
        ang = math.atan2(vy, vx)

        a0 = self.start_angle
        a1 = self.end_angle

        # 방향 보정
        if self.direction == CurveDirection.RIGHT and a1 > a0:
            a1 -= 2 * math.pi
        elif self.direction == CurveDirection.LEFT and a1 < a0:
            a1 += 2 * math.pi

        # ang를 호 범위로 이동
        while ang < min(a0, a1):
            ang += 2 * math.pi
        while ang > max(a0, a1):
            ang -= 2 * math.pi

        # ── 호 내부 투영
        if min(a0, a1) <= ang <= max(a0, a1):
            proj = self.center.moved(ang, self.radius)

            # 중심각 → s
            delta = ang - a0
            if self.direction == CurveDirection.RIGHT:
                delta = -delta
            s = abs(delta) * self.radius

            # offset (좌 -, 우 +)
            offset = self.radius - d
            return proj, offset

        # ── 범위 밖 → 시작 / 끝점 중 최소
        ds = math.hypot(px - self.start_coord.x, py - self.start_coord.y)
        de = math.hypot(px - self.end_coord.x, py - self.end_coord.y)

        if ds <= de:
            proj = self.start_coord
            s = 0.0
        else:
            proj = self.end_coord
            s = self.length

        # 접선 기준 좌/우 판정
        tan = self.tangent_at(s)
        dx = px - proj.x
        dy = py - proj.y
        cross = math.cos(tan) * dy - math.sin(tan) * dx
        offset = cross

        return proj, offset

    def distance_at(self, p: Point2d) -> float:
        pt, off = self.project_at(p)
        return abs(off)

    def _angle_at(self, s: float) -> float:
        """s 위치의 반지름 각도 (center 기준)"""
        theta = s / self.radius
        if self.direction == CurveDirection.RIGHT:
            theta = -theta
        return self.start_angle + theta

    def reversed(self):
        self.start_angle = self.end_angle  # rad
        self.end_angle = self.start_angle # rad
        if self.direction == CurveDirection.LEFT:
            self.direction = CurveDirection.RIGHT
        else:
            self.direction = CurveDirection.LEFT

    def get_offset(self, offset: float):
        if self.direction == CurveDirection.LEFT:
            self.radius = self.radius + offset
        else:
            self.radius = self.radius - offset

    def arc_length_between(self, p1: Point2d, p2: Point2d) -> float:
        """호 위의 두점 사이의 호의 길이"""

        a1 = math.atan2(p1.y - self.center.y, p1.x - self.center.x)
        a2 = math.atan2(p2.y - self.center.y, p2.x - self.center.x)

        delta = a2 - a1

        if self.direction == CurveDirection.RIGHT:
            if delta > 0:
                delta -= 2 * math.pi
        else:  # LEFT
            if delta < 0:
                delta += 2 * math.pi

        return abs(delta) * self.radius
