# core/parser/sketchup_csv.py
from model.objmodel.csvobject import CSVObject
from vector3 import Vector3
from model.objmodel.mesh.mesh import Mesh
from model.objmodel.face.face import Face
from world.coordinatesystem import CoordinateSystem

class CSVObjectParser:
    def __init__(self, lines):
        self.lines = lines

    def parse(self) -> CSVObject:
        try:
            meshes: list[Mesh] = []

            cur_vertices: list[Vector3] = []

            cur_faces: list[Face] = []

            for line in self.lines:
                line = line.strip()
                if not line:
                    continue

                parts = [p.strip() for p in line.split(",") if p.strip()]
                cmd = parts[0]

                if cmd == "CreateMeshBuilder":
                    if cur_vertices:
                        meshes.append(
                            Mesh(
                                vertices=cur_vertices,
                                faces=cur_faces,
                            )
                        )
                    cur_vertices = []
                    cur_faces = []

                elif cmd == "AddVertex":
                    x, y, z = map(float, parts[1:4])
                    cur_vertices.append(Vector3(x, y, z))

                elif cmd == "AddFace":
                    a, b, c = map(int, parts[1:4])
                    cur_faces.append(Face(a, b, c))

            # 마지막 Mesh
            if cur_vertices:
                meshes.append(
                    Mesh(
                        vertices=cur_vertices,
                        faces=cur_faces,
                    )
                )

            obj = CSVObject(meshes)

            obj.coordsystem=CoordinateSystem.OPENBVE
            return obj
        except Exception as e:
            raise ValueError(f'파싱 실패 {e}')