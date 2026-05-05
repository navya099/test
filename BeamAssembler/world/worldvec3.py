from dataclasses import dataclass


@dataclass(frozen=True)
class WorldVec3:
    x: float
    y: float
    z: float
