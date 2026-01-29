from vector3 import Vector3


class CoordinateTransform:
    def to_world(self, v: Vector3) -> Vector3:
        raise NotImplementedError

    def from_world(self, v: Vector3) -> Vector3:
        raise NotImplementedError