# model.py
"""JSON 스키마와 1:1 대응하는 경량 모델. dataclass로 단순하게."""

from dataclasses import dataclass, field, asdict
from typing import Optional
import json


@dataclass
class Station:
    id: str
    name: str
    type: str
    mileage_start: float
    mileage_end: float
    platforms: list = field(default_factory=list)


@dataclass
class Track:
    id: str
    name: str
    type: str
    gauge: int
    direction: str
    design_speed: int
    min_curve_radius: int


@dataclass
class Node:
    id: str
    type: str
    mileage: float
    track_id: str
    lateral_offset: float = 0.0
    attrs: dict = field(default_factory=dict)


@dataclass
class Edge:
    id: str
    from_id: str
    to_id: str
    track_id: str
    geometry: dict = field(default_factory=dict)


@dataclass
class StationData:
    version: str
    station: Station
    tracks: list
    nodes: list
    edges: list
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, path):
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        return cls(
            version=raw["version"],
            station=Station(**raw["station"]),
            tracks=[Track(**t) for t in raw["tracks"]],
            nodes=[Node(id=n["id"], type=n["type"], mileage=n["mileage"],
                        track_id=n["track_id"],
                        lateral_offset=n.get("lateral_offset", 0.0),
                        attrs=n.get("attrs", {}))
                   for n in raw["nodes"]],
            edges=[Edge(id=e["id"], from_id=e["from"], to_id=e["to"],
                        track_id=e["track_id"],
                        geometry=e.get("geometry", {}))
                   for e in raw["edges"]],
            metadata=raw.get("metadata", {}),
        )

    def to_json(self, path):
        raw = {
            "version": self.version,
            "station": asdict(self.station),
            "tracks": [asdict(t) for t in self.tracks],
            "nodes": [
                {"id": n.id, "type": n.type, "mileage": n.mileage,
                 "track_id": n.track_id, "lateral_offset": n.lateral_offset,
                 "attrs": n.attrs}
                for n in self.nodes
            ],
            "edges": [
                {"id": e.id, "from": e.from_id, "to": e.to_id,
                 "track_id": e.track_id, "geometry": e.geometry}
                for e in self.edges
            ],
            "metadata": self.metadata,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=2)

    # 편의 조회
    def tracks_by_id(self):
        return {t.id: asdict(t) for t in self.tracks}

    def nodes_by_id(self):
        return {n.id: n for n in self.nodes}