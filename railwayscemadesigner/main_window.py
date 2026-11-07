# main_window.py
"""툴바 + 캔버스 + 속성 패널."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QDockWidget, QFormLayout, QLineEdit,
    QDoubleSpinBox, QComboBox, QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QAction,  QShortcut, QKeySequence
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

        shortcut_del = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        shortcut_del.activated.connect(self._delete_selected)

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

        # 모드 토글 (체크 가능한 액션 그룹)
        from PyQt6.QtGui import QActionGroup
        self.mode_group = QActionGroup(self)
        self.mode_group.setExclusive(True)

        self.act_select = QAction("선택", self, checkable=True, checked=True)
        self.act_select.triggered.connect(lambda: self._set_mode("select"))
        self.mode_group.addAction(self.act_select)
        tb.addAction(self.act_select)

        self.act_add_node = QAction("노드 추가", self, checkable=True)
        self.act_add_node.triggered.connect(lambda: self._set_mode("add_node"))
        self.mode_group.addAction(self.act_add_node)
        tb.addAction(self.act_add_node)

        self.act_add_edge = QAction("엣지 추가", self, checkable=True)
        self.act_add_edge.triggered.connect(lambda: self._set_mode("add_edge"))
        self.mode_group.addAction(self.act_add_edge)
        tb.addAction(self.act_add_edge)

        tb.addSeparator()

        fit_act = QAction("화면 맞춤", self)
        fit_act.triggered.connect(self.fit_view)
        tb.addAction(fit_act)

    def _set_mode(self, mode):
        if self.scene is None:
            return
        self.scene.set_mode(mode)
        self.statusBar().showMessage(f"모드: {mode}")

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
        # 새 시그널 연결
        self.scene.node_add_requested.connect(self._on_add_node)
        self.scene.edge_requested.connect(self._on_add_edge)
        self.scene.node_selected.connect(panel.set_item)
        self.scene.selectionChanged.connect(self._on_selection_changed)

        self.fit_view()

    def _next_node_id(self):
        existing = {n.id for n in self.data.nodes}
        i = 1
        while f"N-{i:03d}" in existing:
            i += 1
        return f"N-{i:03d}"

    def _next_edge_id(self):
        existing = {e.id for e in self.data.edges}
        i = 1
        while f"E-{i:03d}" in existing:
            i += 1
        return f"E-{i:03d}"

    def _on_add_node(self, scene_x, scene_y):
        """새 노드를 가장 가까운 트랙에 귀속시켜 생성."""
        from model import Node
        import transform

        # 화면 좌표에서 가장 가까운 track의 base_y와 비교하여 트랙 선택
        best_track = None
        best_dist = float("inf")
        for trk_dict in self.scene.tracks_by_id.values():
            # track base y 추정: 화면 y가 가까운 것
            sign = transform.track_direction_sign(trk_dict)
            base_y = transform.track_base_y(trk_dict) * transform.SCALE_Y * sign
            dist = abs(scene_y - base_y)
            if dist < best_dist:
                best_dist = dist
                best_track = trk_dict

        # 간단히 기본 타입은 signal로
        mileage, lateral = transform.scene_to_node(scene_x, scene_y, best_track)
        new_node = Node(
            id=self._next_node_id(),
            type="signal",
            mileage=round(mileage, 4),
            track_id=best_track["id"],
            lateral_offset=round(lateral, 2),
            attrs={"signal_type": "home", "direction": "up", "aspects": ["R", "Y"]},
        )
        self.data.nodes.append(new_node)
        self._rebuild_scene()  # 단순 재구축 (나중에 증분으로 최적화)

    def _on_add_edge(self, node_a_item, node_b_item):
        from model import Edge
        a, b = node_a_item.node, node_b_item.node

        if a.track_id != b.track_id:
            QMessageBox.warning(self, "엣지 생성 불가",
                                "같은 선로(track) 상의 노드끼리만 엣지를 만들 수 있습니다.")
            return

        # 중복 검사 (양방향)
        for e in self.data.edges:
            if (e.from_id == a.id and e.to_id == b.id) or \
                    (e.from_id == b.id and e.to_id == a.id):
                QMessageBox.information(self, "중복", "이미 엣지가 존재합니다.")
                return

        # mileage 순서로 from/to 정렬
        if a.mileage <= b.mileage:
            from_id, to_id = a.id, b.id
            length = (b.mileage - a.mileage) * 1000.0
        else:
            from_id, to_id = b.id, a.id
            length = (a.mileage - b.mileage) * 1000.0

        new_edge = Edge(
            id=self._next_edge_id(),
            from_id=from_id,
            to_id=to_id,
            track_id=a.track_id,
            geometry={"type": "straight", "length": round(length, 1),
                      "radius": None, "start_tangent": 0.0, "end_tangent": 0.0},
        )
        self.data.edges.append(new_edge)
        self._rebuild_scene()

    def _delete_selected(self):
        if self.scene is None:
            return
        selected = self.scene.selectedItems()
        node_ids = {item.node.id for item in selected if isinstance(item, NodeItem)}
        if not node_ids:
            return

        # 노드 삭제
        self.data.nodes = [n for n in self.data.nodes if n.id not in node_ids]
        # 연결된 엣지도 삭제
        self.data.edges = [e for e in self.data.edges
                           if e.from_id not in node_ids and e.to_id not in node_ids]
        self._rebuild_scene()

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