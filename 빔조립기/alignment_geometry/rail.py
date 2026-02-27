from vector3 import Vector3
from vector2 import Vector2

class Rail:
    def __init__(self, station: float, railindex: int, rail_x: float, rail_y: float, object_index: int):
        self.station = station
        self.railindex = railindex
        self.rail_x = rail_x
        self.rail_y = rail_y
        self.object_index = object_index
        self.coord = Vector3(x=0, y=0, z=0)

        self.direction = Vector2(x=0, y=0)