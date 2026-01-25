import pyqtgraph as pg

class PreviewPlotter:
    def __init__(self, plot, projection="top"):
        self.plot = plot
        self.projection = projection

    def clear(self):
        self.plot.clear()

    def draw_objects(self, objects):
        self.clear()
        for obj in objects:
            xs, ys = [], []
            for i, j in obj.get_edges():
                p1 = self._project(*obj.get_vertices()[i])
                p2 = self._project(*obj.get_vertices()[j])
                xs.extend([p1[0], p2[0]])
                ys.extend([p1[1], p2[1]])
            self.plot.plot(xs, ys, connect="pairs")

    def _project(self, x, y, z):
        if self.projection == "front": return x, z
        if self.projection == "side": return y, z
        return x, y  # 기본 top

    def set_projection(self, projection):
        self.projection = projection