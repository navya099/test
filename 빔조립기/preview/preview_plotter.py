import pyqtgraph as pg

class PreviewPlotter:
    def __init__(self, plot, projection="top"):
        self.plot = plot
        self.projection = projection

    def clear(self):
        self.plot.clear()

    def draw_objects(self, objects: list):
        self.clear()

        for csvobj in objects:
            for mesh in csvobj.meshes:
                vertices = mesh.vertices

                xs, ys = [], []

                for face in mesh.faces:
                    a, b, c = face.a, face.b, face.c

                    edges = [
                        (a, b),
                        (b, c),
                        (c, a),
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

                        xs.extend([p1[0], p2[0]])
                        ys.extend([p1[1], p2[1]])

                self.plot.plot(xs, ys, connect="pairs")

    def _project(self, x, y, z):
        if self.projection == "front": return x, z
        if self.projection == "side": return y, z
        return x, y  # 기본 top

    def set_projection(self, projection):
        self.projection = projection