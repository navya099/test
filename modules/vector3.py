from vector2 import Vector2

class Vector3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def to2d(self) -> Vector2:
        return Vector2(self.x, self.y)

def to2d(v3) -> Vector2:
    return Vector2(v3.x, v3.y)