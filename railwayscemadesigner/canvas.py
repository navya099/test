# canvas.py
"""QGraphicsScene 기반 캔버스. 노드 드래그 + 엣지 자동 갱신."""

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsItem
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
# canvas.py 상단
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QPolygonF, QTransform
import transform


NODE_STYLE = {
    "switch":           dict(color=QColor("red"),    shape="rect",  size=8,  label="분기기"),
    "signal":           dict(color=QColor("green"),  shape="tri",   size=8,  label="신호기"),
    "insulation_joint": dict(color=QColor("orange"), shape="line",  size=8,  label="절연절"),
    "boundary":         dict(color=QColor("gray"),   shape="cross", size=8,  label="경계"),
    "buffer_stop":      dict(color=QColor("purple"), shape="diamond", size=8, label="차막이"),
}


class NodeItem(QGraphicsItem):
    """노드 = 드래그 가능한 점."""

    def __init__(self, node, scene_ref):
        super().__init__()
        self.node = node
        self.scene_ref = scene_ref
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setZValue(10)
        self.setToolTip(f"{node.id} ({node.type})")

    def boundingRect(self):
        s = 10
        return QRectF(-s, -s, 2*s, 2*s)

    def paint(self, painter: QPainter, option, widget=None):
        st = NODE_STYLE.get(self.node.type, dict(color=QColor("gray"), shape="rect", size=6))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.setBrush(QBrush(st["color"]))
        s = st["size"]
        shape = st["shape"]

        if shape == "rect":
            painter.drawRect(QRectF(-s / 2, -s / 2, s, s))
        elif shape == "tri":
            pts = [QPointF(0, -s), QPointF(s, s), QPointF(-s, s)]
            painter.drawPolygon(QPolygonF(pts))
        elif shape == "line":
            painter.drawLine(QPointF(0, -s), QPointF(0, s))
        elif shape == "cross":
            painter.drawLine(QPointF(-s, -s), QPointF(s, s))
            painter.drawLine(QPointF(-s, s), QPointF(s, -s))
        elif shape == "diamond":
            pts = [QPointF(0, -s), QPointF(s, 0), QPointF(0, s), QPointF(-s, 0)]
            painter.drawPolygon(QPolygonF(pts))

        if self.isSelected():
            painter.setPen(QPen(QColor("blue"), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(-s, -s, 2 * s, 2 * s))

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.scene_ref.on_node_moved(self)
        return super().itemChange(change, value)


class EdgeItem(QGraphicsItem):
    """엣지 = 두 NodeItem 사이의 선. 노드 이동 시 자동 갱신."""

    def __init__(self, edge, node_a: NodeItem, node_b: NodeItem, track):
        super().__init__()
        self.edge = edge
        self.node_a = node_a
        self.node_b = node_b
        self.track = track
        self.setZValue(1)
        self.setToolTip(f"{edge.id} ({edge.track_id})")
        if track["type"] == "main":
            self.pen = QPen(Qt.GlobalColor.black, 2)
        else:
            self.pen = QPen(QColor("tab:blue") if False else QColor(30, 100, 200), 1.2)

    def boundingRect(self):
        p1 = self.node_a.pos()
        p2 = self.node_b.pos()
        return QRectF(p1, p2).normalized().adjusted(-5, -5, 5, 5)

    def paint(self, painter, option, widget=None):
        painter.setPen(self.pen)
        painter.drawLine(self.node_a.pos(), self.node_b.pos())

    def update_geometry(self):
        self.prepareGeometryChange()
        self.update()


class StationScene(QGraphicsScene):
    """정거장 장면. 노드 이동 시 연결 엣지 갱신 + 시그널 발생."""

    node_moved = pyqtSignal(object)
    node_selected = pyqtSignal(object)
    edge_requested = pyqtSignal(object, object)
    node_add_requested = pyqtSignal(float, float)

    rebuild_requested = pyqtSignal()  # 신규
    move_committed = pyqtSignal(str, float, float, float, float)  # 신규

    MODE_SELECT = "select"
    MODE_ADD_NODE = "add_node"
    MODE_ADD_EDGE = "add_edge"

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.tracks_by_id = data.tracks_by_id()
        self.node_items = {}    # node_id → NodeItem
        self.edge_items = []    # EdgeItem 리스트
        self.mode = self.MODE_SELECT
        self._edge_start = None  # 엣지 추가 모드에서 첫 클릭 노드
        self._build()
        self._drag_start = {}  # node_id → (mileage, lateral) 드래그 시작 스냅샷

    def request_rebuild(self):
        """커맨드가 모델을 바꾼 뒤 호출. MainWindow가 scene을 새로 만든다."""
        self.rebuild_requested.emit()

    def _build(self):
        self.clear()
        self.node_items.clear()
        self.edge_items.clear()

        # 1) 노드 아이템 생성
        for n in self.data.nodes:
            item = NodeItem(n, self)
            x, y = transform.node_to_scene(
                {"mileage": n.mileage, "track_id": n.track_id,
                 "lateral_offset": n.lateral_offset},
                self.tracks_by_id
            )
            item.setPos(x, y)
            self.addItem(item)
            self.node_items[n.id] = item

        # 2) 엣지 아이템 생성
        for e in self.data.edges:
            na = self.node_items.get(e.from_id)
            nb = self.node_items.get(e.to_id)
            if na is None or nb is None:
                continue
            edge_item = EdgeItem(e, na, nb, self.tracks_by_id[e.track_id])
            self.addItem(edge_item)
            self.edge_items.append(edge_item)

    def set_mode(self, mode: str):
        self.mode = mode
        self._edge_start = None
        # 모드별 드래그 허용 제어
        movable = (mode == self.MODE_SELECT)
        for item in self.node_items.values():
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, movable)

    def mousePressEvent(self, event):
        # 1) 선택 모드: 드래그 스냅샷 + 기본 동작
        if self.mode == self.MODE_SELECT:
            if event.button() == Qt.MouseButton.LeftButton:
                item = self.itemAt(event.scenePos(), QTransform())
                if isinstance(item, NodeItem):
                    self._drag_start[item.node.id] = (
                        item.node.mileage, item.node.lateral_offset
                    )
            super().mousePressEvent(event)
            return

        # 2) 좌클릭이 아니면 기본 동작
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        scene_pos = event.scenePos()

        # 3) 노드 추가 모드
        if self.mode == self.MODE_ADD_NODE:
            items = self.items(scene_pos)
            item = items[0] if items else None
            if not isinstance(item, NodeItem):
                self.node_add_requested.emit(scene_pos.x(), scene_pos.y())
            event.accept()
            return

        # 4) 엣지 추가 모드
        if self.mode == self.MODE_ADD_EDGE:
            items = self.items(scene_pos)
            item = next((it for it in items if isinstance(it, NodeItem)), None)
            if item is not None:
                if self._edge_start is None:
                    self._edge_start = item
                    item.setSelected(True)
                elif item is not self._edge_start:
                    self.edge_requested.emit(self._edge_start, item)
                    self._edge_start.setSelected(False)
                    self._edge_start = None
            else:
                if self._edge_start is not None:
                    self._edge_start.setSelected(False)
                    self._edge_start = None
            event.accept()
            return

        # 5) 그 외
        super().mousePressEvent(event)

    # ---- 드래그 시작/종료 훅 ----
    def on_node_moved(self, node_item):
        # 기존: 엣지 갱신 + 모델 반영 (드래그 중)
        for e in self.edge_items:
            if e.node_a is node_item or e.node_b is node_item:
                e.update_geometry()

        track = self.tracks_by_id[node_item.node.track_id]
        pos = node_item.pos()
        import transform
        mileage, lateral = transform.scene_to_node(pos.x(), pos.y(), track)
        node_item.node.mileage = round(mileage, 4)
        node_item.node.lateral_offset = round(lateral, 2)

        self.node_moved.emit(node_item.node.id)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if not self._drag_start:
            return

        # 드래그 종료: 시작 스냅샷과 비교해서 이동이 있으면 커맨드 발행
        for node_id, (old_m, old_l) in list(self._drag_start.items()):
            item = self.node_items.get(node_id)
            if item is None:
                continue
            new_m, new_l = item.node.mileage, item.node.lateral_offset
            if abs(new_m - old_m) > 1e-6 or abs(new_l - old_l) > 1e-6:
                self.move_committed.emit(node_id, old_m, old_l, new_m, new_l)

        self._drag_start.clear()

class StationView(QGraphicsView):
    """확대/축소 + 팬. 마우스 휠로 줌."""

    def __init__(self, scene: StationScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setBackgroundBrush(QBrush(QColor(250, 250, 250)))
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1/1.15
        self.scale(factor, factor)