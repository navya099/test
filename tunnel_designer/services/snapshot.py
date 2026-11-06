"""제원 스냅샷 (JSON)."""
from __future__ import annotations
import json
from dataclasses import asdict
from datetime import datetime

from core.constants import TunnelType, CornerStyle
from core.models import TunnelParams, SnapshotEntry, ArchParams


class SnapshotStore:
    def __init__(self, max_size: int = 200):
        self.entries: list[SnapshotEntry] = []
        self.max_size = max_size

    def add(self, p: TunnelParams, total_area: float,
            note: str = "") -> SnapshotEntry:
        e = SnapshotEntry(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            kind=p.kind.value, total_area=total_area, note=note,
            payload=self._serialize(p),
        )
        self.entries.append(e)
        if len(self.entries) > self.max_size:
            self.entries.pop(0)
        return e

    @staticmethod
    def _serialize(p: TunnelParams) -> dict:
        d = asdict(p)
        d["kind"] = p.kind.value
        d["box_style_top"] = p.box_style_top.value
        d["box_style_bot"] = p.box_style_bot.value
        return d

    @staticmethod
    def deserialize(payload: dict) -> TunnelParams:
        data = dict(payload)
        data["kind"] = TunnelType(data["kind"])
        if "box_style_top" in data and isinstance(data["box_style_top"], str):
            data["box_style_top"] = CornerStyle(data["box_style_top"])
        if "box_style_bot" in data and isinstance(data["box_style_bot"], str):
            data["box_style_bot"] = CornerStyle(data["box_style_bot"])
        arches = data.get("arches") or []
        data["arches"] = [ArchParams(**a) for a in arches]
        return TunnelParams(**data)

    def to_json(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([asdict(e) for e in self.entries], f,
                      ensure_ascii=False, indent=2)

    def from_json(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self.entries = [SnapshotEntry(**r) for r in raw]