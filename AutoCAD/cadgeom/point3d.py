from __future__ import annotations

import math
from typing import Optional, Tuple, Union, Literal

from .geometry import Geometry, AngleUnit, Number
from .point2d import Point2d


class Point3d(Geometry):
    """3D 점. rotate는 XY 평면 회전만 수행하며 z는 불변."""

    __slots__ = ('x', 'y', 'z')

    def __init__(self, x: Number, y: Number, z: Number):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    @property
    def center(self) -> Point2d:
        """회전/거리 기준점은 XY 투영."""
        return Point2d(self.x, self.y)

    def move(self, angle: float, distance: float) -> None:
        """XY 평면 극좌표 이동. z는 불변."""
        self.x += distance * math.cos(angle)
        self.y += distance * math.sin(angle)

    def translate(self, dx: float, dy: float, dz: float = 0.0) -> None:
        """직교 이동 (z 포함)."""
        self.x += dx
        self.y += dy
        self.z += dz

    def rotate(self, angle: float, origin: Optional[Point2d] = None) -> None:
        """XY 평면 회전. z 불변."""
        if origin is None:
            return
        dx = self.x - origin.x
        dy = self.y - origin.y
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        self.x = dx * cos_a - dy * sin_a + origin.x
        self.y = dx * sin_a + dy * cos_a + origin.y

    def rotate3d(self, angle: float, origin: Optional['Point3d'] = None,
                 axis: Literal['x', 'y', 'z'] = 'z') -> None:
        """3D 축 회전."""
        if origin is None:
            origin = self
        dx, dy, dz = self.x - origin.x, self.y - origin.y, self.z - origin.z
        c, s = math.cos(angle), math.sin(angle)
        if axis == 'x':
            y_new = dy * c - dz * s
            z_new = dy * s + dz * c
            self.y = y_new + origin.y
            self.z = z_new + origin.z
        elif axis == 'y':
            x_new = dx * c + dz * s
            z_new = -dx * s + dz * c
            self.x = x_new + origin.x
            self.z = z_new + origin.z
        elif axis == 'z':
            x_new = dx * c - dy * s
            y_new = dx * s + dy * c
            self.x = x_new + origin.x
            self.y = y_new + origin.y
        else:
            raise ValueError(f"axis must be 'x', 'y', or 'z', got {axis!r}")

    def distance_to(self, other: Union['Point3d', Point2d, Tuple[float, float, float]],
                    mode: Literal['2d', '3d'] = '3d') -> float:
        ox, oy, oz = _as_xyz(other)
        dx, dy, dz = ox - self.x, oy - self.y, oz - self.z
        if mode == '2d':
            return math.hypot(dx, dy)
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def angle_to(self, other: Union['Point3d', Point2d],
                 unit: AngleUnit = AngleUnit.RAD) -> float:
        """XY 평면 방위각. 3D 방위/고도는 azimuth_elevation_to 사용."""
        ox, oy, _ = _as_xyz(other)
        angle = math.atan2(oy - self.y, ox - self.x)
        return math.degrees(angle) if unit is AngleUnit.DEG else angle

    def azimuth_elevation_to(self, other: Union['Point3d', Point2d]
                             ) -> Tuple[float, float]:
        """(azimuth, elevation) 라디안 반환."""
        ox, oy, oz = _as_xyz(other)
        dx, dy, dz = ox - self.x, oy - self.y, oz - self.z
        azimuth = math.atan2(dy, dx)
        horizontal = math.hypot(dx, dy)
        elevation = math.atan2(dz, horizontal)
        return azimuth, elevation

    def copy(self) -> 'Point3d':
        return Point3d(self.x, self.y, self.z)

    def _identity(self) -> tuple:
        return (self.x, self.y, self.z)


def _as_xyz(obj: Union[Point3d, Point2d, Tuple]) -> Tuple[float, float, float]:
    if isinstance(obj, Point3d):
        return obj.x, obj.y, obj.z
    if isinstance(obj, Point2d):
        return obj.x, obj.y, 0.0
    if isinstance(obj, tuple) and len(obj) == 3:
        return float(obj[0]), float(obj[1]), float(obj[2])
    raise TypeError(f"cannot interpret as 3d point: {obj!r}")