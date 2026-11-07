"""데이터 모델 (dataclass)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from shapely.geometry import Polygon

from .constants import (
    TunnelType, CornerStyle, FL_TOLERANCE,
)


@dataclass
class ArchParams:
    R1: float = 7.166
    top_angle: float = 90.0
    R2: float = 5.54
    r2_angle: float = 69.0
    R1_Y: float = 1.572
    cx: float = 0.0
    label: str = "본선"

    # ★ 신규: NATM 외곽선(라이닝) 관련
    show_lining: bool = True
    ts: float = 0.4  # 라이닝 두께 (m)
    ts_slab: float = 0.4  # 슬래브 두께 (m)

    @property
    def r1_angles(self) -> tuple[float, float]:
        half = self.top_angle / 2.0
        return (90.0 + half, 90.0 - half)


@dataclass
class TunnelParams:
    kind: TunnelType = TunnelType.NATM

    # 공통 / 시공기준
    FL: float = 0.0
    RL: float = 0.472
    fl_to_culvert: float = 0.472
    D: float = 4.4

    # ★ 안전박스(좌/우/높이) — 파라미터화
    sideL: float = 0.8        # 좌측 안전박스 폭 (m)
    sideR: float = 0.8        # 우측 안전박스 폭 (m)
    safeheight: float = 2.1   # 안전박스 높이 (m)

    # 단일 NATM
    R1: float = 7.166
    top_angle: float = 90.0
    R2: float = 5.54
    r2_angle: float = 69.0
    R1_Y: float = 1.572

    # 다중 아치
    arches: list[ArchParams] = field(default_factory=list)
    pillar_w: float = 1.0
    gap_L: float = 0.5
    gap_R: float = 0.5

    # Box
    box_width: float = 8.0
    box_height: float = 6.5
    box_wall_t: float = 0.4
    box_slab_t: float = 0.4
    box_style_top: CornerStyle = CornerStyle.CHAMFER
    box_style_bot: CornerStyle = CornerStyle.NONE
    box_fillet_top_r: float = 0.0
    box_fillet_bot_r: float = 0.0
    box_chamfer_top_dx: float = 0.6
    box_chamfer_top_dy: float = 0.6
    box_chamfer_bot_dx: float = 0.3
    box_chamfer_bot_dy: float = 0.3

    # ★ 신규: NATM 외곽선(라이닝) 관련
    show_lining: bool = True
    ts: float = 0.4  # 라이닝 두께 (m)
    ts_slab: float = 1.0  # 슬래브 두께 (m)

    # ★ 신규: Box 다중 기둥 및 코핑부
    box_columns: int = 1  # 기둥 개수 (N개)
    box_col_width: float = 0.4  # 기둥 폭 (m)
    box_coping_w: float = 0.3  # 코핑부 돌출 폭 (m)
    box_coping_h: float = 0.6  # 코핑부 높이 (m)

    # ★ 신규: 좌우 배수구 (측구)
    box_drain_w: float = 0.4  # 배수구 폭 (m)
    box_drain_h: float = 0.5  # 배수구 깊이 (m)

    # ★ 신규: 다중 트랙
    tracks: list[TrackParams] = field(default_factory=list)

    # 편의: tracks 가 비어있으면 D 기반 2트랙 자동 생성
    def get_tracks(self) -> list[TrackParams]:
        if self.tracks:
            return self.tracks
        # 기존 D 기반 (하선/상선)
        half = self.D / 2
        return [
            TrackParams(offset_x=-half, label="하선"),
            TrackParams(offset_x=+half, label="상선"),
        ]

    @property
    def r1_angles(self) -> tuple[float, float]:
        half = self.top_angle / 2.0
        return (90.0 + half, 90.0 - half)


@dataclass
class TunnelGeometry:
    a: ArchParams
    center_top: tuple[float, float]
    left_center: tuple[float, float]
    right_center: tuple[float, float]
    top_start: tuple[float, float]
    top_end: tuple[float, float]
    left_end: tuple[float, float]
    right_end: tuple[float, float]
    polygon: Polygon
    area: float
    SL: float
    A: float
    top_of_tunnel: float

    # ★ 신규: 외곽선(Lining) 기하 정보 (NATM 전용)
    lining_top_arc: Optional[tuple] = None  # (center, radius, start_deg, end_deg)
    lining_left_arc: Optional[tuple] = None
    lining_right_arc: Optional[tuple] = None
    lining_bottom_line: Optional[tuple] = None  # (start_point, end_point)

    outer_polygon: Polygon | None = None
    lining_polygon: Polygon | None = None

@dataclass
class MultiArchGeometry:
    arches: list[TunnelGeometry]
    total_area: float
    bbox: tuple[float, float, float, float]
    layout: list[ArchParams]


@dataclass
class BoxGeometry:
    p: TunnelParams
    inner: Polygon
    inner_area: float
    inner_pts: list[tuple[float, float]]
    outer: Polygon
    outer_area: float
    cx_left: float
    cx_right: float
    floor_y: float
    ceiling_y: float
    top_of_tunnel: float
    SL: float
    A: float
    fillet_arcs: list[tuple[tuple[float, float], float, float, float]]


@dataclass
class FitHistoryEntry:
    timestamp: str
    target_FL: float
    achieved_FL: float
    R1_Y: float
    dR1_Y: float
    R1: float
    top_angle: float
    R2: float
    r2_angle: float
    D: float
    success: bool

    @property
    def is_ok(self) -> bool:
        import math
        return (not math.isnan(self.achieved_FL)
                and abs(self.achieved_FL - self.target_FL) <= FL_TOLERANCE)


@dataclass
class AlignResult:
    labels: list[str]
    old_R1Y: list[float]
    new_R1Y: list[float]
    old_FL: list[float]
    new_FL: list[float]
    success: list[bool]
    target_FL: float


@dataclass
class SnapshotEntry:
    timestamp: str
    kind: str
    total_area: float
    note: str
    payload: dict


@dataclass
class OverlapInfo:
    has_overlap: bool
    pairs: list[tuple[int, int]]
    overlap_areas: list[float]
    min_gap: float
    gap_details: list[tuple[int, int, float]]

@dataclass
class TrackParams:
    """개별 선로 (X 위치, 라벨)."""
    offset_x: float = 0.0        # 터널 중심(0,0) 기준 X 오프셋 (m)
    label: str = ""              # 표시용 이름 (예: "하선", "상선", "3선")

    # ★ 신규: 차량한계선개별제어
    show_clearance: bool = True  # 차량한계 표시 여부