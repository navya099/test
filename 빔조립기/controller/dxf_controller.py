import ezdxf
class DXFController:
    def __init__(self, projection='front'):
        self.projection = projection
        self.doc = ezdxf.new()
        self.msp = self.doc.modelspace()

    def _draw_mesh(self, csvobj, color=None, layer='0'):

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

                    self.msp.add_line(p1, p2, dxfattribs={'color': color, 'layer': layer})

    def _draw_3dmesh(self, csvobj, color=None,layer_name="DEFAULT"):
        for mesh in csvobj.meshes:
            vertices = mesh.vertices
            for face in mesh.faces:
                v1, v2, v3 = [vertices[i] for i in (face.a, face.b, face.c)]
                p1 = (v1.x, v1.y, v1.z)
                p2 = (v2.x, v2.y, v2.z)
                p3 = (v3.x, v3.y, v3.z)
                self.msp.add_3dface([p1, p2, p3], dxfattribs={'layer': layer_name, 'color': color})

    def export_dxf(self, layers, filename, option=''):
        self.doc = ezdxf.new()
        self.msp = self.doc.modelspace()
        for layer in layers:
            # 1. Mesh 렌더링
            if layer.mesh:
                if option == '2d':
                    self._draw_mesh(
                    layer.mesh,color=self._color_from_category(layer.category),
                    layer=layer.category
                    )
                elif option == '3d':
                    self._draw_3dmesh(layer.mesh, color=self._color_from_category(layer.category),layer_name=layer.category)
                else:
                    raise ValueError('option must be "2d" or "3d"')
        self.doc.saveas(filename)

    def _project(self, x, y, z):
        if self.projection == "front": return x, z
        if self.projection == "side": return y, z
        return x, y  # 기본 top

    def set_projection(self, projection):
        self.projection = projection

    def _color_from_category(self, category: str) -> int:
        return {
            "BEAM": 4,
            "POLE": 4,
            "BRACKET": 6,
            "TRACK": 7,
            "STRUCTURE": 4,
        }.get(category, 7)
