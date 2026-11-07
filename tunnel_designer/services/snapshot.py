"""제원 스냅샷 (JSON)."""
from __future__ import annotations
import json
from dataclasses import asdict
from datetime import datetime

from core.constants import TunnelType, CornerStyle
from core.models import TunnelParams, SnapshotEntry, ArchParams, TrackParams


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

    # services/snapshot.py의 deserialize 수정

    @staticmethod
    def deserialize(payload: dict) -> TunnelParams:
        data = dict(payload)
        data["kind"] = TunnelType(data["kind"])
        if "box_style_top" in data and isinstance(data["box_style_top"], str):
            data["box_style_top"] = CornerStyle(data["box_style_top"])
        if "box_style_bot" in data and isinstance(data["box_style_bot"], str):
            data["box_style_bot"] = CornerStyle(data["box_style_bot"])

        # ★ D 필드 제거 (구버전 호환)
        legacy_D = data.pop("D", None)

        # 트랙 복원
        tracks_raw = data.get("tracks") or []
        tracks = []
        for t in tracks_raw:
            tracks.append(TrackParams(
                offset_x=t.get("offset_x", 0.0),
                label=t.get("label", ""),
                show_clearance=t.get("show_clearance", True)
            ))

        # ★ tracks가 비어있고 D가 있으면 D 기반 2트랙 생성
        if not tracks and legacy_D is not None:
            half = float(legacy_D) / 2
            tracks = [
                TrackParams(offset_x=-half, label="하선"),
                TrackParams(offset_x=+half, label="상선"),
            ]

        data["tracks"] = tracks

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