from __future__ import annotations

import math
from typing import Union, Tuple, Optional

from .geometry import Geometry, AngleUnit, PointLike, Number


class Point2d(Geometry):
    """2D 점."""

    __slots__ = ('x', 'y')

    def __init__(self, x: Number = 0.0, y: Number = 0.0):
        self.x = float(x)
        self.y = float(y)

    # ---- Geometry 계약 ----

    @property
    def center(self) -> 'Point2d':
        return self

    def move(self, angle: float, distance: float) -> None:
        self.x += distance * math.cos(angle)
        self.y += distance * math.sin(angle)

    def rotate(self, angle: float, origin: Optional['Point2d'] = None) -> None:
        if origin is None:
            return  # 자기 자신 중심 회전 = no-op
        dx = self.x - origin.x
        dy = self.y - origin.y
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        self.x = dx * cos_a - dy * sin_a + origin.x
        self.y = dx * sin_a + dy * cos_a + origin.y

    def distance_to(self, other: PointLike) -> float:
        ox, oy = _as_xy(other)
        return math.hypot(ox - self.x, oy - self.y)

    def angle_to(self, other: PointLike, unit: AngleUnit = AngleUnit.RAD) -> float:
        ox, oy = _as_xy(other)
        angle = math.atan2(oy - self.y, ox - self.x)
        return math.degrees(angle) if unit is AngleUnit.DEG else angle

    def copy(self) -> 'Point2d':
        return Point2d(self.x, self.y)

    # ---- 내부 ----

    def _identity(self) -> tuple:
        return (self.x, self.y)

    # ---- 연산자 편의 ----

    def __add__(self, other: 'Point2d') -> 'Point2d':
        return Point2d(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Point2d') -> 'Point2d':
        return Point2d(self.x - other.x, self.y - other.y)


def _as_xy(obj: PointLike) -> Tuple[float, float]:
    """Geometry 또는 (x, y) 튜플을 좌표로 변환."""
    if isinstance(obj, Point2d):
        return obj.x, obj.y
    if isinstance(obj, tuple) and len(obj) == 2:
        return float(obj[0]), float(obj[1])
    if isinstance(obj, Geometry):
        c = obj.center
        return c.x, c.y
    raise TypeError(f"cannot interpret as point: {obj!r}")