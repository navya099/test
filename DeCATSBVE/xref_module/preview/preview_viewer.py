import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets

from xref_module.preview.preview_plotter import PreviewPlotter


class PreviewViewer:
    def __init__(self, title="미리보기", projection="top"):
        self.title = title
        self.app = None
        self.win = None
        self.plot = None
        self.plotter = None
        self.objects = []
        self.projection = projection

    def initialize(self):
        # 이미 창이 살아있으면 다시 띄우기
        if self.win is not None:
            self.win.show()
            self.win.raise_()
            self.win.activateWindow()
            return

        self._ensure_app()
        self._build_window()
        self.win.show()

    def _ensure_app(self):
        self.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    def _build_window(self):
        self.win = pg.GraphicsLayoutWidget(title=self.title)
        self.plot = self.win.addPlot()
        self.plot.setAspectLocked(True)
        self.plot.showGrid(x=True, y=True)
        self.plotter = PreviewPlotter(self.plot, projection=self.projection)

    def add_object(self, obj):
        self.objects.append(obj)

    def clear(self):
        self.objects.clear()
        self.plotter.clear()

    def draw(self):
        self.initialize()
        self.plotter.draw_layers(self.objects)

    def set_projection(self, projection):
        self.projection = projection
        if self.plotter:
            self.plotter.set_projection(projection)