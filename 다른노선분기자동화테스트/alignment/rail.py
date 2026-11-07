# alignment/rail.py
from dataclasses import dataclass, field
from vector3 import Vector3
from vector2 import Vector2

@dataclass
class Rail:
    station: float
    railindex: int
    rail_x: float
    rail_y: float
    object_index: int
    coord: Vector3 = field(default_factory=lambda: Vector3(x=0.0, y=0.0, z=0.0))
    direction: Vector2 = field(default_factory=lambda: Vector2(x=0.0, y=0.0))

    def __repr__(self):
        return f"Rail(sta={self.station}, idx={self.railindex}, x={self.rail_x}, y={self.rail_y})"