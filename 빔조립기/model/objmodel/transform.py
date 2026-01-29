from dataclasses import dataclass

from vector3 import Vector3


@dataclass(frozen=True)
class Transform:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rotation: float = 0.0
    pivot: Vector3 = Vector3(0,0,0)
