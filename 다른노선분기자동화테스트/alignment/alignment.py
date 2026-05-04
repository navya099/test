from .rail import Rail
from .curve import Curve
from vector2 import Vector2

class Alignment:
    def __init__(self, name: str):
        self.name = name
        self.raildata: list[Rail] = []
        self.curvedata: list[Curve] = []

    def compute_directions_for_alignment(self):
        for i in range(len(self.raildata) - 1):
            curr = self.raildata[i]
            nxt = self.raildata[i + 1]

            curr.direction = Vector2(
                x=nxt.coord.x - curr.coord.x,
                y=nxt.coord.z - curr.coord.z
            )

    @classmethod
    def from_raildata(cls, name, raildata):
        al = cls(name)
        al.raildata = raildata
        al.compute_directions_for_alignment()
        return al