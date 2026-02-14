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

        # 좌표 표시용 라벨 추가
        self.label = pg.LabelItem(justify='right')
        self.win.addItem(self.label)

        # 마우스 이동 이벤트 연결
        self.proxy = pg.SignalProxy(self.plot.scene().sigMouseMoved, rateLimit=60, slot=self._mouse_moved)

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



    def _mouse_moved(self, evt):
        pos = evt[0]  # QGraphicsSceneMouseEvent
        if self.plot.sceneBoundingRect().contains(pos):
            mousePoint = self.plot.vb.mapSceneToView(pos)
            x, y = mousePoint.x(), mousePoint.y()
            self.label.setText(f"x={x:.2f}, y={y:.2f}")

