# alignment/alignment.py
import logging
from .rail import Rail
from vector2 import Vector2

logger = logging.getLogger(__name__)

class Alignment:
    def __init__(self, name: str):
        self.name = name
        self.raildata: list[Rail] = []
        self.curvedata: list = []

    def compute_directions_for_alignment(self):
        if len(self.raildata) < 2:
            return
        for i in range(len(self.raildata) - 1):
            curr, nxt = self.raildata[i], self.raildata[i + 1]
            curr.direction = Vector2(x=nxt.coord.x - curr.coord.x, y=nxt.coord.z - curr.coord.z)
        # 마지막 rail direction 채우기
        self.raildata[-1].direction = self.raildata[-2].direction

    @classmethod
    def from_raildata(cls, name, raildata):
        if not raildata:
            raise ValueError(f"'{name}'의 raildata가 비어 있습니다.")
        al = cls(name)
        al.raildata = list(raildata)
        al.compute_directions_for_alignment()
        return al