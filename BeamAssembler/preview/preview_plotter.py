import pyqtgraph as pg

from preview.text_label import TextLabel


class PreviewPlotter:
    def __init__(self, plot, projection="top"):
        self.plot = plot
        self.projection = projection

    def clear(self):
        self.plot.clear()

    def draw_layers(self, layers: list):
        self.clear()

        for layer in layers:
            # 1. Mesh 렌더링
            if layer.mesh:
                self._draw_mesh(
                    layer.mesh,
                    color=layer.color or self._color_from_category(layer.category)
                )

            # 2. 라벨 렌더링
            if layer.label and layer.pivot:
                x, y = self._project(*layer.pivot)
                text_item = pg.TextItem(
                    layer.label,
                    color=layer.color or "black",
                    anchor=(0.5, 0)
                )
                text_item.setPos(x, y)
                self.plot.addItem(text_item)


    def _draw_mesh(self, csvobj, color):
        pen = pg.mkPen(color=color, width=1)
        for mesh in csvobj.meshes:
            vertices = mesh.vertices

            xs, ys = [], []

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

                    xs.extend([p1[0], p2[0]])
                    ys.extend([p1[1], p2[1]])

            self.plot.plot(xs, ys, connect="pairs", pen=pen)

    def _color_from_category(self, category: str) -> str:
        return {
            "BEAM": "skyblue",
            "POLE": "skyblue",
            "BRACKET": "purple",
            "TRACK": "white",
            "STRUCTURE": "skyblue",
        }.get(category, "white")

    def _project(self, x, y, z):
        if self.projection == "front": return x, z
        if self.projection == "side": return y, z
        return x, y  # 기본 top

    def set_projection(self, projection):
        self.projection = projection