from __future__ import annotations

import math
from typing import Optional, Union

from .geometry import Geometry, AngleUnit, PointLike
from .point2d import Point2d
from .arc import Arc


class BulgeSegment(Geometry):
    """
    DXF bulge 세그먼트.

    bulge = tan(θ/4). 양수면 반시계, 음수면 시계 방향 호.
    bulge == 0이면 직선.
    """

    __slots__ = ('start', 'end', 'bulge')

    def __init__(self, start: Point2d, end: Point2d, bulge: float = 0.0):
        self.start = start
        self.end = end
        self.bulge = float(bulge)

    # ---- 파생 속성 ----

    @property
    def is_line(self) -> bool:
        return self.bulge == 0.0

    @property
    def chord(self) -> float:
        return self.start.distance_to(self.end)

    @property
    def theta(self) -> float:
        """중심각 (부호 유지). bulge=0이면 0."""
        return 4 * math.atan(self.bulge)

    @property
    def radius(self) -> Optional[float]:
        if self.is_line:
            return None
        return self.chord / (2 * math.sin(abs(self.theta) / 2))

    @property
    def center(self) -> Point2d:
        """bulge=0이면 chord 중점."""
        mid = Point2d((self.start.x + self.end.x) / 2,
                      (self.start.y + self.end.y) / 2)
        if self.is_line:
            return mid
        chord_angle = math.atan2(self.end.y - self.start.y,
                                 self.end.x - self.start.x)
        perp = chord_angle + (math.pi / 2 if self.bulge > 0 else -math.pi / 2)
        offset = math.sqrt(max(0.0, self.radius ** 2 - (self.chord / 2) ** 2))
        return mid.moved(perp, offset)

    @property
    def start_angle(self) -> Optional[float]:
        if self.is_line:
            return None
        return math.atan2(self.start.y - self.center.y,
                          self.start.x - self.center.x)

    @property
    def end_angle(self) -> Optional[float]:
        if self.is_line:
            return None
        return math.atan2(self.end.y - self.center.y,
                          self.end.x - self.center.x)

    @property
    def length(self) -> float:
        if self.is_line:
            return self.chord
        return abs(self.radius * self.theta)

    @property
    def as_arc(self) -> Optional[Arc]:
        """호로 변환. bulge=0이면 None."""
        if self.is_line:
            return None
        if self.bulge > 0:
            return Arc(self.center, self.radius, self.start_angle, self.end_angle)
        # 시계 방향: Arc는 반시계만 지원하므로 시작/끝 교환
        return Arc(self.center, self.radius, self.end_angle, self.start_angle)

    # ---- Geometry 계약 ----

    def move(self, angle: float, distance: float) -> None:
        self.start.move(angle, distance)
        self.end.move(angle, distance)

    def rotate(self, angle: float, origin: Optional[Point2d] = None) -> None:
        if origin is None:
            origin = self.center
        self.start.rotate(angle, origin)
        self.end.rotate(angle, origin)

    def distance_to(self, other: PointLike) -> float:
        point = _to_point(other)
        if self.is_line:
            return _segment_distance(self.start, self.end, point)
        arc = self.as_arc
        return arc.distance_to(point)

    def angle_to(self, other: PointLike,
                 unit: AngleUnit = AngleUnit.RAD) -> float:
        point = _to_point(other)
        angle = math.atan2(point.y - self.start.y, point.x - self.start.x)
        return math.degrees(angle) if unit is AngleUnit.DEG else angle

    def copy(self) -> 'BulgeSegment':
        return BulgeSegment(self.start.copy(), self.end.copy(), self.bulge)

    def _identity(self) -> tuple:
        return (self.start._identity(), self.end._identity(), self.bulge)


def _segment_distance(a: Point2d, b: Point2d, p: Point2d) -> float:
    dx, dy = b.x - a.x, b.y - a.y
    if dx == 0 and dy == 0:
        return a.distance_to(p)
    t = ((p.x - a.x) * dx + (p.y - a.y) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(p.x - (a.x + t * dx), p.y - (a.y + t * dy))


def _to_point(obj: PointLike) -> Point2d:
    if isinstance(obj, Point2d):
        return obj
    if isinstance(obj, tuple) and len(obj) == 2:
        return Point2d(*obj)
    if isinstance(obj, Geometry):
        return obj.center
    raise TypeError(f"cannot interpret as point: {obj!r}")