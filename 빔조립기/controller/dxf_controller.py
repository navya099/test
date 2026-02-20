import ezdxf
class DXFController:
    def __init__(self, projection='front'):
        self.projection = projection
        self.doc = ezdxf.new()
        self.msp = self.doc.modelspace()

    def _draw_mesh(self, csvobj):

        for mesh in csvobj.meshes:
            vertices = mesh.vertices

            for face in mesh.faces:
                edges = [
                    (face.a, face.b),
                    (face.b, face.c),
                    (face.c, face.a),
                ]

                for i, j in edges:
                    p1 = self._project(
                        vertices[i].x,
                        vertices[i].y,
                        vertices[i].z,
                    )
                    p2 = self._project(
                        vertices[j].x,
                        vertices[j].y,
                        vertices[j].z,
                    )

                    self.msp.add_line(p1, p2)
    def export_dxf(self, layers, filename):
        for layer in layers:
            # 1. Mesh 렌더링
            if layer.mesh:
                self._draw_mesh(
                    layer.mesh,

                )

        self.doc.saveas(filename)

    def _project(self, x, y, z):
        if self.projection == "front": return x, z
        if self.projection == "side": return y, z
        return x, y  # 기본 top

    def set_projection(self, projection):
        self.projection = projection

    def _color_from_category(self, category: str) -> str:
        return {
            "BEAM": "skyblue",
            "POLE": "skyblue",
            "BRACKET": "purple",
            "TRACK": "white",
            "STRUCTURE": "skyblue",
        }.get(category, "white")

    def _color_to_index(self, color: str) -> int:
        # 간단 매핑 예시
        mapping = {"white": 7, "skyblue": 4, "purple": 6}
        return mapping.get(color, 7)
