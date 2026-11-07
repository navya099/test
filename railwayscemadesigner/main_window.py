# main_window.py
"""툴바 + 캔버스 + 속성 패널."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QDockWidget, QFormLayout, QLineEdit,
    QDoubleSpinBox, QComboBox, QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

from model import StationData
from canvas import StationScene, StationView, NodeItem


class PropertyPanel(QWidget):
    """선택한 노드의 속성 편집."""

    def __init__(self, scene: StationScene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.current_item: NodeItem | None = None

        layout = QFormLayout(self)

        self.id_label = QLabel("-")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["switch", "signal", "insulation_joint",
                                  "boundary", "buffer_stop"])
        self.mileage_spin = QDoubleSpinBox()
        self.mileage_spin.setDecimals(4)
        self.mileage_spin.setRange(0, 10000)
        self.lateral_spin = QDoubleSpinBox()
        self.lateral_spin.setDecimals(2)
        self.lateral_spin.setRange(-100, 100)
        self.track_label = QLabel("-")

        layout.addRow("ID", self.id_label)
        layout.addRow("Type", self.type_combo)
        layout.addRow("Track", self.track_label)
        layout.addRow("Mileage (km)", self.mileage_spin)
        layout.addRow("Lateral (m)", self.lateral_spin)

        # 값 변경 → 모델/화면 반영
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self.mileage_spin.valueChanged.connect(self._on_mileage_changed)
        self.lateral_spin.valueChanged.connect(self._on_lateral_changed)

        self._updating = False

    def set_item(self, item):
        self._updating = True
        try:
            if item is None:
                self.id_label.setText("-")
                self.track_label.setText("-")
                self.mileage_spin.setValue(0)
                self.lateral_spin.setValue(0)
            else:
                n = item.node
                self.id_label.setText(n.id)
                self.track_label.setText(n.track_id)
                self.type_combo.setCurrentText(n.type)
                self.mileage_spin.setValue(n.mileage)
                self.lateral_spin.setValue(n.lateral_offset)
        finally:
            self._updating = False

    def _on_type_changed(self, text):
        if self._updating or self.current_item is None:
            return
        self.current_item.node.type = text
        self.current_item.update()

    def _on_mileage_changed(self, val):
        if self._updating or self.current_item is None:
            return
        self.current_item.node.mileage = val
        self._reposition()

    def _on_lateral_changed(self, val):
        if self._updating or self.current_item is None:
            return
        self.current_item.node.lateral_offset = val
        self._reposition()

    def _reposition(self):
        import transform
        n = self.current_item.node
        x, y = transform.node_to_scene(
            {"mileage": n.mileage, "track_id": n.track_id,
             "lateral_offset": n.lateral_offset},
            self.scene.tracks_by_id
        )
        self.current_item.setPos(x, y)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("선로배선 수동배치 편집기")
        self.resize(1400, 800)

        self.data: StationData | None = None
        self.scene: StationScene | None = None
        self.view: StationView | None = None

        self._build_toolbar()

        # 중앙: 캔버스
        self.central = QWidget()
        self.central_layout = QVBoxLayout(self.central)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(self.central)

        # 우측: 속성 패널
        self.dock = QDockWidget("속성", self)
        self.dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)

        self.statusBar().showMessage("파일 > 열기로 station.json 로드")

    def _build_toolbar(self):
        tb = QToolBar("메인")
        self.addToolBar(tb)

        open_act = QAction("열기", self)
        open_act.triggered.connect(self.open_file)
        tb.addAction(open_act)

        save_act = QAction("저장", self)
        save_act.triggered.connect(self.save_file)
        tb.addAction(save_act)

        tb.addSeparator()

        fit_act = QAction("화면 맞춤", self)
        fit_act.triggered.connect(self.fit_view)
        tb.addAction(fit_act)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "JSON 열기", "", "JSON (*.json)")
        if not path:
            return
        try:
            self.data = StationData.from_json(path)
        except Exception as ex:
            QMessageBox.critical(self, "로드 실패", str(ex))
            return
        self._rebuild_scene()
        self.statusBar().showMessage(f"로드 완료: {path}")

    def _rebuild_scene(self):
        if self.data is None:
            return
        # 기존 위젯 정리
        if self.view is not None:
            self.central_layout.removeWidget(self.view)
            self.view.deleteLater()

        self.scene = StationScene(self.data)
        self.view = StationView(self.scene)
        self.central_layout.addWidget(self.view)

        # 속성 패널 연결
        panel = PropertyPanel(self.scene)
        self.dock.setWidget(panel)
        self.scene.node_selected.connect(panel.set_item)

        # 선택 변경 시그널
        self.scene.selectionChanged.connect(self._on_selection_changed)

        self.fit_view()

    def _on_selection_changed(self):
        if self.scene is None:
            return
        items = self.scene.selectedItems()
        if not items:
            self.scene.node_selected.emit(None)
            return
        item = items[0]
        if isinstance(item, NodeItem):
            self.scene.node_selected.emit(item)

    def fit_view(self):
        if self.view and self.scene:
            self.view.fitInView(self.scene.itemsBoundingRect(),
                                Qt.AspectRatioMode.KeepAspectRatio)

    def save_file(self):
        if self.data is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "JSON 저장", "", "JSON (*.json)")
        if not path:
            return
        self.data.to_json(path)
        self.statusBar().showMessage(f"저장 완료: {path}")