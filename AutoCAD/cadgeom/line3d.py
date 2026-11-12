from __future__ import annotations

import math
from typing import Optional, Union, Literal

from .geometry import Geometry, AngleUnit
from .point2d import Point2d
from .point3d import Point3d


class Line3d(Geometry):
    """3D 선분."""

    __slots__ = ('start', 'end')

    def __init__(self, start: Point3d, end: Point3d):
        self.start = start
        self.end = end

    @property
    def length(self) -> float:
        return self.start.distance_to(self.end, mode='3d')

    @property
    def center(self) -> Point2d:
        """회전 기준점은 XY 투영 중점."""
        return Point2d((self.start.x + self.end.x) / 2,
                       (self.start.y + self.end.y) / 2)

    @property
    def direction_2d(self) -> float:
        """XY 평면 방위각."""
        return math.atan2(self.end.y - self.start.y,
                          self.end.x - self.start.x)

    # ---- Geometry 계약 ----

    def move(self, angle: float, distance: float) -> None:
        """XY 평면 극좌표 이동. z 불변."""
        self.start.move(angle, distance)
        self.end.move(angle, distance)

    def translate(self, dx: float, dy: float, dz: float = 0.0) -> None:
        """직교 이동 (z 포함)."""
        self.start.translate(dx, dy, dz)
        self.end.translate(dx, dy, dz)

    def rotate(self, angle: float, origin: Optional[Point2d] = None) -> None:
        if origin is None:
            origin = self.center
        self.start.rotate(angle, origin)
        self.end.rotate(angle, origin)

    def distance_to(self, other: Union['Line3d', Point3d, Point2d],
                    mode: Literal['2d', '3d'] = '3d') -> float:
        if isinstance(other, Line3d):
            return min(
                self.distance_to_point(other.start, mode),
                self.distance_to_point(other.end, mode),
                other.distance_to_point(self.start, mode),
                other.distance_to_point(self.end, mode),
            )
        return self.distance_to_point(_to_point3d(other), mode)

    def distance_to_point(self, point: Point3d,
                          mode: Literal['2d', '3d'] = '3d') -> float:
        """점-선분 최단 거리. 2d 모드에서는 XY 투영만 사용."""
        if mode == '2d':
            return Line2dProxy(self.start, self.end).distance_to_point(
                Point2d(point.x, point.y)
            )
        # 3D: 선분 위 최근접점
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        dz = self.end.z - self.start.z
        denom = dx * dx + dy * dy + dz * dz
        if denom == 0:
            return self.start.distance_to(point, mode='3d')
        t = ((point.x - self.start.x) * dx
             + (point.y - self.start.y) * dy
             + (point.z - self.start.z) * dz) / denom
        t = max(0.0, min(1.0, t))
        px = self.start.x + t * dx
        py = self.start.y + t * dy
        pz = self.start.z + t * dz
        return math.sqrt((point.x - px) ** 2
                         + (point.y - py) ** 2
                         + (point.z - pz) ** 2)

    def angle_to(self, other, unit: AngleUnit = AngleUnit.RAD) -> float:
        angle = self.direction_2d
        return math.degrees(angle) if unit is AngleUnit.DEG else angle

    def copy(self) -> 'Line3d':
        return Line3d(self.start.copy(), self.end.copy())

    def _identity(self) -> tuple:
        return (self.start._identity(), self.end._identity())


class Line2dProxy:
    """Line3d 내부 2D 거리 계산용 임시 헬퍼 (XY 투영)."""
    def __init__(self, start: Point3d, end: Point3d):
        self.sx, self.sy = start.x, start.y
        self.ex, self.ey = end.x, end.y

    def distance_to_point(self, p: Point2d) -> float:
        dx, dy = self.ex - self.sx, self.ey - self.sy
        if dx == 0 and dy == 0:
            return math.hypot(p.x - self.sx, p.y - self.sy)
        t = ((p.x - self.sx) * dx + (p.y - self.sy) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        return math.hypot(p.x - (self.sx + t * dx), p.y - (self.sy + t * dy))


def _to_point3d(obj) -> Point3d:
    if isinstance(obj, Point3d):
        return obj
    if isinstance(obj, Point2d):
        return Point3d(obj.x, obj.y, 0.0)
    raise TypeError(f"cannot interpret as 3d point: {obj!r}")