# ui/preview/preview_viewer.py

import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets


class PreviewViewer:
    """
    2D 선(Line) 미리보기 전용 Viewer
    - 입력: List[np.ndarray(N,2)]
    """

    def __init__(self, title="미리보기", projection=None, parent=None):
        self.objects = []   # 3D 객체만 저장
        self.title = title

        self.app = None
        self.win = None
        self.plot = None
        self.projection = projection
        self._initialized = False
    # -----------------------------
    # 초기화
    # -----------------------------
    def initialize(self):
        if self._initialized:
            return

        self._ensure_app()
        self._build_window()
        self.win.show()

        self._initialized = True

    # -----------------------------
    # 내부 구현
    # -----------------------------

    def _ensure_app(self):
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication(sys.argv)

    def _build_window(self):
        self.win = pg.GraphicsLayoutWidget(title=self.title)
        self.plot = self.win.addPlot()

        self.plot.setAspectLocked(True)
        self.plot.showGrid(x=True, y=True)
        self.plot.invertY(False)   # 필요시 True

    def clear(self):
        self.plot.clear()

    def add_object(self, pole_obj):
        self.objects.append(pole_obj)

    def draw(self):
        self.initialize()
        self.plot.clear()

        for obj in self.objects:
            vertices = obj.get_vertices()
            edges = obj.get_edges()

            xs = []
            ys = []

            for i, j in edges:
                p1 = self._project(*vertices[i])
                p2 = self._project(*vertices[j])

                xs.extend([p1[0], p2[0]])
                ys.extend([p1[1], p2[1]])

            self.plot.plot(xs, ys, connect='pairs')

    def _project(self, x, y, z):
        if self.projection == "front":
            return x, z  # 정면도
        elif self.projection == "side":
            return y, z  # 측면도
        elif self.projection == "top":
            return x, y  # 정면도
        else:
            raise ValueError(f"Unknown projection: {self.projection}")

    def set_projection(self, projection):
        self.projection = projection