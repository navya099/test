from __future__ import annotations

import math
from typing import Optional, Union

from .geometry import Geometry, AngleUnit, PointLike
from .point2d import Point2d


class Line2d(Geometry):
    """2D 선분."""

    __slots__ = ('start', 'end')

    def __init__(self, start: Point2d, end: Point2d):
        self.start = start
        self.end = end

    # ---- 파생 속성 ----

    @property
    def length(self) -> float:
        return self.start.distance_to(self.end)

    @property
    def direction(self) -> float:
        return math.atan2(self.end.y - self.start.y, self.end.x - self.start.x)

    @property
    def center(self) -> Point2d:
        return Point2d((self.start.x + self.end.x) / 2,
                       (self.start.y + self.end.y) / 2)

    # ---- 유틸 ----

    def get_x_from_y(self, y: float) -> Optional[float]:
        """수직선이면 None."""
        if self.end.x == self.start.x:
            return None
        m = (self.end.y - self.start.y) / (self.end.x - self.start.x)
        b = self.start.y - m * self.start.x
        return (y - b) / m

    def get_y_from_x(self, x: float) -> Optional[float]:
        """수직선이면 None."""
        if self.end.x == self.start.x:
            return None
        m = (self.end.y - self.start.y) / (self.end.x - self.start.x)
        b = self.start.y - m * self.start.x
        return m * x + b

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
        """점이면 점-선분 거리, 선분이면 최소 거리."""
        if isinstance(other, Line2d):
            return min(
                self.distance_to_point(other.start),
                self.distance_to_point(other.end),
                other.distance_to_point(self.start),
                other.distance_to_point(self.end),
            )
        return self.distance_to_point(_to_point(other))

    def distance_to_point(self, point: Point2d) -> float:
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        if dx == 0 and dy == 0:
            return self.start.distance_to(point)
        t = ((point.x - self.start.x) * dx + (point.y - self.start.y) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        proj_x = self.start.x + t * dx
        proj_y = self.start.y + t * dy
        return math.hypot(point.x - proj_x, point.y - proj_y)

    def angle_to(self, other: PointLike, unit: AngleUnit = AngleUnit.RAD) -> float:
        angle = self.direction
        return math.degrees(angle) if unit is AngleUnit.DEG else angle

    def copy(self) -> 'Line2d':
        return Line2d(self.start.copy(), self.end.copy())

    def _identity(self) -> tuple:
        return (self.start._identity(), self.end._identity())


def _to_point(obj: PointLike) -> Point2d:
    if isinstance(obj, Point2d):
        return obj
    if isinstance(obj, tuple) and len(obj) == 2:
        return Point2d(*obj)
    if isinstance(obj, Geometry):
        return obj.center
    raise TypeError(f"cannot interpret as point: {obj!r}")