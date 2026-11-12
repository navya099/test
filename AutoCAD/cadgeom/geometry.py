"""
기하학 객체의 공통 계약.

각도 규약:
- 단위: 라디안 기본. 0rad = +X축, 반시계 방향이 양(+).
- "자기 중심(center)"은 각 객체가 정의하며, rotate(origin=None)의 기준점이다.
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Tuple, Union, Literal

Number = Union[int, float]
PointLike = Union['Geometry', Tuple[Number, Number]]


class AngleUnit(str, Enum):
    RAD = 'rad'
    DEG = 'deg'


class Geometry(ABC):
    """2D/3D 기하학 객체의 추상 기반 클래스."""

    # ---- 필수 계약 ----

    @property
    @abstractmethod
    def center(self) -> 'Point2d':
        """회전/거리 계산의 기준이 되는 중심점."""

    @abstractmethod
    def move(self, angle: float, distance: float) -> None:
        """극좌표 (angle, distance)만큼 제자리 이동."""

    @abstractmethod
    def rotate(self, angle: float, origin: Optional['Point2d'] = None) -> None:
        """origin 기준 회전. None이면 self.center 기준."""

    @abstractmethod
    def distance_to(self, other: PointLike) -> float:
        """other까지의 최단 거리."""

    @abstractmethod
    def angle_to(self, other: PointLike, unit: AngleUnit = AngleUnit.RAD) -> float:
        """self의 기준점에서 other 방향의 각도."""

    @abstractmethod
    def copy(self) -> 'Geometry':
        """깊은 복사본 반환."""

    # ---- 기본 구현 (하위 클래스에서 재정의 가능) ----

    def moved(self, angle: float, distance: float) -> 'Geometry':
        """이동된 새 객체 반환. 기본: copy 후 move."""
        new = self.copy()
        new.move(angle, distance)
        return new

    def rotated(self, angle: float, origin: Optional['Point2d'] = None) -> 'Geometry':
        """회전된 새 객체 반환. 기본: copy 후 rotate."""
        new = self.copy()
        new.rotate(angle, origin)
        return new

    # ---- 동등성 (좌표 기반, 부동소수점 허용 오차) ----

    def _identity(self) -> tuple:
        """하위 클래스가 자신의 상태를 튜플로 반환. __eq__/__hash__에 사용."""
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        a, b = self._identity(), other._identity()
        if len(a) != len(b):
            return False
        for x, y in zip(a, b):
            if isinstance(x, float) or isinstance(y, float):
                if not math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-9):
                    return False
            elif x != y:
                return False
        return True

    def __hash__(self) -> int:
        return hash(tuple(
            round(v, 9) if isinstance(v, float) else v
            for v in self._identity()
        ))

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._identity()})"