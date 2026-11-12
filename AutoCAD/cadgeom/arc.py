from __future__ import annotations

import math
from typing import Optional, Union

from .geometry import Geometry, AngleUnit, PointLike
from .point2d import Point2d


class Arc(Geometry):
    """2D 호. start_angle → end_angle은 항상 반시계 방향."""

    __slots__ = ('_center', 'radius', 'start_angle', 'end_angle')

    def __init__(self, center: Point2d, radius: float,
                 start_angle: float, end_angle: float):
        if radius <= 0:
            raise ValueError(f"radius must be positive, got {radius}")
        self._center = center
        self.radius = float(radius)
        self.start_angle = float(start_angle)
        self.end_angle = float(end_angle)

    # ---- 파생 속성 ----

    @property
    def center(self) -> Point2d:
        return self._center

    @property
    def theta(self) -> float:
        """호의 중심각 (0, 2π]. 항상 반시계 방향."""
        t = (self.end_angle - self.start_angle) % (2 * math.pi)
        return t if t > 0 else 2 * math.pi

    @property
    def start_point(self) -> Point2d:
        return self._point_at(self.start_angle)

    @property
    def end_point(self) -> Point2d:
        return self._point_at(self.end_angle)

    @property
    def mid_point(self) -> Point2d:
        return self._point_at(self.start_angle + self.theta / 2)

    @property
    def length(self) -> float:
        return self.theta * self.radius

    @property
    def chord_length(self) -> float:
        return self.start_point.distance_to(self.end_point)

    # ---- Geometry 계약 ----

    def move(self, angle: float, distance: float) -> None:
        self._center.move(angle, distance)

    def rotate(self, angle: float, origin: Optional[Point2d] = None) -> None:
        if origin is None:
            origin = self._center
        self._center.rotate(angle, origin)
        self.start_angle += angle
        self.end_angle += angle

    def distance_to(self, other: PointLike) -> float:
        point = _to_point(other)
        dist_to_center = self._center.distance_to(point)
        angle_p = math.atan2(point.y - self._center.y,
                             point.x - self._center.x)
        if self._angle_in_range(angle_p):
            return abs(dist_to_center - self.radius)
        return min(self.start_point.distance_to(point),
                   self.end_point.distance_to(point))

    def angle_to(self, other: PointLike,
                 unit: AngleUnit = AngleUnit.RAD) -> float:
        point = _to_point(other)
        sp = self.start_point
        angle = math.atan2(point.y - sp.y, point.x - sp.x)
        return math.degrees(angle) if unit is AngleUnit.DEG else angle

    def copy(self) -> 'Arc':
        return Arc(self._center.copy(), self.radius,
                   self.start_angle, self.end_angle)

    def _identity(self) -> tuple:
        return (self._center._identity(), self.radius,
                self.start_angle, self.end_angle)

    # ---- 내부 ----

    def _point_at(self, angle: float) -> Point2d:
        return Point2d(self._center.x + self.radius * math.cos(angle),
                       self._center.y + self.radius * math.sin(angle))

    def _angle_in_range(self, angle: float) -> bool:
        a = angle % (2 * math.pi)
        start = self.start_angle % (2 * math.pi)
        end = self.end_angle % (2 * math.pi)
        if start <= end:
            return start <= a <= end
        return a >= start or a <= end


def _to_point(obj: PointLike) -> Point2d:
    if isinstance(obj, Point2d):
        return obj
    if isinstance(obj, tuple) and len(obj) == 2:
        return Point2d(*obj)
    if isinstance(obj, Geometry):
        return obj.center
    raise TypeError(f"cannot interpret as point: {obj!r}")