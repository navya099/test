# core/geometry/mesh.py
from dataclasses import dataclass

from xref_module.objmodel.face.face import Face
from xref_module.vector3.vector3 import Vector3


@dataclass
class Mesh:
    vertices: list[Vector3]
    faces: list[Face]

    def iter_edges(self):
        for f in self.faces:
            yield f.a, f.b
            yield f.b, f.c
            yield f.c, f.a