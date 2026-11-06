"""상수 및 열거형."""
from __future__ import annotations
from enum import Enum


# ── UI 상수 ────────────────────────────────────────
LEFT_PANEL_WIDTH = 500   # 좌측 컨트롤 패널 폭 (px)


# ── 수치 상수 ────────────────────────────────────────
FL_TOLERANCE = 0.02
ARC_SAMPLES = 1000
POLYGON_ARC_POINTS = 100
LABEL_Y_MARGIN = 0.5
DXF_DEFAULT_IN = "c:/temp/건축한계.dxf"

MIN_PILLAR_W = 0.3
OVERLAP_LAYER = "OVERLAP"
HATCH_STYLE_SOLID = "solid"
HATCH_STYLE_PATTERN = "ANSI31"
HATCH_STYLE_BOTH = "both"


# ── 열거형 ───────────────────────────────────────────
class TunnelType(str, Enum):
    NATM = "NATM (아치형)"
    NATM_2ARCH = "2-Arch (분기부)"
    NATM_3ARCH = "3-Arch (정거장)"
    BOX = "개착 Box형"


class CornerStyle(str, Enum):
    NONE = "없음"
    FILLET = "필렛 (R)"
    CHAMFER = "사선 (/)"