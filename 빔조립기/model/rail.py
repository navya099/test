from dataclasses import dataclass

from vector3 import Vector3

@dataclass
class RailData:
    index: int
    name: str
    brackets: list
    coord: Vector3
    uid: str

