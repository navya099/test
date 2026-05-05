from alignment_geometry.rail import Rail
from alignment_geometry.curve import Curve
class Alignment:
    def __init__(self, name: str):
        self.name = name
        self.index = 0
        self.curvedata: list[Curve] = []
        self.raildata: list[Rail] = []