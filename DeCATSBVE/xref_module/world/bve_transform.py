from xref_module.vector3.vector3 import Vector3
from xref_module.world.base_transform import CoordinateTransform


class OpenBVETransform(CoordinateTransform):
    def to_world(self, v):
        return Vector3(v.x, v.z, v.y)

    def from_world(self, v):
        return Vector3(v.x, v.z, v.y)