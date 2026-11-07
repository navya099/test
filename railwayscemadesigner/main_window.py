# main_window.py

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QToolBar,
    QDockWidget, QFormLayout, QLabel,
    QDoubleSpinBox, QComboBox, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QAction, QActionGroup, QUndoStack, QKeySequence, QShortcut, QTransform
from PyQt6.QtCore import Qt

from model import StationData, Node, Edge
from canvas import StationScene, StationView, NodeItem
from undo_commands import (
    AddNodeCommand, DeleteNodesCommand, AddEdgeCommand,
    MoveNodeCommand, EditNodeCommand,
)
import transform


class PropertyPanel(QWidget):
    def __init__(self, scene: StationScene, main_window, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.main = main_window
        self.current_item = None
        self._updating = False
        self._edit_start = None   # 편집 시작 시 old 값 스냅샷

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

        # 편집 시작/종료 훅
        self.mileage_spin.editingFinished.connect(self._commit_mileage)
        self.lateral_spin.editingFinished.connect(self._commit_lateral)
        self.mileage_spin.valueChanged.connect(self._on_mileage_changed_live)
        self.lateral_spin.valueChanged.connect(self._on_lateral_changed_live)

    def set_item(self, item):
        self._updating = True
        try:
            self.current_item = item
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
                self._edit_start = (n.mileage, n.lateral_offset)
        finally:
            self._updating = False

    def _on_mileage_changed_live(self, val):
        # 드래그 중 실시간 반영 (undo 대상 아님)
        if self._updating or self.current_item is None:
            return
        self.current_item.node.mileage = val
        self._reposition()

    def _on_lateral_changed_live(self, val):
        if self._updating or self.current_item is None:
            return
        self.current_item.node.lateral_offset = val
        self._reposition()

    def _reposition(self):
        n = self.current_item.node
        x, y = transform.node_to_scene(
            {"mileage": n.mileage, "track_id": n.track_id,
             "lateral_offset": n.lateral_offset},
            self.scene.tracks_by_id
        )
        self.current_item.setPos(x, y)

    def _commit_mileage(self):
        self._commit_edit()

    def _commit_lateral(self):
        self._commit_edit()

    def _commit_edit(self):
        if self._updating or self.current_item is None or self._edit_start is None:
            return
        old_m, old_l = self._edit_start
        new_m = self.mileage_spin.value()
        new_l = self.lateral_spin.value()
        if abs(new_m - old_m) < 1e-6 and abs(new_l - old_l) < 1e-6:
            return
        node_id = self.current_item.node.id
        self.main.undo_stack.push(MoveNodeCommand(
            self.main.data, self.main._rebuild_scene,
            node_id, old_m, old_l, new_m, new_l,
        ))
        self._edit_start = (new_m, new_l)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("선로배선 수동배치 편집기")
        self.resize(1400, 800)

        self.data: StationData | None = None
        self.scene: StationScene | None = None
        self.view: StationView | None = None
        self.panel: PropertyPanel | None = None

        self.undo_stack = QUndoStack(self)
        self._rebuilding = False

        self._build_toolbar()

        self.central = QWidget()
        self.central_layout = QVBoxLayout(self.central)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(self.central)

        self.dock = QDockWidget("속성", self)
        self.dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)

        self.statusBar().showMessage("파일 > 열기로 station.json 로드")

        # Delete 단축키
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self,
                  activated=self._delete_selected)

    # ---------- 툴바 ----------

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

        undo_act = self.undo_stack.createUndoAction(self, "되돌리기")
        undo_act.setShortcut(QKeySequence.StandardKey.Undo)
        tb.addAction(undo_act)

        redo_act = self.undo_stack.createRedoAction(self, "다시 실행")
        redo_act.setShortcut(QKeySequence.StandardKey.Redo)
        tb.addAction(redo_act)

        tb.addSeparator()

        self.mode_group = QActionGroup(self)
        self.mode_group.setExclusive(True)

        self.act_select = QAction("선택", self)
        self.act_select.setCheckable(True)
        self.act_select.setChecked(True)
        self.act_select.triggered.connect(lambda: self._set_mode("select"))
        self.mode_group.addAction(self.act_select)
        tb.addAction(self.act_select)

        self.act_add_node = QAction("노드 추가", self)
        self.act_add_node.setCheckable(True)
        self.act_add_node.triggered.connect(lambda: self._set_mode("add_node"))
        self.mode_group.addAction(self.act_add_node)
        tb.addAction(self.act_add_node)

        self.act_add_edge = QAction("엣지 추가", self)
        self.act_add_edge.setCheckable(True)
        self.act_add_edge.triggered.connect(lambda: self._set_mode("add_edge"))
        self.mode_group.addAction(self.act_add_edge)
        tb.addAction(self.act_add_edge)

        tb.addSeparator()

        fit_act = QAction("화면 맞춤", self)
        fit_act.triggered.connect(self.fit_view)
        tb.addAction(fit_act)

    def _set_mode(self, mode: str):
        if self.scene is None:
            return
        self.scene.set_mode(mode)
        self.statusBar().showMessage(f"모드: {mode}")

    # ---------- 파일 ----------

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "JSON 열기", "", "JSON (*.json)")
        if not path:
            return
        try:
            self.data = StationData.from_json(path)
        except Exception as ex:
            QMessageBox.critical(self, "로드 실패", str(ex))
            return

        self.undo_stack.clear()
        self._rebuild_scene(fit=True)   # ← 최초 로드만 fit
        self.statusBar().showMessage(f"로드 완료: {path}")

    def save_file(self):
        if self.data is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "JSON 저장", "", "JSON (*.json)")
        if not path:
            return
        self.data.to_json(path)
        self.statusBar().showMessage(f"저장 완료: {path}")

    # ---------- scene 재구축 ----------

    def _rebuild_scene(self, fit: bool = False):
        if self.data is None:
            return
        if self._rebuilding:
            return
        self._rebuilding = True
        try:
            # 재구축 전 뷰 상태 저장 (fit=False일 때 복원용)
            old_transform = None
            old_center = None
            if self.view is not None and not fit:
                old_transform = self.view.transform()
                old_center = self.view.mapToScene(
                    self.view.viewport().rect().center()
                )

            # 재구축 전 선택 상태 저장
            selected_ids = set()
            if self.scene is not None:
                selected_ids = {
                    it.node.id for it in self.scene.selectedItems()
                    if isinstance(it, NodeItem)
                }
                # 시그널 해제
                for sig in (self.scene.selectionChanged,
                            self.scene.node_selected,
                            self.scene.node_add_requested,
                            self.scene.edge_requested,
                            self.scene.move_committed):
                    try:
                        sig.disconnect()
                    except (TypeError, RuntimeError):
                        pass
                self.scene.clearSelection()
                self.scene = None

            if self.view is not None:
                self.central_layout.removeWidget(self.view)
                self.view.setParent(None)
                self.view.deleteLater()
                self.view = None

            # 새 scene / view 생성
            self.scene = StationScene(self.data)
            self.view = StationView(self.scene)
            self.central_layout.addWidget(self.view)

            # 속성 패널 교체
            self.panel = PropertyPanel(self.scene, self)
            self.dock.setWidget(self.panel)

            # 시그널 연결
            self.scene.node_add_requested.connect(self._on_add_node)
            self.scene.edge_requested.connect(self._on_add_edge)
            self.scene.node_selected.connect(self.panel.set_item)
            self.scene.selectionChanged.connect(self._on_selection_changed)
            self.scene.move_committed.connect(self._on_move_committed)

            # 모드 재적용
            if self.act_add_edge.isChecked():
                self.scene.set_mode("add_edge")
            elif self.act_add_node.isChecked():
                self.scene.set_mode("add_node")
            else:
                self.scene.set_mode("select")

            # 선택 상태 복원
            for nid in selected_ids:
                if nid in self.scene.node_items:
                    self.scene.node_items[nid].setSelected(True)

            # 뷰 상태 복원
            if fit:
                self.fit_view()
            elif old_transform is not None:
                self.view.setTransform(old_transform)
                self.view.centerOn(old_center)
        finally:
            self._rebuilding = False

    def fit_view(self):
        if self.view and self.scene:
            self.view.fitInView(
                self.scene.itemsBoundingRect(),
                Qt.AspectRatioMode.KeepAspectRatio,
            )

    def _on_selection_changed(self):
        if self.scene is None or self.panel is None:
            return
        items = self.scene.selectedItems()
        if not items:
            self.panel.set_item(None)
            return
        item = items[0]
        if isinstance(item, NodeItem):
            self.panel.set_item(item)

    # ---------- 노드/엣지 생성 커맨드 ----------

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

    def _on_add_node(self, scene_x: float, scene_y: float):
        if self._rebuilding or self.data is None:
            return

        # 클릭 위치에 가장 가까운 트랙 선택
        best_track = None
        best_dist = float("inf")
        for trk in self.scene.tracks_by_id.values():
            sign = transform.track_direction_sign(trk)
            base_y = transform.track_base_y(trk) * transform.SCALE_Y * sign
            dist = abs(scene_y - base_y)
            if dist < best_dist:
                best_dist = dist
                best_track = trk

        if best_track is None:
            return

        mileage, lateral = transform.scene_to_node(scene_x, scene_y, best_track)
        new_node = Node(
            id=self._next_node_id(),
            type="signal",
            mileage=round(mileage, 4),
            track_id=best_track["id"],
            lateral_offset=round(lateral, 2),
            attrs={"signal_type": "home", "direction": "up", "aspects": ["R", "Y"]},
        )
        self.undo_stack.push(
            AddNodeCommand(self.data, self._rebuild_scene, new_node)
        )

    def _on_add_edge(self, node_a_item, node_b_item):
        if self._rebuilding or self.data is None:
            return
        a, b = node_a_item.node, node_b_item.node

        # 중복 검사
        for e in self.data.edges:
            if (e.from_id == a.id and e.to_id == b.id) or \
               (e.from_id == b.id and e.to_id == a.id):
                QMessageBox.information(self, "중복", "이미 엣지가 존재합니다.")
                return

        same_track = (a.track_id == b.track_id)
        switch_connection = False
        if not same_track:
            if a.type == "switch" and a.attrs.get("branch_track_id") == b.track_id:
                switch_connection = True
            elif b.type == "switch" and b.attrs.get("branch_track_id") == a.track_id:
                switch_connection = True

        if not (same_track or switch_connection):
            QMessageBox.warning(
                self, "엣지 생성 불가",
                "같은 선로이거나, 분기기를 경유한 연결만 허용됩니다.",
            )
            return

        # from/to 정렬
        if same_track:
            if a.mileage <= b.mileage:
                from_id, to_id = a.id, b.id
                length = (b.mileage - a.mileage) * 1000.0
            else:
                from_id, to_id = b.id, a.id
                length = (a.mileage - b.mileage) * 1000.0
        else:
            if a.type == "switch":
                from_id, to_id = a.id, b.id
            else:
                from_id, to_id = b.id, a.id
            length = abs(b.mileage - a.mileage) * 1000.0

        new_edge = Edge(
            id=self._next_edge_id(),
            from_id=from_id,
            to_id=to_id,
            track_id=a.track_id if same_track else (
                b.track_id if a.type == "switch" else a.track_id
            ),
            geometry={
                "type": "straight",
                "length": round(length, 1),
                "radius": None,
                "start_tangent": 0.0,
                "end_tangent": 0.0,
            },
        )
        self.undo_stack.push(
            AddEdgeCommand(self.data, self._rebuild_scene, new_edge)
        )

    def _delete_selected(self):
        if self.scene is None or self.data is None:
            return
        node_ids = {
            it.node.id for it in self.scene.selectedItems()
            if isinstance(it, NodeItem)
        }
        if not node_ids:
            return
        self.undo_stack.push(
            DeleteNodesCommand(self.data, self._rebuild_scene, node_ids)
        )

    def _on_move_committed(self, node_id, old_m, old_l, new_m, new_l):
        self.undo_stack.push(MoveNodeCommand(
            self.data, self._rebuild_scene,
            node_id, old_m, old_l, new_m, new_l,
        ))