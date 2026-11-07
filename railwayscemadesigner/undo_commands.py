# undo_commands.py
"""QUndoCommand 서브클래스.
모든 커맨드는 StationData(data)와 on_changed 콜백만 참조한다.
scene은 참조하지 않는다 (scene은 재구축 때마다 교체되기 때문).
"""

from PyQt6.QtGui import QUndoCommand


class _ModelCommand(QUndoCommand):
    def __init__(self, data, on_changed, text: str):
        super().__init__(text)
        self.data = data
        self.on_changed = on_changed

    def _refresh(self):
        if self.on_changed is not None:
            self.on_changed()


class AddNodeCommand(_ModelCommand):
    def __init__(self, data, on_changed, node):
        super().__init__(data, on_changed, f"노드 추가 {node.id}")
        self.node = node

    def redo(self):
        self.data.nodes.append(self.node)
        self._refresh()

    def undo(self):
        self.data.nodes = [n for n in self.data.nodes if n.id != self.node.id]
        self._refresh()


class DeleteNodesCommand(_ModelCommand):
    def __init__(self, data, on_changed, node_ids):
        super().__init__(data, on_changed, f"노드 삭제 ({len(node_ids)}개)")
        self.node_ids = set(node_ids)
        self._removed_nodes = []
        self._removed_edges = []

    def redo(self):
        self._removed_nodes = [n for n in self.data.nodes if n.id in self.node_ids]
        self._removed_edges = [
            e for e in self.data.edges
            if e.from_id in self.node_ids or e.to_id in self.node_ids
        ]
        self.data.nodes = [n for n in self.data.nodes if n.id not in self.node_ids]
        self.data.edges = [
            e for e in self.data.edges
            if e.from_id not in self.node_ids and e.to_id not in self.node_ids
        ]
        self._refresh()

    def undo(self):
        self.data.nodes.extend(self._removed_nodes)
        self.data.edges.extend(self._removed_edges)
        self._refresh()


class AddEdgeCommand(_ModelCommand):
    def __init__(self, data, on_changed, edge):
        super().__init__(data, on_changed, f"엣지 추가 {edge.id}")
        self.edge = edge

    def redo(self):
        self.data.edges.append(self.edge)
        self._refresh()

    def undo(self):
        self.data.edges = [e for e in self.data.edges if e.id != self.edge.id]
        self._refresh()


class MoveNodeCommand(_ModelCommand):
    def __init__(self, data, on_changed, node_id,
                 old_mileage, old_lateral, new_mileage, new_lateral):
        super().__init__(data, on_changed, f"노드 이동 {node_id}")
        self.node_id = node_id
        self.old = (old_mileage, old_lateral)
        self.new = (new_mileage, new_lateral)

    def _apply(self, mileage, lateral):
        for n in self.data.nodes:
            if n.id == self.node_id:
                n.mileage = mileage
                n.lateral_offset = lateral
                break
        self._refresh()

    def redo(self):
        self._apply(*self.new)

    def undo(self):
        self._apply(*self.old)


class EditNodeCommand(_ModelCommand):
    def __init__(self, data, on_changed, node_id, old_attrs: dict, new_attrs: dict):
        super().__init__(data, on_changed, f"노드 편집 {node_id}")
        self.node_id = node_id
        self.old = old_attrs
        self.new = new_attrs

    def _apply(self, attrs: dict):
        for n in self.data.nodes:
            if n.id == self.node_id:
                for k, v in attrs.items():
                    setattr(n, k, v)
                break
        self._refresh()

    def redo(self):
        self._apply(self.new)

    def undo(self):
        self._apply(self.old)