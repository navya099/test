from dataclasses import dataclass
from point2d import Point2D

@dataclass
class Point3D:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    @property
    def origin(self) -> tuple:
        return self.x, self.y, self.z

    def convert_2d(self):
        return Point2D(self.x, self.y)