"""
터널 단면 작도기 (Tunnel Section Designer) — 완전 통합본 v6
=============================================================
- NATM 단일 / 2-Arch (분기부) / 3-Arch (정거장) / 개착 Box형
- Box 모서리: 없음 / 필렛(R) / 사선 헌치(/) 선택
- NATM FL 자동 맞춤 (brentq)
- 다중 아치 FL 통일 (기준 선택 + 미리보기)
- FL 자동 맞춤 이력 (CSV, 더블클릭 복원)
- 제원 스냅샷 (JSON, 더블클릭 복원)
- 아치 겹침 검사 (실시간 경고 + 도면 강조 + 저장 방어 + 자동 방지)
- DXF HATCH 겹침 내보내기 (단색 / ANSI31 / 둘 다)

요구사항:
    pip install matplotlib numpy scipy shapely ezdxf
"""
from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, asdict, field, replace
from datetime import datetime
from enum import Enum
from typing import Optional

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, Rectangle as MplRect
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import ezdxf
from shapely.geometry import LineString, Polygon
from scipy.optimize import brentq, minimize_scalar

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


# =============================================================================
# 상수
# =============================================================================
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


# =============================================================================
# 열거형
# =============================================================================
class TunnelType(str, Enum):
    NATM = "NATM (아치형)"
    NATM_2ARCH = "2-Arch (분기부)"
    NATM_3ARCH = "3-Arch (정거장)"
    BOX = "개착 Box형"


class CornerStyle(str, Enum):
    NONE = "없음"
    FILLET = "필렛 (R)"
    CHAMFER = "사선 (/)"


# =============================================================================
# 데이터 모델
# =============================================================================
@dataclass
class ArchParams:
    R1: float = 7.166
    top_angle: float = 90.0
    R2: float = 5.54
    r2_angle: float = 69.0
    R1_Y: float = 1.572
    cx: float = 0.0
    label: str = "본선"

    @property
    def r1_angles(self) -> tuple[float, float]:
        half = self.top_angle / 2.0
        return (90.0 + half, 90.0 - half)


@dataclass
class TunnelParams:
    kind: TunnelType = TunnelType.NATM

    FL: float = 0.0
    RL: float = 0.472
    fl_to_culvert: float = 0.472
    sideL: float = 0.8
    sideR: float = 0.8
    safeheight: float = 2.1
    D: float = 4.4

    R1: float = 7.166
    top_angle: float = 90.0
    R2: float = 5.54
    r2_angle: float = 69.0
    R1_Y: float = 1.572

    arches: list[ArchParams] = field(default_factory=list)
    pillar_w: float = 1.0
    gap_L: float = 0.5
    gap_R: float = 0.5

    # Box
    box_width: float = 8.0
    box_height: float = 6.5
    box_wall_t: float = 0.4
    box_slab_t: float = 0.4

    box_style_top: CornerStyle = CornerStyle.FILLET
    box_style_bot: CornerStyle = CornerStyle.NONE

    box_fillet_top_r: float = 0.0
    box_fillet_bot_r: float = 0.0

    box_chamfer_top_dx: float = 0.4
    box_chamfer_top_dy: float = 0.4
    box_chamfer_bot_dx: float = 0.0
    box_chamfer_bot_dy: float = 0.0

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


# =============================================================================
# 기하 유틸
# =============================================================================
def _polar(center, radius, deg):
    rad = math.radians(deg)
    return (center[0] + radius * math.cos(rad),
            center[1] + radius * math.sin(rad))


def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    return dx / n, dy / n


def find_side_center(top_center, top_radius, ang_left, ang_right, side_radius):
    left_pt = _polar(top_center, top_radius, ang_left)
    right_pt = _polar(top_center, top_radius, ang_right)
    dx_l, dy_l = _unit(top_center, left_pt)
    dx_r, dy_r = _unit(top_center, right_pt)
    return ((left_pt[0] - dx_l * side_radius, left_pt[1] - dy_l * side_radius),
            (right_pt[0] - dx_r * side_radius, right_pt[1] - dy_r * side_radius))


def find_end_point(center, radius, start_point, angle_deg):
    sa = math.degrees(math.atan2(start_point[1] - center[1], start_point[0] - center[0]))
    return _polar(center, radius, sa + angle_deg)


def find_start_point(center, radius, end_point, angle_deg):
    ea = math.degrees(math.atan2(end_point[1] - center[1], end_point[0] - center[0]))
    return _polar(center, radius, ea - angle_deg)


def arc_to_linestring(center, radius, start_deg, end_deg,
                      num_points=POLYGON_ARC_POINTS):
    angs = np.linspace(math.radians(start_deg), math.radians(end_deg), num_points)
    return LineString([(center[0] + radius * math.cos(a),
                        center[1] + radius * math.sin(a)) for a in angs])


def find_extreme_x_on_arc(center, radius, start_deg, end_deg):
    if end_deg < start_deg:
        end_deg += 360.0
    angs = np.radians(np.linspace(start_deg, end_deg, ARC_SAMPLES))
    xs = center[0] + radius * np.cos(angs)
    ys = center[1] + radius * np.sin(angs)
    return (xs.max(), ys[xs.argmax()]), (xs.min(), ys[xs.argmin()])


# =============================================================================
# 단일 아치
# =============================================================================
def compute_geometry_from_arch(a: ArchParams, FL: float = 0.0) -> TunnelGeometry:
    center_top = (a.cx, a.R1_Y)
    a_left, a_right = a.r1_angles

    left_center, right_center = find_side_center(
        center_top, a.R1, a_left, a_right, a.R2)

    top_start = _polar(center_top, a.R1, a_left)
    top_end = _polar(center_top, a.R1, a_right)
    left_end = find_end_point(left_center, a.R2, top_start, a.r2_angle)
    right_end = find_end_point(right_center, a.R2, top_end, -a.r2_angle)

    left_arc = arc_to_linestring(left_center, a.R2, a_left, a_left + a.r2_angle)
    top_arc = arc_to_linestring(center_top, a.R1, a_left, a_right)
    right_arc = arc_to_linestring(right_center, a.R2, a_right, a_right - a.r2_angle)
    bottom = LineString([left_arc.coords[-1], right_arc.coords[-1]])

    coords = (list(left_arc.coords[::-1]) + list(top_arc.coords)
              + list(right_arc.coords) + list(bottom.coords[::-1]))
    polygon = Polygon(coords)

    _, sl_pt = find_extreme_x_on_arc(left_center, a.R2, a_left, a_left + a.r2_angle)

    return TunnelGeometry(
        a=a, center_top=center_top,
        left_center=left_center, right_center=right_center,
        top_start=top_start, top_end=top_end,
        left_end=left_end, right_end=right_end,
        polygon=polygon, area=polygon.area,
        SL=sl_pt[1], A=abs(left_end[0] - a.cx),
        top_of_tunnel=a.R1_Y + a.R1 - FL,
    )


def compute_fl_for_arch(a: ArchParams) -> float:
    a_left, a_right = a.r1_angles
    center_top = (a.cx, a.R1_Y)
    left_center, _ = find_side_center(center_top, a.R1, a_left, a_right, a.R2)
    top_start = _polar(center_top, a.R1, a_left)
    left_end = find_end_point(left_center, a.R2, top_start, a.r2_angle)
    return left_end[1]


def compute_fl(p: TunnelParams, R1_Y: float) -> float:
    a = ArchParams(R1=p.R1, top_angle=p.top_angle, R2=p.R2,
                   r2_angle=p.r2_angle, R1_Y=R1_Y, cx=0.0)
    return compute_fl_for_arch(a) - p.fl_to_culvert


def fit_R1_Y_to_FL(p: TunnelParams,
                   tol: float = 1e-4,
                   bounds: tuple[float, float] = (-20.0, 20.0)
                   ) -> tuple[float, bool]:
    target = p.FL

    def f(y):
        return compute_fl(p, y) - target

    lo, hi = bounds
    if f(lo) > 0 or f(hi) < 0:
        return p.R1_Y, False
    try:
        return float(brentq(f, lo, hi, xtol=tol, maxiter=100)), True
    except (ValueError, RuntimeError):
        res = minimize_scalar(lambda y: abs(f(y)), bounds=(lo, hi), method='bounded')
        return float(res.x), bool(res.success)


# =============================================================================
# 다중 아치
# =============================================================================
def arch_half_width(a: ArchParams) -> float:
    g = compute_geometry_from_arch(a)
    return max(abs(g.left_end[0] - a.cx), abs(g.right_end[0] - a.cx))


def layout_2arch(arches, pillar_w):
    assert len(arches) == 2
    hw = arch_half_width(arches[0])
    offset = hw + pillar_w / 2
    return [
        replace(arches[0], cx=-offset, label="좌선"),
        replace(arches[1], cx=+offset, label="우선"),
    ]


def layout_3arch(central, left, right, gap_L, gap_R):
    hw_c = arch_half_width(central)
    hw_l = arch_half_width(left)
    hw_r = arch_half_width(right)
    left_cx = -(hw_c + gap_L + hw_l)
    right_cx = +(hw_c + gap_R + hw_r)
    return [
        replace(central, cx=0.0, label="중앙"),
        replace(left, cx=left_cx, label="좌선"),
        replace(right, cx=right_cx, label="우선"),
    ]


def compute_multi_arch(p: TunnelParams) -> MultiArchGeometry:
    if p.kind == TunnelType.NATM_2ARCH:
        layout = layout_2arch(p.arches, p.pillar_w)
    elif p.kind == TunnelType.NATM_3ARCH:
        assert len(p.arches) == 3
        layout = layout_3arch(p.arches[0], p.arches[1], p.arches[2],
                              p.gap_L, p.gap_R)
    else:
        raise ValueError("NATM_2ARCH 또는 NATM_3ARCH만 지원")

    geoms = [compute_geometry_from_arch(a, FL=p.FL) for a in layout]
    total = sum(g.area for g in geoms)
    xs, ys = [], []
    for g in geoms:
        minx, miny, maxx, maxy = g.polygon.bounds
        xs.extend([minx, maxx])
        ys.extend([miny, maxy])
    bbox = (min(xs), min(ys), max(xs), max(ys))
    return MultiArchGeometry(arches=geoms, total_area=total,
                             bbox=bbox, layout=layout)


def check_multi_arch_overlap(mg: MultiArchGeometry,
                              tol: float = 0.0) -> OverlapInfo:
    geoms = [g.polygon for g in mg.arches]
    n = len(geoms)
    pairs, areas = [], []
    for i in range(n):
        for j in range(i + 1, n):
            inter = geoms[i].intersection(geoms[j])
            if inter.area > tol:
                pairs.append((i, j))
                areas.append(inter.area)

    order = sorted(range(n), key=lambda k: mg.arches[k].a.cx)
    gaps = []
    for a, b in zip(order, order[1:]):
        gi, gj = mg.arches[a], mg.arches[b]
        gap = min(gj.polygon.bounds[0] - gi.polygon.bounds[2],
                  gj.left_end[0] - gi.right_end[0])
        gaps.append((a, b, gap))

    return OverlapInfo(
        has_overlap=bool(pairs),
        pairs=pairs, overlap_areas=areas,
        min_gap=min((g for _, _, g in gaps), default=float('inf')),
        gap_details=gaps,
    )


def fit_arch_R1_Y_to_FL(a: ArchParams, target_floor_y: float,
                        fl_to_culvert: float,
                        tol: float = 1e-4,
                        bounds: tuple[float, float] = (-20.0, 30.0)
                        ) -> tuple[float, bool]:
    target_left_end_y = target_floor_y + fl_to_culvert

    def f(R1_Y):
        return compute_fl_for_arch(replace(a, R1_Y=R1_Y)) - target_left_end_y

    lo, hi = bounds
    if f(lo) > 0 or f(hi) < 0:
        return a.R1_Y, False
    try:
        return float(brentq(f, lo, hi, xtol=tol, maxiter=100)), True
    except (ValueError, RuntimeError):
        res = minimize_scalar(lambda y: abs(f(y)),
                              bounds=(lo, hi), method='bounded')
        return float(res.x), bool(res.success)


def align_multi_arch_fl(p: TunnelParams,
                        reference_idx: int = 0) -> AlignResult:
    ref = p.arches[reference_idx]
    target_FL = compute_fl_for_arch(ref) - p.fl_to_culvert

    labels, old_R1Y, new_R1Y, old_FL, new_FL, success = [], [], [], [], [], []
    for a in p.arches:
        labels.append(a.label)
        old_R1Y.append(a.R1_Y)
        old_FL.append(compute_fl_for_arch(a) - p.fl_to_culvert)
        new_y, ok = fit_arch_R1_Y_to_FL(a, target_FL, p.fl_to_culvert)
        new_R1Y.append(new_y)
        success.append(ok)
        new_FL.append(compute_fl_for_arch(replace(a, R1_Y=new_y)) - p.fl_to_culvert)

    return AlignResult(labels=labels, old_R1Y=old_R1Y, new_R1Y=new_R1Y,
                       old_FL=old_FL, new_FL=new_FL,
                       success=success, target_FL=target_FL)


# =============================================================================
# Box (필렛 / 사선 / 없음)
# =============================================================================
def _clamp_box_corners(p: TunnelParams) -> TunnelParams:
    B, H = p.box_width, p.box_height
    max_r = max(0.0, min(B, H) / 2 - 0.05)
    r_top = min(p.box_fillet_top_r, max_r)
    r_bot = min(p.box_fillet_bot_r, max_r)

    max_dx = max(0.0, B / 2 - 0.05)
    max_dy = max(0.0, H / 2 - 0.05)
    cht_dx = min(p.box_chamfer_top_dx, max_dx)
    cht_dy = min(p.box_chamfer_top_dy, max_dy)
    chb_dx = min(p.box_chamfer_bot_dx, max_dx)
    chb_dy = min(p.box_chamfer_bot_dy, max_dy)

    return replace(
        p,
        box_fillet_top_r=r_top, box_fillet_bot_r=r_bot,
        box_chamfer_top_dx=cht_dx, box_chamfer_top_dy=cht_dy,
        box_chamfer_bot_dx=chb_dx, box_chamfer_bot_dy=chb_dy,
    )


def _fillet_corner(corner, prev, nxt, r, num_pts=20):
    if r <= 0:
        return [corner], corner, corner
    up = _unit(corner, prev)
    un = _unit(corner, nxt)
    dot = max(-1.0, min(1.0, up[0] * un[0] + up[1] * un[1]))
    theta = math.acos(dot)
    if theta <= 1e-6 or abs(theta - math.pi) < 1e-6:
        return [corner], corner, corner
    t = r / math.tan(theta / 2)
    d = r / math.sin(theta / 2)
    p1 = (corner[0] + up[0] * t, corner[1] + up[1] * t)
    p2 = (corner[0] + un[0] * t, corner[1] + un[1] * t)
    bx, by = up[0] + un[0], up[1] + un[1]
    bn = math.hypot(bx, by)
    bx, by = bx / bn, by / bn
    center = (corner[0] + bx * d, corner[1] + by * d)
    a1 = math.atan2(p1[1] - center[1], p1[0] - center[0])
    a2 = math.atan2(p2[1] - center[1], p2[0] - center[0])
    da = a2 - a1
    while da > math.pi:
        da -= 2 * math.pi
    while da < -math.pi:
        da += 2 * math.pi
    angles = [a1 + da * i / (num_pts - 1) for i in range(num_pts)]
    return ([(center[0] + r * math.cos(a), center[1] + r * math.sin(a))
             for a in angles], p1, p2)


def _chamfer_corner_signed(corner,
                           sx_x: int, sx_y: int,
                           sy_x: int, sy_y: int,
                           dx: float, dy: float):
    """
    corner에서 'x축 방향으로 dx, y축 방향으로 dy' 만큼 절단.
    - (sx_x, sx_y) : 첫 번째 절단점의 부호 (예: 우측이면 (1, 0), 하단이면 (0, -1))
    - (sy_x, sy_y) : 두 번째 절단점의 부호
    - dx, dy       : 각 축 방향 절단 거리 (항상 양수)

    반환: (p1, p2) — 코너를 대체할 두 점
    """
    if dx <= 0 or dy <= 0:
        return None

    cx, cy = corner

    # 첫 번째 절단점: (sx_x, sx_y) 방향으로
    if sx_x != 0:
        p1 = (cx + sx_x * dx, cy)
    else:
        p1 = (cx, cy + sx_y * dy)

    # 두 번째 절단점: (sy_x, sy_y) 방향으로
    if sy_x != 0:
        p2 = (cx + sy_x * dx, cy)
    else:
        p2 = (cx, cy + sy_y * dy)

    return p1, p2


def _box_inner_polygon(p: TunnelParams) -> list[tuple[float, float]]:
    B, H = p.box_width, p.box_height
    x_L, x_R = -B / 2, B / 2
    y_B, y_T = p.FL, p.FL + H

    pts: list[tuple[float, float]] = []

    # ==========================================
    # 1. LB (좌하단) : 위에서 내려와서 오른쪽으로 나감
    # ==========================================
    if p.box_style_bot == CornerStyle.CHAMFER:
        dx, dy = p.box_chamfer_bot_dx, p.box_chamfer_bot_dy
        if dx > 0 and dy > 0:
            pts.extend([(x_L, y_B + dy), (x_L + dx, y_B)])  # ⬆️ -> ➡️
        else:
            pts.append((x_L, y_B))
    elif p.box_style_bot == CornerStyle.FILLET:
        arc_pts, _, _ = _fillet_corner(
            (x_L, y_B), (x_R, y_B), (x_L, y_T), p.box_fillet_bot_r)
        pts.extend(arc_pts)
    else:
        pts.append((x_L, y_B))

    # ==========================================
    # 2. RB (우하단) : 왼쪽에서 들어와서 위로 올라감
    # ==========================================
    if p.box_style_bot == CornerStyle.CHAMFER:
        dx, dy = p.box_chamfer_bot_dx, p.box_chamfer_bot_dy
        if dx > 0 and dy > 0:
            pts.extend([(x_R - dx, y_B), (x_R, y_B + dy)])  # ⬅️ -> ⬆️
        else:
            pts.append((x_R, y_B))
    elif p.box_style_bot == CornerStyle.FILLET:
        arc_pts, _, _ = _fillet_corner(
            (x_R, y_B), (x_L, y_B), (x_R, y_T), p.box_fillet_bot_r)
        pts.extend(arc_pts)
    else:
        pts.append((x_R, y_B))

    # ==========================================
    # 3. RT (우상단) : 아래에서 올라와서 왼쪽으로 나감
    # ==========================================
    if p.box_style_top == CornerStyle.CHAMFER:
        dx, dy = p.box_chamfer_top_dx, p.box_chamfer_top_dy
        if dx > 0 and dy > 0:
            pts.extend([(x_R, y_T - dy), (x_R - dx, y_T)])  # ⬇️ -> ⬅️
        else:
            pts.append((x_R, y_T))
    elif p.box_style_top == CornerStyle.FILLET:
        arc_pts, _, _ = _fillet_corner(
            (x_R, y_T), (x_R, y_B), (x_L, y_T), p.box_fillet_top_r)
        pts.extend(arc_pts)
    else:
        pts.append((x_R, y_T))

    # ==========================================
    # 4. LT (좌상단) : 오른쪽에서 들어와서 아래로 내려감
    # ==========================================
    if p.box_style_top == CornerStyle.CHAMFER:
        dx, dy = p.box_chamfer_top_dx, p.box_chamfer_top_dy
        if dx > 0 and dy > 0:
            pts.extend([(x_L + dx, y_T), (x_L, y_T - dy)])  # ➡️ -> ⬇️
        else:
            pts.append((x_L, y_T))
    elif p.box_style_top == CornerStyle.FILLET:
        arc_pts, _, _ = _fillet_corner(
            (x_L, y_T), (x_L, y_B), (x_R, y_T), p.box_fillet_top_r)
        pts.extend(arc_arcs if 'arc_arcs' in locals() else arc_pts)
    else:
        pts.append((x_L, y_T))

    # 폴리곤 닫기
    pts.append(pts[0])
    return pts


def compute_box_geometry(p: TunnelParams) -> BoxGeometry:
    p = _clamp_box_corners(p)
    B, H = p.box_width, p.box_height
    tw, ts = p.box_wall_t, p.box_slab_t
    x_L, x_R = -B / 2, B / 2
    y_B, y_T = p.FL, p.FL + H

    inner_pts = _box_inner_polygon(p)
    inner = Polygon(inner_pts)

    x_OL, x_OR = x_L - tw, x_R + tw
    y_OB, y_OT = y_B - ts, y_T + ts
    outer = Polygon([(x_OL, y_OB), (x_OR, y_OB), (x_OR, y_OT), (x_OL, y_OT)])

    fillet_arcs = []
    corners = [
        ((x_L, y_B), (x_R, y_B), (x_L, y_T),
         p.box_style_bot, p.box_fillet_bot_r),
        ((x_R, y_B), (x_L, y_B), (x_R, y_T),
         p.box_style_bot, p.box_fillet_bot_r),
        ((x_R, y_T), (x_R, y_B), (x_L, y_T),
         p.box_style_top, p.box_fillet_top_r),
        ((x_L, y_T), (x_L, y_B), (x_R, y_T),
         p.box_style_top, p.box_fillet_top_r),
    ]
    for corner, prev, nxt, style, r in corners:
        if style != CornerStyle.FILLET or r <= 0:
            continue
        _, p1, p2 = _fillet_corner(corner, prev, nxt, r)
        up = _unit(corner, prev)
        un = _unit(corner, nxt)
        dot = max(-1, min(1, up[0] * un[0] + up[1] * un[1]))
        theta = math.acos(dot)
        d = r / math.sin(theta / 2)
        bx, by = up[0] + un[0], up[1] + un[1]
        bn = math.hypot(bx, by)
        center = (corner[0] + bx / bn * d, corner[1] + by / bn * d)
        a1 = math.degrees(math.atan2(p1[1] - center[1], p1[0] - center[0]))
        a2 = math.degrees(math.atan2(p2[1] - center[1], p2[0] - center[0]))
        fillet_arcs.append((center, r, a1, a2))

    return BoxGeometry(
        p=p, inner=inner, inner_area=inner.area, inner_pts=inner_pts,
        outer=outer, outer_area=outer.area,
        cx_left=x_L, cx_right=x_R,
        floor_y=y_B, ceiling_y=y_T,
        top_of_tunnel=y_OT,
        SL=y_B + p.safeheight, A=B / 2,
        fillet_arcs=fillet_arcs,
    )


# =============================================================================
# DXF HATCH
# =============================================================================
def add_hatch_for_polygon(msp, poly: Polygon, *,
                          color: int = 1,
                          solid: bool = True,
                          pattern: str = HATCH_STYLE_PATTERN,
                          scale: float = 0.3,
                          alpha: int = 70,
                          layer: str = OVERLAP_LAYER):
    if poly.is_empty:
        return
    if poly.geom_type != "Polygon":
        for g in getattr(poly, "geoms", []):
            add_hatch_for_polygon(msp, g, color=color, solid=solid,
                                  pattern=pattern, scale=scale,
                                  alpha=alpha, layer=layer)
        return

    hatch = msp.add_hatch(color=color, dxfattribs={"layer": layer})
    if solid:
        hatch.set_solid_fill(color=color)
    else:
        try:
            hatch.set_pattern_fill(pattern, color=color, scale=scale)
        except Exception:
            hatch.set_solid_fill(color=color)

    ext = [(x, y) for x, y in poly.exterior.coords]
    if ext and ext[0] != ext[-1]:
        ext.append(ext[0])
    if ext:
        hatch.paths.add_polyline_path(ext, is_closed=True)

    for interior in poly.interiors:
        hole = [(x, y) for x, y in interior.coords]
        if hole and hole[0] != hole[-1]:
            hole.append(hole[0])
        if hole:
            hatch.paths.add_polyline_path(hole, is_closed=True)

    try:
        hatch.transparency = alpha / 100.0
    except AttributeError:
        pass


# =============================================================================
# 이력 / 스냅샷 / DXF 캐시
# =============================================================================
class FitHistory:
    def __init__(self, max_size: int = 100):
        self.entries: list[FitHistoryEntry] = []
        self.max_size = max_size

    def add(self, p, R1_Y_prev, achieved_FL, success):
        e = FitHistoryEntry(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            target_FL=p.FL, achieved_FL=achieved_FL,
            R1_Y=p.R1_Y, dR1_Y=p.R1_Y - R1_Y_prev,
            R1=p.R1, top_angle=p.top_angle,
            R2=p.R2, r2_angle=p.r2_angle, D=p.D,
            success=success,
        )
        self.entries.append(e)
        if len(self.entries) > self.max_size:
            self.entries.pop(0)
        return e

    def to_csv(self, path):
        if not self.entries:
            raise ValueError("저장할 이력이 없습니다.")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(asdict(self.entries[0]).keys()))
            w.writeheader()
            for e in self.entries:
                w.writerow(asdict(e))


class SnapshotStore:
    def __init__(self, max_size: int = 200):
        self.entries: list[SnapshotEntry] = []
        self.max_size = max_size

    def add(self, p, total_area, note=""):
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

    def to_json(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([asdict(e) for e in self.entries], f,
                      ensure_ascii=False, indent=2)

    def from_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self.entries = [SnapshotEntry(**r) for r in raw]


class DxfCache:
    def __init__(self):
        self.path: Optional[str] = None
        self.entities: Optional[list] = None

    def load(self, path: str, force: bool = False):
        if not force and path == self.path and self.entities is not None:
            return self.entities
        try:
            doc = ezdxf.readfile(path)
        except (FileNotFoundError, IOError) as e:
            messagebox.showwarning("DXF 로드 실패", f"{path}\n{e}")
            self.path, self.entities = None, None
            return None
        self.path = path
        self.entities = list(doc.modelspace())
        return self.entities


# =============================================================================
# 스타일
# =============================================================================
def setup_style(root: tk.Tk):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        style.theme_use("default")
    base = ("Malgun Gothic", 10)
    bold = ("Malgun Gothic", 10, "bold")
    title = ("Malgun Gothic", 12, "bold")
    root.option_add("*Font", base)
    style.configure("TFrame", background="#f5f6f8")
    style.configure("Card.TFrame", background="#ffffff")
    style.configure("TLabel", background="#f5f6f8", font=base)
    style.configure("Card.TLabel", background="#ffffff", font=base)
    style.configure("Unit.TLabel", background="#ffffff",
                    foreground="#888888", font=("Malgun Gothic", 9))
    style.configure("Title.TLabel", background="#f5f6f8", font=title,
                    foreground="#1a1a1a")
    style.configure("Info.TLabel", background="#f5f6f8",
                    foreground="#555555", font=("Malgun Gothic", 9))
    style.configure("Spec.TLabel", background="#eaf1ff", font=bold,
                    foreground="#1a3a70", padding=6)
    style.configure("TLabelframe", background="#f5f6f8",
                    bordercolor="#d0d4da", relief="solid")
    style.configure("TLabelframe.Label", background="#f5f6f8",
                    font=bold, foreground="#333333")
    style.configure("TScale", background="#ffffff", troughcolor="#e0e4ea")
    style.configure("TEntry", fieldbackground="#ffffff", padding=4)
    style.configure("TButton", padding=(10, 6), font=base)
    style.configure("Accent.TButton", font=bold, foreground="white",
                    background="#2f6fed")
    style.map("Accent.TButton",
              background=[("active", "#1e5ad6"), ("disabled", "#a9bce8")])
    style.configure("Link.TButton", font=bold, foreground="white",
                    background="#2b8a3e")
    style.map("Link.TButton",
              background=[("active", "#226c31"), ("disabled", "#a9d0b3")])
    style.configure("Danger.TButton", foreground="#b00020")
    style.configure("Treeview", rowheight=26, font=base)
    style.configure("Treeview.Heading", font=bold)
    style.configure("TNotebook", background="#f5f6f8", borderwidth=0)
    style.configure("TNotebook.Tab", padding=(14, 8), font=base)
    style.map("TNotebook.Tab",
              background=[("selected", "#ffffff"), ("!selected", "#e6e9ee")])
    style.configure("TCheckbutton", background="#f5f6f8", font=base)


# =============================================================================
# 파라미터 위젯
# =============================================================================
class ParamRow:
    def __init__(self, parent, *, label, attr, lo, hi, res, unit,
                 decimals, on_change, initial):
        self.attr = attr
        self.on_change = on_change
        self.res = res
        self.decimals = decimals
        self.lo = lo
        self.hi = hi
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text=label, style="Card.TLabel",
                  width=13).grid(row=0, column=0, sticky="w", padx=(6, 8))
        self.var = tk.DoubleVar(value=initial)
        self.scale = ttk.Scale(frame, from_=lo, to=hi, orient="horizontal",
                               variable=self.var, command=self._on_scale)
        self.scale.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self.entry_var = tk.StringVar(value=f"{initial:.{decimals}f}")
        entry = ttk.Entry(frame, textvariable=self.entry_var,
                          width=9, justify="right")
        entry.grid(row=0, column=2, sticky="e")
        entry.bind("<Return>", self._on_entry)
        entry.bind("<FocusOut>", self._on_entry)
        ttk.Label(frame, text=unit, style="Unit.TLabel",
                  width=3).grid(row=0, column=3, sticky="w", padx=(4, 6))
        self.frame = frame

    def _on_scale(self, _val):
        v = round(self.var.get() / self.res) * self.res
        self.entry_var.set(f"{v:.{self.decimals}f}")
        self.on_change(self.attr, v)

    def _on_entry(self, _evt=None):
        try:
            v = float(self.entry_var.get())
        except ValueError:
            self.entry_var.set(f"{self.var.get():.{self.decimals}f}")
            return
        v = max(self.lo, min(self.hi, v))
        self.var.set(v)
        self.entry_var.set(f"{v:.{self.decimals}f}")
        self.on_change(self.attr, v)

    def set_value(self, v: float):
        self.var.set(v)
        self.entry_var.set(f"{v:.{self.decimals}f}")


# =============================================================================
# 메인 애플리케이션
# =============================================================================
class TunnelApp:
    def __init__(self):
        self.params = TunnelParams()
        self.dxf = DxfCache()
        self.dxf_path = DXF_DEFAULT_IN
        self.history = FitHistory()
        self.snapshots = SnapshotStore()
        self.rows: dict[str, ParamRow] = {}
        self.arch_rows: list[dict[str, ParamRow]] = []
        self._suspend = False

        self.root = tk.Tk()
        self.root.title("터널 단면 작도기 v6")
        self.root.geometry("1380x960")
        self.root.minsize(1180, 820)
        setup_style(self.root)

        self.auto_avoid_overlap = tk.BooleanVar(value=False)
        self.hatch_style = tk.StringVar(value=HATCH_STYLE_SOLID)

        paned = ttk.PanedWindow(self.root, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=8, pady=8)
        left = ttk.Frame(paned, padding=(4, 4))
        right = ttk.Frame(paned, padding=(4, 4))
        paned.add(left, weight=0)
        paned.add(right, weight=1)

        self._build_controls(left)
        self._build_canvas(right)

        self.update_plot()
        self.root.bind("<Control-s>", lambda e: self.save_dxf())
        self.root.bind("<Control-o>", lambda e: self.open_dxf())
        self.root.bind("<Control-f>", lambda e: self.auto_fit_fl())
        self.root.bind("<Control-Shift-F>", lambda e: self._on_shortcut_align())
        self.root.bind("<Control-Shift-S>", lambda e: self.take_snapshot())

    # ---------------------------------------------------------------
    def _build_controls(self, parent):
        header = ttk.Frame(parent)
        header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text="터널 단면 제원",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="슬라이더 또는 값을 직접 입력하세요.",
                  style="Info.TLabel").pack(anchor="w")

        type_frame = ttk.Frame(parent)
        type_frame.pack(fill="x", pady=(0, 8))
        self.type_var = tk.StringVar(value=self.params.kind.value)
        for tt in TunnelType:
            ttk.Radiobutton(
                type_frame, text=tt.value, value=tt.value,
                variable=self.type_var, command=self._on_type_change
            ).pack(side="left", padx=(0, 8))

        self.shape_group = ttk.LabelFrame(parent, text="  단면 형상  ", padding=8)
        self.shape_group.pack(fill="x", pady=(0, 8))
        self.shape_group.columnconfigure(0, weight=1)

        self.dim_group = ttk.LabelFrame(parent, text="  위치 · 치수  ", padding=8)
        self.dim_group.pack(fill="x", pady=(0, 8))
        self.dim_group.columnconfigure(0, weight=1)

        self._populate_param_rows()

        self.spec_label = ttk.Label(parent, text="", style="Spec.TLabel",
                                    anchor="w", justify="left")
        self.spec_label.pack(fill="x", pady=(0, 8))

        opts = ttk.LabelFrame(parent, text="  옵션  ", padding=8)
        opts.pack(fill="x", pady=(0, 8))
        ttk.Checkbutton(opts, text="겹침 자동 방지 (슬라이더 조작 시)",
                        variable=self.auto_avoid_overlap
                        ).pack(anchor="w")

        hatch_row = ttk.Frame(opts)
        hatch_row.pack(fill="x", pady=(6, 0))
        ttk.Label(hatch_row, text="DXF HATCH 스타일:",
                  style="Info.TLabel").pack(side="left", padx=(0, 8))
        for label, value in (("단색", HATCH_STYLE_SOLID),
                             ("ANSI31", HATCH_STYLE_PATTERN),
                             ("둘 다", HATCH_STYLE_BOTH)):
            ttk.Radiobutton(hatch_row, text=label, value=value,
                            variable=self.hatch_style
                            ).pack(side="left", padx=(0, 6))

        act = ttk.Frame(parent)
        act.pack(fill="x", pady=(0, 6))
        act.columnconfigure((0, 1), weight=1)

        self.btn_auto_fit = ttk.Button(
            act, text="⚡  FL 자동 맞춤  (Ctrl+F)",
            style="Accent.TButton", command=self.auto_fit_fl)
        self.btn_auto_fit.grid(row=0, column=0, columnspan=2,
                               sticky="ew", pady=(0, 6))

        self.btn_align_fl = ttk.Button(
            act, text="🔗  아치 FL 통일  (Ctrl+Shift+F)",
            style="Link.TButton", command=self.align_multi_arch_fl_ui)
        self.btn_align_fl.grid(row=1, column=0, columnspan=2,
                               sticky="ew", pady=(0, 6))
        self.btn_align_fl.grid_remove()

        ttk.Button(act, text="도면 저장  (Ctrl+S)",
                   command=self.save_dxf
                   ).grid(row=2, column=0, sticky="ew", padx=(0, 3))
        ttk.Button(act, text="DXF 열기  (Ctrl+O)",
                   command=self.open_dxf
                   ).grid(row=2, column=1, sticky="ew", padx=(3, 0))

        ttk.Button(act, text="스냅샷 저장  (Ctrl+Shift+S)",
                   command=self.take_snapshot
                   ).grid(row=3, column=0, columnspan=2, sticky="ew",
                          pady=(6, 0))
        ttk.Button(act, text="초기값 복원",
                   command=self.reset_params
                   ).grid(row=4, column=0, sticky="ew", padx=(0, 3), pady=(6, 0))
        ttk.Button(act, text="종료", style="Danger.TButton",
                   command=self.close
                   ).grid(row=4, column=1, sticky="ew", padx=(3, 0), pady=(6, 0))

    # ---------------------------------------------------------------
    def _populate_param_rows(self):
        for w in self.shape_group.winfo_children():
            w.destroy()
        for w in self.dim_group.winfo_children():
            w.destroy()
        self.rows.clear()
        self.arch_rows.clear()

        if self.params.kind == TunnelType.BOX:
            self._build_box_editor()
        elif self.params.kind in (TunnelType.NATM_2ARCH, TunnelType.NATM_3ARCH):
            self._build_multi_arch_editor()
        else:
            self._build_single_natm_editor()

    def _build_single_natm_editor(self):
        shape = [
            ("R1",         "R1",        1.0, 20.0, 0.01, "m", 3),
            ("상단 각도",   "top_angle",  0.0, 180.0, 0.5,  "°", 1),
            ("R2",         "R2",        1.0, 20.0, 0.01, "m", 3),
            ("R2 각도",    "r2_angle",   0.0, 180.0, 0.5,  "°", 1),
        ]
        dim = [
            ("선로 중심간격", "D",    0.0,  30.0, 0.01, "m", 2),
            ("R1 중심 Y",    "R1_Y", -10.0, 10.0, 0.01, "m", 3),
            ("목표 FL",      "FL",   -5.0,  5.0,  0.01, "m", 3),
        ]
        for i, (label, attr, lo, hi, res, unit, dec) in enumerate(shape):
            row = ParamRow(self.shape_group, label=label, attr=attr,
                           lo=lo, hi=hi, res=res, unit=unit, decimals=dec,
                           on_change=self._on_param_change,
                           initial=getattr(self.params, attr))
            row.frame.grid(row=i, column=0, sticky="ew", pady=2)
            self.rows[attr] = row
        for i, (label, attr, lo, hi, res, unit, dec) in enumerate(dim):
            row = ParamRow(self.dim_group, label=label, attr=attr,
                           lo=lo, hi=hi, res=res, unit=unit, decimals=dec,
                           on_change=self._on_param_change,
                           initial=getattr(self.params, attr))
            row.frame.grid(row=i, column=0, sticky="ew", pady=2)
            self.rows[attr] = row

    def _build_box_editor(self):
        base = [
            ("내공 폭 B",     "box_width",   2.0, 25.0, 0.01, "m", 2),
            ("내공 높이 H",   "box_height",  2.0, 20.0, 0.01, "m", 2),
            ("벽체 두께 tw",  "box_wall_t",  0.1,  2.0, 0.01, "m", 3),
            ("슬래브 두께 ts", "box_slab_t",  0.1,  2.0, 0.01, "m", 3),
        ]
        dim = [
            ("선로 중심간격", "D",  0.0, 30.0, 0.01, "m", 2),
            ("바닥 FL",       "FL", -5.0, 10.0, 0.01, "m", 3),
        ]
        for i, (label, attr, lo, hi, res, unit, dec) in enumerate(base):
            row = ParamRow(self.shape_group, label=label, attr=attr,
                           lo=lo, hi=hi, res=res, unit=unit, decimals=dec,
                           on_change=self._on_param_change,
                           initial=getattr(self.params, attr))
            row.frame.grid(row=i, column=0, sticky="ew", pady=2)
            self.rows[attr] = row
        for i, (label, attr, lo, hi, res, unit, dec) in enumerate(dim):
            row = ParamRow(self.dim_group, label=label, attr=attr,
                           lo=lo, hi=hi, res=res, unit=unit, decimals=dec,
                           on_change=self._on_param_change,
                           initial=getattr(self.params, attr))
            row.frame.grid(row=i, column=0, sticky="ew", pady=2)
            self.rows[attr] = row

        # 상단 모서리
        top_box = ttk.LabelFrame(self.shape_group,
                                 text="  상단 모서리  ", padding=6)
        top_box.grid(row=len(base), column=0, sticky="ew", pady=(6, 2))
        top_box.columnconfigure(0, weight=1)

        self.style_top_var = tk.StringVar(value=self.params.box_style_top.value)
        style_row_t = ttk.Frame(top_box, style="Card.TFrame")
        style_row_t.grid(row=0, column=0, sticky="w", pady=(0, 4))
        for cs in CornerStyle:
            ttk.Radiobutton(style_row_t, text=cs.value, value=cs.value,
                            variable=self.style_top_var,
                            command=self._on_box_style_change
                            ).pack(side="left", padx=(0, 8))

        row_r_t = ParamRow(top_box, label="필렛 R",
                           attr="box_fillet_top_r",
                           lo=0.0, hi=3.0, res=0.01, unit="m", decimals=3,
                           on_change=self._on_param_change,
                           initial=self.params.box_fillet_top_r)
        row_r_t.frame.grid(row=1, column=0, sticky="ew")
        self.rows["box_fillet_top_r"] = row_r_t

        ch_row_t = ttk.Frame(top_box, style="Card.TFrame")
        ch_row_t.grid(row=2, column=0, sticky="ew")
        for label, attr, init in (
                ("사선 dx", "box_chamfer_top_dx", self.params.box_chamfer_top_dx),
                ("사선 dy", "box_chamfer_top_dy", self.params.box_chamfer_top_dy)):
            row = ParamRow(ch_row_t, label=label, attr=attr,
                           lo=0.0, hi=3.0, res=0.01, unit="m", decimals=3,
                           on_change=self._on_param_change, initial=init)
            row.frame.pack(fill="x", pady=1)
            self.rows[attr] = row

        # 하단 모서리
        bot_box = ttk.LabelFrame(self.shape_group,
                                 text="  하단 모서리  ", padding=6)
        bot_box.grid(row=len(base) + 1, column=0, sticky="ew", pady=(6, 2))
        bot_box.columnconfigure(0, weight=1)

        self.style_bot_var = tk.StringVar(value=self.params.box_style_bot.value)
        style_row_b = ttk.Frame(bot_box, style="Card.TFrame")
        style_row_b.grid(row=0, column=0, sticky="w", pady=(0, 4))
        for cs in CornerStyle:
            ttk.Radiobutton(style_row_b, text=cs.value, value=cs.value,
                            variable=self.style_bot_var,
                            command=self._on_box_style_change
                            ).pack(side="left", padx=(0, 8))

        row_r_b = ParamRow(bot_box, label="필렛 R",
                           attr="box_fillet_bot_r",
                           lo=0.0, hi=3.0, res=0.01, unit="m", decimals=3,
                           on_change=self._on_param_change,
                           initial=self.params.box_fillet_bot_r)
        row_r_b.frame.grid(row=1, column=0, sticky="ew")
        self.rows["box_fillet_bot_r"] = row_r_b

        ch_row_b = ttk.Frame(bot_box, style="Card.TFrame")
        ch_row_b.grid(row=2, column=0, sticky="ew")
        for label, attr, init in (
                ("사선 dx", "box_chamfer_bot_dx", self.params.box_chamfer_bot_dx),
                ("사선 dy", "box_chamfer_bot_dy", self.params.box_chamfer_bot_dy)):
            row = ParamRow(ch_row_b, label=label, attr=attr,
                           lo=0.0, hi=3.0, res=0.01, unit="m", decimals=3,
                           on_change=self._on_param_change, initial=init)
            row.frame.pack(fill="x", pady=1)
            self.rows[attr] = row

    def _build_multi_arch_editor(self):
        nb = ttk.Notebook(self.shape_group)
        nb.pack(fill="both", expand=True)
        self.arch_notebook = nb

        labels = (["좌선", "우선"]
                  if self.params.kind == TunnelType.NATM_2ARCH
                  else ["중앙", "좌선", "우선"])
        specs = [
            ("R1",         "R1",        1.0, 25.0, 0.01, "m", 3),
            ("상단 각도",   "top_angle",  0.0, 180.0, 0.5, "°", 1),
            ("R2",         "R2",        1.0, 25.0, 0.01, "m", 3),
            ("R2 각도",    "r2_angle",   0.0, 180.0, 0.5, "°", 1),
            ("R1 중심 Y",  "R1_Y",     -5.0, 15.0, 0.01, "m", 3),
        ]
        for i, label in enumerate(labels):
            tab = ttk.Frame(nb)
            nb.add(tab, text=f"  {label}  ")
            rows_i: dict[str, ParamRow] = {}
            a = self.params.arches[i]
            for j, (lab, attr, lo, hi, res, unit, dec) in enumerate(specs):
                row = ParamRow(tab, label=lab, attr=f"arch{i}.{attr}",
                               lo=lo, hi=hi, res=res, unit=unit, decimals=dec,
                               on_change=self._on_arch_param_change,
                               initial=getattr(a, attr))
                row.frame.grid(row=j, column=0, sticky="ew", pady=2)
                rows_i[attr] = row
            tab.columnconfigure(0, weight=1)
            self.arch_rows.append(rows_i)

        extra = ([("중벽 폭", "pillar_w", 0.3, 5.0, 0.01, "m", 2)]
                 if self.params.kind == TunnelType.NATM_2ARCH
                 else [("좌측 이격", "gap_L", 0.0, 5.0, 0.01, "m", 2),
                       ("우측 이격", "gap_R", 0.0, 5.0, 0.01, "m", 2)])
        for j, (lab, attr, lo, hi, res, unit, dec) in enumerate(extra):
            row = ParamRow(self.dim_group, label=lab, attr=attr,
                           lo=lo, hi=hi, res=res, unit=unit, decimals=dec,
                           on_change=self._on_param_change,
                           initial=getattr(self.params, attr))
            row.frame.grid(row=j, column=0, sticky="ew", pady=2)
            self.rows[attr] = row

    def _on_arch_param_change(self, key: str, value: float):
        if self._suspend:
            return
        i_str, attr = key.split(".", 1)
        idx = int(i_str.replace("arch", ""))
        setattr(self.params.arches[idx], attr, value)
        if self._maybe_auto_avoid():
            return
        self.update_plot()

    def _on_box_style_change(self):
        self.params.box_style_top = CornerStyle(self.style_top_var.get())
        self.params.box_style_bot = CornerStyle(self.style_bot_var.get())
        self.update_plot()

    # ---------------------------------------------------------------
    def _on_type_change(self):
        new_kind = TunnelType(self.type_var.get())
        if new_kind == self.params.kind:
            return
        self.params.kind = new_kind

        if new_kind == TunnelType.NATM_2ARCH and len(self.params.arches) != 2:
            a = ArchParams(R1=self.params.R1, top_angle=self.params.top_angle,
                           R2=self.params.R2, r2_angle=self.params.r2_angle,
                           R1_Y=self.params.R1_Y)
            self.params.arches = [replace(a, label="좌선"),
                                  replace(a, label="우선")]
        elif new_kind == TunnelType.NATM_3ARCH and len(self.params.arches) != 3:
            central = ArchParams(R1=9.0, top_angle=100.0, R2=7.0,
                                 r2_angle=70.0, R1_Y=2.0, label="중앙")
            side = ArchParams(R1=5.5, top_angle=85.0, R2=4.5,
                              r2_angle=65.0, R1_Y=1.5, label="측선")
            self.params.arches = [central,
                                  replace(side, label="좌선"),
                                  replace(side, label="우선")]

        self._populate_param_rows()
        self._update_action_buttons(new_kind)
        self.update_plot()

    def _update_action_buttons(self, kind):
        if kind == TunnelType.NATM:
            self.btn_auto_fit.grid()
        else:
            self.btn_auto_fit.grid_remove()
        if kind in (TunnelType.NATM_2ARCH, TunnelType.NATM_3ARCH):
            self.btn_align_fl.grid()
        else:
            self.btn_align_fl.grid_remove()

    # ---------------------------------------------------------------
    def _build_canvas(self, parent):
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True)

        tab_plot = ttk.Frame(nb)
        nb.add(tab_plot, text="  도면  ")

        self.fig, self.ax = plt.subplots(figsize=(7, 6), dpi=100)
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.grid(True, color="#e5e5e5", linewidth=0.6)

        self.canvas = FigureCanvasTkAgg(self.fig, master=tab_plot)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        tb = ttk.Frame(tab_plot)
        tb.pack(fill="x")
        self.toolbar = NavigationToolbar2Tk(self.canvas, tb, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side="left")

        tab_hist = ttk.Frame(nb)
        nb.add(tab_hist, text="  이력  ")
        self._build_history_tab(tab_hist)

    def _build_history_tab(self, parent):
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True, padx=4, pady=4)

        fit_tab = ttk.Frame(nb)
        nb.add(fit_tab, text="  FL 자동 맞춤  ")
        self._build_fit_history_subtab(fit_tab)

        snap_tab = ttk.Frame(nb)
        nb.add(snap_tab, text="  제원 스냅샷  ")
        self._build_snapshot_subtab(snap_tab)

    def _build_fit_history_subtab(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(fill="x", padx=8, pady=6)
        ttk.Button(bar, text="CSV 저장",
                   command=self.save_history_csv).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="초기화",
                   command=self.clear_history).pack(side="left", padx=(0, 6))
        ttk.Label(bar, text="더블클릭으로 파라미터 복원",
                  style="Info.TLabel").pack(side="left", padx=(12, 0))
        self.hist_count = ttk.Label(bar, text="0건")
        self.hist_count.pack(side="right")

        cols = ("timestamp", "target_FL", "achieved_FL", "R1_Y", "dR1_Y",
                "R1", "top_angle", "R2", "r2_angle", "D", "status")
        heads = {
            "timestamp": "시각", "target_FL": "목표 FL", "achieved_FL": "달성 FL",
            "R1_Y": "R1_Y", "dR1_Y": "ΔR1_Y",
            "R1": "R1", "top_angle": "상단°", "R2": "R2",
            "r2_angle": "R2°", "D": "D", "status": "상태",
        }
        widths = {"timestamp": 140, "status": 50}
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.hist_tree = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            self.hist_tree.heading(c, text=heads[c])
            self.hist_tree.column(c, width=widths.get(c, 70), anchor="center")
        self.hist_tree.bind("<Double-1>", self._on_history_dblclick)
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.hist_tree.yview)
        self.hist_tree.configure(yscroll=sb.set)
        self.hist_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _build_snapshot_subtab(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(fill="x", padx=8, pady=6)
        ttk.Button(bar, text="현재 제원 저장",
                   style="Accent.TButton",
                   command=self.take_snapshot).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="JSON 저장",
                   command=self.save_snapshots_json).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="JSON 불러오기",
                   command=self.load_snapshots_json).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="선택 삭제",
                   command=self.delete_snapshot).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="초기화",
                   command=self.clear_snapshots).pack(side="left", padx=(0, 6))
        self.snap_count = ttk.Label(bar, text="0건")
        self.snap_count.pack(side="right")

        ttk.Label(parent, text="더블클릭으로 해당 제원 복원",
                  style="Info.TLabel").pack(anchor="w", padx=12)

        cols = ("timestamp", "kind", "total_area", "note")
        heads = {
            "timestamp": "시각", "kind": "타입",
            "total_area": "총 내공면적(㎡)", "note": "메모",
        }
        widths = {"timestamp": 140, "kind": 130, "total_area": 120, "note": 220}
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.snap_tree = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            self.snap_tree.heading(c, text=heads[c])
            self.snap_tree.column(c, width=widths.get(c, 100),
                                  anchor="center" if c != "note" else "w")
        self.snap_tree.bind("<Double-1>", self._on_snapshot_dblclick)
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.snap_tree.yview)
        self.snap_tree.configure(yscroll=sb.set)
        self.snap_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    # ---------------------------------------------------------------
    def _on_param_change(self, attr: str, value: float):
        if self._suspend:
            return
        setattr(self.params, attr, value)
        if self._maybe_auto_avoid():
            return
        self.update_plot()

    def _maybe_auto_avoid(self) -> bool:
        if (not self.auto_avoid_overlap.get()
                or self.params.kind not in (TunnelType.NATM_2ARCH,
                                            TunnelType.NATM_3ARCH)):
            return False
        return self._auto_fix_overlap()

    def _auto_fix_overlap(self) -> bool:
        fixed = False
        for _ in range(10):
            mg = compute_multi_arch(self.params)
            info = check_multi_arch_overlap(mg)
            if not info.has_overlap:
                break
            need = -info.min_gap + 0.01
            if self.params.kind == TunnelType.NATM_2ARCH:
                self.params.pillar_w += need
                self._suspend = True
                try:
                    if "pillar_w" in self.rows:
                        self.rows["pillar_w"].set_value(self.params.pillar_w)
                finally:
                    self._suspend = False
            else:
                self.params.gap_L += need / 2
                self.params.gap_R += need / 2
                self._suspend = True
                try:
                    for k in ("gap_L", "gap_R"):
                        if k in self.rows:
                            self.rows[k].set_value(getattr(self.params, k))
                finally:
                    self._suspend = False
            fixed = True
        if fixed:
            self.update_plot()
        return fixed

    def _apply_params(self, **kwargs):
        self._suspend = True
        try:
            for k, v in kwargs.items():
                if not hasattr(self.params, k):
                    continue
                setattr(self.params, k, v)
                if k in self.rows:
                    self.rows[k].set_value(v)
        finally:
            self._suspend = False
        self.update_plot()

    def reset_params(self):
        if not messagebox.askyesno("초기값 복원",
                                   "모든 파라미터를 초기값으로 되돌릴까요?"):
            return
        kind = self.params.kind
        d = TunnelParams(kind=kind)
        if kind == TunnelType.NATM_2ARCH:
            a = ArchParams()
            d.arches = [replace(a, label="좌선"), replace(a, label="우선")]
        elif kind == TunnelType.NATM_3ARCH:
            central = ArchParams(R1=9.0, top_angle=100.0, R2=7.0,
                                 r2_angle=70.0, R1_Y=2.0, label="중앙")
            side = ArchParams(R1=5.5, top_angle=85.0, R2=4.5,
                              r2_angle=65.0, R1_Y=1.5, label="측선")
            d.arches = [central, replace(side, label="좌선"),
                        replace(side, label="우선")]
        self.params = d
        self.type_var.set(kind.value)
        self._populate_param_rows()
        self._update_action_buttons(kind)
        self.update_plot()

    # ---------------------------------------------------------------
    def auto_fit_fl(self):
        if self.params.kind != TunnelType.NATM:
            if self.params.kind == TunnelType.BOX:
                messagebox.showinfo("FL 자동 맞춤",
                                    "개착 Box형은 H가 FL을 직접 결정합니다.")
            else:
                messagebox.showinfo(
                    "FL 자동 맞춤",
                    "2-Arch / 3-Arch는 '아치 FL 통일'을 사용하세요.\n"
                    "(Ctrl+Shift+F)")
            return

        p = self.params
        target = simpledialog.askfloat(
            "FL 자동 맞춤",
            f"목표 FL 값을 입력하세요 (현재 {p.FL:.3f}):",
            initialvalue=p.FL)
        if target is None:
            return

        p_target = replace(p, FL=target)
        r1_y_prev = p.R1_Y
        r1_y_opt, ok = fit_R1_Y_to_FL(p_target)

        if not ok:
            self.history.add(p_target, r1_y_prev, float("nan"), success=False)
            self._refresh_history_view()
            messagebox.showwarning(
                "자동 맞춤 실패",
                f"FL={target}을 만족하는 R1_Y를 찾을 수 없습니다.")
            return

        self.params.FL = target
        self.params.R1_Y = r1_y_opt
        self._suspend = True
        try:
            self.rows["FL"].set_value(target)
            self.rows["R1_Y"].set_value(r1_y_opt)
        finally:
            self._suspend = False
        self.update_plot()

        achieved = compute_fl(self.params, r1_y_opt)
        entry = self.history.add(self.params, r1_y_prev, achieved, success=True)
        self._refresh_history_view()
        self.take_snapshot(auto=True,
                           note=f"NATM FL 자동 맞춤 (목표 {target:.3f})")

        messagebox.showinfo(
            "자동 맞춤 완료",
            f"R1_Y  = {r1_y_opt:.4f}  (Δ {entry.dR1_Y:+.4f})\n"
            f"FL     = {achieved:.4f}  (목표 {target})\n"
            f"이력 {len(self.history.entries)}건 / "
            f"스냅샷 {len(self.snapshots.entries)}건")

    # ---------------------------------------------------------------
    def _on_shortcut_align(self):
        if self.params.kind in (TunnelType.NATM_2ARCH, TunnelType.NATM_3ARCH):
            self.align_multi_arch_fl_ui()
        else:
            messagebox.showinfo("FL 통일",
                                "다중 아치(2-Arch / 3-Arch)에서만 사용할 수 있습니다.")

    def align_multi_arch_fl_ui(self):
        if self.params.kind not in (TunnelType.NATM_2ARCH, TunnelType.NATM_3ARCH):
            return

        p = self.params
        labels = [a.label for a in p.arches]

        ref_idx = self._ask_reference_arch(labels, 0)
        if ref_idx is None:
            return

        result = align_multi_arch_fl(p, reference_idx=ref_idx)
        if not all(result.success):
            fails = [labels[i] for i, ok in enumerate(result.success) if not ok]
            messagebox.showwarning(
                "FL 통일 실패",
                f"다음 아치의 FL을 맞출 수 없습니다: {', '.join(fails)}\n"
                f"R1/R2/각도 조합을 확인하세요.")
            return

        if not self._confirm_align_dialog(result, labels[ref_idx]):
            return
        if not self._guard_overlap("FL 통일 적용"):
            return

        self._suspend = True
        try:
            for i, new_y in enumerate(result.new_R1Y):
                self.params.arches[i] = replace(self.params.arches[i],
                                                R1_Y=new_y)
            for i, rows in enumerate(self.arch_rows):
                if "R1_Y" in rows:
                    rows["R1_Y"].set_value(result.new_R1Y[i])
        finally:
            self._suspend = False

        self.update_plot()
        self.take_snapshot(auto=True,
                           note=f"FL 통일 후 (기준: {labels[ref_idx]}, "
                                f"FL={result.target_FL:.3f})")

        messagebox.showinfo(
            "FL 통일 완료",
            f"기준: {labels[ref_idx]}  (FL = {result.target_FL:.4f} m)\n"
            + "\n".join(
                f"  {result.labels[i]}: R1_Y {result.old_R1Y[i]:.3f} → "
                f"{result.new_R1Y[i]:.3f}  "
                f"(Δ {result.new_R1Y[i] - result.old_R1Y[i]:+.3f})"
                for i in range(len(result.labels))))

    def _ask_reference_arch(self, labels, default_idx=0) -> Optional[int]:
        win = tk.Toplevel(self.root)
        win.title("FL 통일 기준")
        win.transient(self.root)
        win.grab_set()
        win.resizable(False, False)

        ttk.Label(win, text="기준이 될 아치를 선택하세요.\n"
                            "(다른 아치들이 이 FL에 맞춰집니다)",
                  padding=12).pack()

        var = tk.IntVar(value=default_idx)
        frame = ttk.Frame(win, padding=(16, 0, 16, 8))
        frame.pack(fill="x")
        for i, label in enumerate(labels):
            ttk.Radiobutton(frame, text=label, value=i,
                            variable=var).pack(anchor="w", pady=2)

        result = {"idx": None}

        def on_ok():
            result["idx"] = var.get()
            win.destroy()

        btns = ttk.Frame(win, padding=(16, 8, 16, 12))
        btns.pack(fill="x")
        ttk.Button(btns, text="취소",
                   command=win.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(btns, text="확인", style="Accent.TButton",
                   command=on_ok).pack(side="right")

        win.update_idletasks()
        x = (self.root.winfo_rootx() + self.root.winfo_width() // 2
             - win.winfo_width() // 2)
        y = (self.root.winfo_rooty() + self.root.winfo_height() // 2
             - win.winfo_height() // 2)
        win.geometry(f"+{x}+{y}")
        self.root.wait_window(win)
        return result["idx"]

    def _confirm_align_dialog(self, r: AlignResult, ref_label: str) -> bool:
        win = tk.Toplevel(self.root)
        win.title("FL 통일 미리보기")
        win.transient(self.root)
        win.grab_set()

        ttk.Label(win, text=f"기준 아치: {ref_label}   (FL = {r.target_FL:.4f} m)",
                  style="Title.TLabel", padding=(12, 12, 12, 6)).pack(anchor="w")

        cols = ("label", "old_R1Y", "new_R1Y", "delta", "old_FL", "new_FL")
        heads = {
            "label": "아치", "old_R1Y": "이전 R1_Y", "new_R1Y": "변경 R1_Y",
            "delta": "ΔR1_Y", "old_FL": "이전 FL", "new_FL": "변경 FL",
        }
        frame = ttk.Frame(win, padding=(12, 0, 12, 8))
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=cols, show="headings",
                            height=len(r.labels))
        for c in cols:
            tree.heading(c, text=heads[c])
            tree.column(c, width=100, anchor="center")
        for i, label in enumerate(r.labels):
            tree.insert("", "end", values=(
                label,
                f"{r.old_R1Y[i]:.4f}", f"{r.new_R1Y[i]:.4f}",
                f"{r.new_R1Y[i] - r.old_R1Y[i]:+.4f}",
                f"{r.old_FL[i]:.4f}", f"{r.new_FL[i]:.4f}"))
        tree.pack(side="left", fill="both", expand=True)

        result = {"ok": False}
        btns = ttk.Frame(win, padding=(12, 0, 12, 12))
        btns.pack(fill="x", side="bottom")
        ttk.Button(btns, text="취소",
                   command=win.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(btns, text="적용", style="Accent.TButton",
                   command=lambda: (result.update(ok=True), win.destroy())
                   ).pack(side="right")

        win.update_idletasks()
        x = (self.root.winfo_rootx() + self.root.winfo_width() // 2
             - win.winfo_width() // 2)
        y = (self.root.winfo_rooty() + self.root.winfo_height() // 2
             - win.winfo_height() // 2)
        win.geometry(f"+{x}+{y}")
        self.root.wait_window(win)
        return result["ok"]

    def _guard_overlap(self, action_name: str) -> bool:
        if self.params.kind not in (TunnelType.NATM_2ARCH, TunnelType.NATM_3ARCH):
            return True
        mg = compute_multi_arch(self.params)
        info = check_multi_arch_overlap(mg)
        if not info.has_overlap:
            return True
        names = [f"{mg.layout[i].label}↔{mg.layout[j].label}"
                 for i, j in info.pairs]
        total = sum(info.overlap_areas)
        return messagebox.askyesno(
            "아치 겹침 경고",
            f"다음 아치가 겹쳐 있습니다:\n  {', '.join(names)}\n"
            f"겹침 면적 합: {total:.2f}㎡\n\n"
            f"그래도 {action_name}을(를) 계속할까요?")

    # ---------------------------------------------------------------
    def _refresh_history_view(self):
        for i in self.hist_tree.get_children():
            self.hist_tree.delete(i)
        for e in self.history.entries:
            status = "✅" if e.is_ok else ("⚠️" if e.success else "❌")
            self.hist_tree.insert("", "end", values=(
                e.timestamp, f"{e.target_FL:.4f}",
                f"{e.achieved_FL:.4f}" if e.success else "-",
                f"{e.R1_Y:.4f}", f"{e.dR1_Y:+.4f}",
                f"{e.R1:.2f}", f"{e.top_angle:.1f}",
                f"{e.R2:.2f}", f"{e.r2_angle:.1f}", f"{e.D:.2f}",
                status))
        self.hist_count.config(text=f"{len(self.history.entries)}건")

    def _on_history_dblclick(self, _evt):
        sel = self.hist_tree.selection()
        if not sel:
            return
        idx = self.hist_tree.index(sel[0])
        e = self.history.entries[idx]
        if not messagebox.askyesno("이력 복원",
                                   f"{e.timestamp} 값으로 파라미터를 복원할까요?"):
            return
        if self.params.kind != TunnelType.NATM:
            self.type_var.set(TunnelType.NATM.value)
            self.params.kind = TunnelType.NATM
            self._populate_param_rows()
            self._update_action_buttons(TunnelType.NATM)
        self._apply_params(R1=e.R1, top_angle=e.top_angle, R2=e.R2,
                           r2_angle=e.r2_angle, D=e.D,
                           R1_Y=e.R1_Y, FL=e.target_FL)

    def save_history_csv(self):
        if not self.history.entries:
            messagebox.showinfo("이력", "저장할 이력이 없습니다.")
            return
        path = filedialog.asksaveasfilename(
            title="이력 CSV 저장", defaultextension=".csv",
            initialfile=f"fit_history_{datetime.now():%Y%m%d_%H%M%S}.csv",
            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            self.history.to_csv(path)
            messagebox.showinfo("저장 완료", path)
        except Exception as ex:
            messagebox.showerror("저장 실패", str(ex))

    def clear_history(self):
        if not self.history.entries:
            return
        if messagebox.askyesno("이력 초기화",
                               f"{len(self.history.entries)}건을 삭제할까요?"):
            self.history.entries.clear()
            self._refresh_history_view()

    # ---------------------------------------------------------------
    def take_snapshot(self, auto: bool = False, note: str = ""):
        if not auto and not self._guard_overlap("스냅샷 저장"):
            return

        p = self.params
        if p.kind == TunnelType.BOX:
            total = compute_box_geometry(p).inner_area
        elif p.kind in (TunnelType.NATM_2ARCH, TunnelType.NATM_3ARCH):
            total = compute_multi_arch(p).total_area
        else:
            a = ArchParams(R1=p.R1, top_angle=p.top_angle, R2=p.R2,
                           r2_angle=p.r2_angle, R1_Y=p.R1_Y, cx=0.0)
            total = compute_geometry_from_arch(a, FL=p.FL).area

        if not auto:
            note = simpledialog.askstring(
                "제원 스냅샷", "메모를 입력하세요 (선택):",
                initialvalue=note or p.kind.value) or ""

        self.snapshots.add(p, total_area=total, note=note)
        self._refresh_snapshot_view()
        if not auto:
            messagebox.showinfo(
                "스냅샷 저장",
                f"제원 스냅샷이 저장되었습니다 "
                f"({len(self.snapshots.entries)}건).")

    def _refresh_snapshot_view(self):
        for i in self.snap_tree.get_children():
            self.snap_tree.delete(i)
        for e in self.snapshots.entries:
            self.snap_tree.insert("", "end", values=(
                e.timestamp, e.kind, f"{e.total_area:.2f}", e.note))
        self.snap_count.config(text=f"{len(self.snapshots.entries)}건")

    def _on_snapshot_dblclick(self, _evt):
        sel = self.snap_tree.selection()
        if not sel:
            return
        idx = self.snap_tree.index(sel[0])
        e = self.snapshots.entries[idx]
        if not messagebox.askyesno(
                "스냅샷 복원",
                f"{e.timestamp}\n{e.kind}\n{e.note or '(메모 없음)'}\n\n"
                f"이 제원으로 복원할까요?"):
            return
        self._restore_snapshot(e)

    def _restore_snapshot(self, e: SnapshotEntry):
        try:
            new_p = SnapshotStore.deserialize(e.payload)
        except Exception as ex:
            messagebox.showerror("복원 실패", str(ex))
            return
        self.params = new_p
        self.type_var.set(new_p.kind.value)
        self._populate_param_rows()
        self._update_action_buttons(new_p.kind)
        self.update_plot()

    def delete_snapshot(self):
        sel = self.snap_tree.selection()
        if not sel:
            return
        idxs = sorted((self.snap_tree.index(i) for i in sel), reverse=True)
        if not messagebox.askyesno("삭제", f"{len(idxs)}건을 삭제할까요?"):
            return
        for i in idxs:
            self.snapshots.entries.pop(i)
        self._refresh_snapshot_view()

    def clear_snapshots(self):
        if not self.snapshots.entries:
            return
        if messagebox.askyesno("스냅샷 초기화",
                               f"{len(self.snapshots.entries)}건을 삭제할까요?"):
            self.snapshots.entries.clear()
            self._refresh_snapshot_view()

    def save_snapshots_json(self):
        if not self.snapshots.entries:
            messagebox.showinfo("스냅샷", "저장할 스냅샷이 없습니다.")
            return
        path = filedialog.asksaveasfilename(
            title="스냅샷 JSON 저장", defaultextension=".json",
            initialfile=f"snapshots_{datetime.now():%Y%m%d_%H%M%S}.json",
            filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            self.snapshots.to_json(path)
            messagebox.showinfo("저장 완료", path)
        except Exception as ex:
            messagebox.showerror("저장 실패", str(ex))

    def load_snapshots_json(self):
        path = filedialog.askopenfilename(
            title="스냅샷 JSON 불러오기",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            self.snapshots.from_json(path)
            self._refresh_snapshot_view()
            messagebox.showinfo("불러오기 완료",
                                f"{len(self.snapshots.entries)}건 로드됨.")
        except Exception as ex:
            messagebox.showerror("불러오기 실패", str(ex))

    # ---------------------------------------------------------------
    # 렌더링
    # ---------------------------------------------------------------
    def update_plot(self):
        p = self.params
        ax = self.ax
        ax.clear()
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, color="#e5e5e5", linewidth=0.6)

        self._draw_cad(translate_x=-p.D / 2, translate_y=+p.RL)
        self._draw_cad(translate_x=+p.D / 2, translate_y=+p.RL)

        if p.kind == TunnelType.BOX:
            g = compute_box_geometry(p)
            self._draw_box_section(g)
            self._update_box_spec_panel(g)
        elif p.kind in (TunnelType.NATM_2ARCH, TunnelType.NATM_3ARCH):
            mg = compute_multi_arch(p)
            self._draw_multi_arch(mg, p)
            self._update_multi_arch_spec_panel(mg, p)
        else:
            a = ArchParams(R1=p.R1, top_angle=p.top_angle, R2=p.R2,
                           r2_angle=p.r2_angle, R1_Y=p.R1_Y,
                           cx=0.0, label="본선")
            g = compute_geometry_from_arch(a, FL=p.FL)
            self._draw_tunnel(g, p)
            self._draw_haunch_bottom(g, p)
            self._draw_centerlines(p, g)
            self._draw_dimension_lines(g, p)
            self._draw_angles(g)
            self._draw_safe_box(g, p)
            self._draw_sl_line(g)
            self._update_spec_panel(g, p)

        self.canvas.draw_idle()

    def _draw_cad(self, translate_x, translate_y):
        ents = self.dxf.load(self.dxf_path)
        if not ents:
            return
        ax = self.ax
        for e in ents:
            t = e.dxftype()
            if t == 'LINE':
                s, en = e.dxf.start, e.dxf.end
                ax.plot([s.x + translate_x, en.x + translate_x],
                        [s.y + translate_y, en.y + translate_y], 'k-', lw=0.8)
            elif t == 'CIRCLE':
                c, r = e.dxf.center, e.dxf.radius
                ax.add_patch(Circle((c.x + translate_x, c.y + translate_y),
                                    r, color='r', fill=False))
            elif t == 'ARC':
                c, r = e.dxf.center, e.dxf.radius
                ax.add_patch(Arc((c.x + translate_x, c.y + translate_y),
                                 2 * r, 2 * r, angle=0,
                                 theta1=e.dxf.start_angle,
                                 theta2=e.dxf.end_angle, color='g'))

    # ---------- 단일 NATM ----------
    def _draw_tunnel(self, g, p):
        ax = self.ax
        a_left, a_right = g.a.r1_angles

        def arc(c, r, s, e, color):
            if e < s:
                e += 360.0
            ax.add_patch(Arc(c, 2 * r, 2 * r, angle=0,
                             theta1=s, theta2=e, color=color, lw=1.8))

        arc(g.center_top, g.a.R1, a_right, a_left, '#d64545')
        arc(g.left_center, g.a.R2, a_left, a_left + g.a.r2_angle, '#2f6fed')
        arc(g.right_center, g.a.R2, a_right - g.a.r2_angle, a_right, '#2b8a3e')

    def _draw_haunch_bottom(self, g, p):
        ax = self.ax
        for end, side, sign in ((g.left_end, p.sideL, +1),
                                (g.right_end, p.sideR, -1)):
            x = [end[0], end[0] + sign * side, end[0] + sign * side, 0]
            y = [end[1], end[1], end[1] - p.fl_to_culvert,
                 end[1] - p.fl_to_culvert]
            ax.plot(x, y, 'k-', lw=1.2)

    def _draw_centerlines(self, p, g):
        ax = self.ax
        y_text = g.top_of_tunnel + LABEL_Y_MARGIN
        for x, label in ((-p.D / 2, 'CL of 하선'),
                         (0, 'CL of 터널'),
                         (p.D / 2, 'CL of 상선')):
            ax.axvline(x, color='gray', linestyle='--', linewidth=0.9)
            ax.text(x, y_text, label, ha='center', fontsize=9, color='#555555')

    def _draw_dimension_lines(self, g, p):
        ax = self.ax
        for c, e in ((g.center_top, g.top_end),
                     (g.center_top, g.top_start),
                     (g.left_center, g.left_end),
                     (g.right_center, g.right_end)):
            ax.plot([c[0], e[0]], [c[1], e[1]],
                    linestyle='--', color='#888888', lw=0.8)

        a_left, a_right = g.a.r1_angles
        for c, e, ang in ((g.center_top, g.top_end, a_right),
                          (g.center_top, g.top_start, a_left)):
            m = ((c[0] + e[0]) / 2, (c[1] + e[1]) / 2)
            ax.text(m[0] - 0.25, m[1] + 0.25, f'R1={g.a.R1 * 1000:.0f}',
                    rotation=ang, fontsize=9)
        for c, e in ((g.left_center, g.left_end),
                     (g.right_center, g.right_end)):
            m = ((c[0] + e[0]) / 2, (c[1] + e[1]) / 2)
            rot = math.degrees(math.atan2(e[1] - c[1], e[0] - c[0]))
            ax.text(m[0], m[1], f'R2={g.a.R2 * 1000:.0f}',
                    rotation=rot, fontsize=9)

    def _draw_angles(self, g):
        self._draw_angle_annotation(g.top_start, g.center_top, g.top_end)
        self._draw_angle_annotation(g.left_end, g.left_center, g.top_start)
        self._draw_angle_annotation(g.top_end, g.right_center, g.right_end)

    def _draw_angle_annotation(self, p1, p2, p3, radius=1.0):
        v1 = np.array(p1) - np.array(p2)
        v2 = np.array(p3) - np.array(p2)
        cos = np.clip(v1 @ v2 / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1, 1)
        angle_deg = math.degrees(math.acos(cos))
        a1 = math.degrees(math.atan2(v1[1], v1[0]))
        a2 = math.degrees(math.atan2(v2[1], v2[0]))
        if a2 < a1:
            a2 += 360.0
        self.ax.add_patch(Arc(p2, 2 * radius, 2 * radius, angle=0,
                              theta1=a1, theta2=a2, color='#333333'))
        mid = math.radians((a1 + a2) / 2.0)
        self.ax.text(p2[0] + radius * 0.7 * math.cos(mid),
                     p2[1] + radius * 0.7 * math.sin(mid),
                     f'{angle_deg:.1f}°', fontsize=11, ha='center',
                     color='#333333')

    def _draw_safe_box(self, g, p):
        ax = self.ax
        h = p.safeheight
        for end, side, sign in ((g.left_end, p.sideL, +1),
                                (g.right_end, p.sideR, -1)):
            x0, y0 = end
            x1 = x0 + sign * side
            ax.plot([x0, x0, x1, x1], [y0, y0 + h, y0 + h, y0],
                    color='#9aa0a6', linestyle='--', lw=0.9)
            ax.plot([x0, x1], [y0 + h, y0], color='#9aa0a6',
                    linestyle='--', lw=0.9)
            ax.plot([x1, x0], [y0 + h, y0], color='#9aa0a6',
                    linestyle='--', lw=0.9)

    def _draw_sl_line(self, g):
        ax = self.ax
        ax.axhline(g.SL, color='#9aa0a6', linestyle='--', linewidth=0.9)
        ax.text(g.left_end[0] - 0.6, g.SL, 'SL',
                fontsize=9, color='#555555', va='center')

    def _update_spec_panel(self, g, p):
        new_fl = compute_fl(p, g.a.R1_Y)
        ok = abs(new_fl - p.FL) <= FL_TOLERANCE
        mark = "✅" if ok else "⚠️"
        self.spec_label.config(text=(
            f"면적 {g.area:.2f}㎡   |   A {g.A:.2f}m   |   "
            f"SL {g.SL:.2f}m   |   편평률 {g.top_of_tunnel / (g.A * 2):.2f}\n"
            f"R2/R1 {g.a.R2 / g.a.R1:.2f}   |   "
            f"FL {new_fl:.3f}m (목표 {p.FL:.3f}m)   {mark}"))

    # ---------- 다중 아치 ----------
    def _draw_multi_arch(self, mg, p):
        palette = ['#2f6fed', '#2b8a3e', '#d64545']
        for i, (g, a) in enumerate(zip(mg.arches, mg.layout)):
            color = palette[i % len(palette)]
            self._draw_single_arch(g, a, color)

        ax = self.ax
        ax.axvline(0, color='gray', linestyle='--', lw=0.9)
        ax.text(0, max(g.top_of_tunnel for g in mg.arches) + 1.2,
                'CL', ha='center', fontsize=9)

        ax.axhline(p.FL, color='#d64545', linestyle=':', lw=1)

        if p.kind == TunnelType.NATM_2ARCH:
            self._draw_pillar(mg, p)
        else:
            self._draw_gaps(mg, p)
        self._draw_overlap_highlight(mg)

    def _draw_single_arch(self, g, a, color):
        ax = self.ax

        def arc(c, r, s, e):
            if e < s:
                e += 360
            ax.add_patch(Arc(c, 2 * r, 2 * r, angle=0,
                             theta1=s, theta2=e, color=color, lw=1.8))

        a_left, a_right = a.r1_angles
        arc(g.center_top, a.R1, a_right, a_left)
        arc(g.left_center, a.R2, a_left, a_left + a.r2_angle)
        arc(g.right_center, a.R2, a_right - a.r2_angle, a_right)

        ax.plot([g.left_end[0], g.right_end[0]],
                [g.left_end[1], g.right_end[1]], 'k-', lw=1.2)

        ax.text(a.cx, g.top_of_tunnel + 0.4, a.label,
                ha='center', fontsize=10, color=color, fontweight='bold')

    def _draw_pillar(self, mg, p):
        left_g, right_g = mg.arches[0], mg.arches[1]
        x_l, x_r = left_g.right_end[0], right_g.left_end[0]
        y_b = max(left_g.right_end[1], right_g.left_end[1])
        y_t = max(left_g.top_of_tunnel, right_g.top_of_tunnel)

        self.ax.add_patch(MplRect(
            (x_l, y_b), x_r - x_l, y_t - y_b,
            facecolor='#f0f0f0', edgecolor='#888888',
            hatch='///', alpha=0.6, linewidth=0.8))
        self.ax.text((x_l + x_r) / 2, y_b - 0.6,
                     f'중벽 {p.pillar_w * 1000:.0f}',
                     ha='center', fontsize=9, color='#666666')

    def _draw_gaps(self, mg, p):
        central = mg.arches[0]
        left = mg.arches[1]
        right = mg.arches[2]

        def gap_arrow(x1, x2, y, label):
            self.ax.annotate('', xy=(x1, y), xytext=(x2, y),
                             arrowprops=dict(arrowstyle='<->',
                                             color='#333333', lw=1))
            self.ax.text((x1 + x2) / 2, y + 0.25, label,
                         ha='center', fontsize=8)

        y_arrow = p.FL + 0.3
        gap_arrow(left.top_end[0], central.left_end[0],
                  y_arrow, f'{p.gap_L * 1000:.0f}')
        gap_arrow(central.right_end[0], right.top_start[0],
                  y_arrow, f'{p.gap_R * 1000:.0f}')

    def _draw_overlap_highlight(self, mg):
        info = check_multi_arch_overlap(mg)
        if not info.has_overlap:
            return
        geoms = [g.polygon for g in mg.arches]
        for (i, j), area in zip(info.pairs, info.overlap_areas):
            inter = geoms[i].intersection(geoms[j])
            polys = ([inter] if inter.geom_type == "Polygon"
                     else list(getattr(inter, "geoms", [])))
            for poly in polys:
                if poly.is_empty:
                    continue
                xs, ys = poly.exterior.xy
                self.ax.fill(xs, ys, facecolor='red', alpha=0.25,
                             edgecolor='red', linestyle='-', linewidth=1.2)
                cx, cy = poly.centroid.x, poly.centroid.y
                self.ax.text(cx, cy, f"겹침 {area:.2f}㎡",
                             ha='center', va='center', fontsize=9,
                             color='white', fontweight='bold',
                             bbox=dict(boxstyle="round,pad=0.2",
                                       facecolor="red", edgecolor="none",
                                       alpha=0.85))
        names = [f"{mg.layout[i].label}↔{mg.layout[j].label}"
                 for i, j in info.pairs]
        y_top = max(g.top_of_tunnel for g in mg.arches) + 1.8
        self.ax.text(0, y_top, f"⚠ 아치 겹침: {', '.join(names)}",
                     ha='center', fontsize=10, color='white',
                     bbox=dict(boxstyle="round,pad=0.4",
                               facecolor="#d64545", edgecolor="none"))

    def _update_multi_arch_spec_panel(self, mg, p):
        fls = [compute_fl_for_arch(a) - p.fl_to_culvert for a in mg.layout]
        fl_spread = max(fls) - min(fls)
        unified = ("✅ 통일" if fl_spread < FL_TOLERANCE
                   else f"⚠️ 편차 {fl_spread * 1000:.0f}mm")

        overlap = check_multi_arch_overlap(mg)
        if overlap.has_overlap:
            names = [f"{mg.layout[i].label}↔{mg.layout[j].label}"
                     for i, j in overlap.pairs]
            overlap_txt = f"❌ 겹침: {', '.join(names)}"
        elif overlap.min_gap < 0.05:
            overlap_txt = f"⚠️ 인접 (최소 간격 {overlap.min_gap * 1000:.0f}mm)"
        else:
            overlap_txt = f"✅ 분리 (최소 간격 {overlap.min_gap * 1000:.0f}mm)"

        if p.kind == TunnelType.NATM_2ARCH:
            left, right = mg.arches
            lines = [
                f"총 내공면적 {mg.total_area:.2f}㎡  |  중벽 {p.pillar_w * 1000:.0f}mm",
                f"좌 {left.area:.2f}㎡ (FL {fls[0]:.3f})  |  "
                f"우 {right.area:.2f}㎡ (FL {fls[1]:.3f})",
                f"FL 상태: {unified}",
                f"겹침 검사: {overlap_txt}",
            ]
            if p.pillar_w < MIN_PILLAR_W:
                lines.append(
                    f"⚠️ 중벽 폭 {p.pillar_w * 1000:.0f}mm < "
                    f"최소 {MIN_PILLAR_W * 1000:.0f}mm")
        else:
            c, l, r = mg.arches
            lines = [
                f"총 내공면적 {mg.total_area:.2f}㎡  |  "
                f"이격 L{p.gap_L * 1000:.0f} R{p.gap_R * 1000:.0f}",
                f"중앙 {c.area:.2f}㎡ (FL {fls[0]:.3f})  |  "
                f"좌 {l.area:.2f}㎡ (FL {fls[1]:.3f})  |  "
                f"우 {r.area:.2f}㎡ (FL {fls[2]:.3f})",
                f"FL 상태: {unified}",
                f"겹침 검사: {overlap_txt}",
            ]
        self.spec_label.config(text="\n".join(lines))

    # ---------- Box ----------
    def _draw_box_section(self, g):
        p, ax = g.p, self.ax
        tw, ts = p.box_wall_t, p.box_slab_t

        oxs, oys = g.outer.exterior.xy
        ax.plot(oxs, oys, color='#555555', lw=1.6)

        xs = [pt[0] for pt in g.inner_pts]
        ys = [pt[1] for pt in g.inner_pts]
        ax.plot(xs, ys, color='#2f6fed', lw=2.0)

        try:
            wall_poly = g.outer.difference(g.inner)
            geoms = ([wall_poly] if wall_poly.geom_type == 'Polygon'
                     else list(wall_poly.geoms))
            for poly in geoms:
                _fill_polygon(ax, poly, color='#d0d4da', alpha=0.55)
        except Exception:
            pass

        for center, r, a1, a2 in g.fillet_arcs:
            if a2 < a1:
                a2 += 360
            ax.add_patch(Arc(center, 2 * r, 2 * r, angle=0,
                             theta1=a1, theta2=a2, color='#d64545', lw=1.2))

        # 필렛 라벨
        if (p.box_style_top == CornerStyle.FILLET
                and p.box_fillet_top_r > 0):
            ax.text(g.cx_right - p.box_fillet_top_r - 0.35,
                    g.ceiling_y - p.box_fillet_top_r - 0.35,
                    f'R{p.box_fillet_top_r * 1000:.0f}',
                    fontsize=8, color='#d64545')
        if (p.box_style_bot == CornerStyle.FILLET
                and p.box_fillet_bot_r > 0):
            ax.text(g.cx_right - p.box_fillet_bot_r - 0.35,
                    g.floor_y + p.box_fillet_bot_r + 0.15,
                    f'R{p.box_fillet_bot_r * 1000:.0f}',
                    fontsize=8, color='#d64545')

        # 사선 라벨
        if p.box_style_top == CornerStyle.CHAMFER:
            ax.text(g.cx_right - p.box_chamfer_top_dx - 0.2,
                    g.ceiling_y - p.box_chamfer_top_dy - 0.2,
                    f'{p.box_chamfer_top_dx * 1000:.0f}×'
                    f'{p.box_chamfer_top_dy * 1000:.0f}',
                    fontsize=8, color='#d64545')
        if p.box_style_bot == CornerStyle.CHAMFER:
            ax.text(g.cx_right - p.box_chamfer_bot_dx - 0.2,
                    g.floor_y + p.box_chamfer_bot_dy + 0.15,
                    f'{p.box_chamfer_bot_dx * 1000:.0f}×'
                    f'{p.box_chamfer_bot_dy * 1000:.0f}',
                    fontsize=8, color='#d64545')

        y_dim = g.top_of_tunnel + 0.5
        ax.annotate('', xy=(g.cx_left, y_dim), xytext=(g.cx_right, y_dim),
                    arrowprops=dict(arrowstyle='<->', color='#333333', lw=1))
        ax.text(0, y_dim + 0.3, f'B = {p.box_width * 1000:.0f}',
                ha='center', fontsize=9)

        x_dim = g.cx_right + tw + 0.5
        ax.annotate('', xy=(x_dim, g.floor_y), xytext=(x_dim, g.ceiling_y),
                    arrowprops=dict(arrowstyle='<->', color='#333333', lw=1))
        ax.text(x_dim + 0.3, (g.floor_y + g.ceiling_y) / 2,
                f'H = {p.box_height * 1000:.0f}',
                rotation=90, va='center', fontsize=9)

        ax.text(g.cx_left - tw / 2, g.floor_y + 0.2,
                f'tw={tw * 1000:.0f}', rotation=90,
                ha='center', fontsize=8, color='#666666')
        ax.text(g.cx_left + 0.3, g.ceiling_y + ts / 2,
                f'ts={ts * 1000:.0f}', va='center', fontsize=8,
                color='#666666')

        ax.axvline(0, color='gray', linestyle='--', lw=0.9)
        ax.text(0, g.top_of_tunnel + 1.0, 'CL', ha='center', fontsize=9)

        ax.axhline(g.floor_y, color='#d64545', linestyle=':', lw=1)
        ax.text(g.cx_right + tw + 0.9, g.floor_y, 'FL',
                fontsize=9, color='#d64545', va='center')

        ax.axhline(g.SL, color='#9aa0a6', linestyle='--', lw=0.9)
        ax.text(g.cx_left - tw - 0.9, g.SL, 'SL',
                fontsize=9, color='#555555', va='center')

        h = p.safeheight
        for x0, sign in ((g.cx_left, +1), (g.cx_right, -1)):
            x1 = x0 + sign * min(p.sideL, p.box_width / 2 - 0.1)
            y0 = g.floor_y
            ax.plot([x0, x0, x1, x1], [y0, y0 + h, y0 + h, y0],
                    color='#9aa0a6', linestyle='--', lw=0.8)
            ax.plot([x0, x1], [y0 + h, y0], color='#9aa0a6',
                    linestyle='--', lw=0.8)
            ax.plot([x1, x0], [y0 + h, y0], color='#9aa0a6',
                    linestyle='--', lw=0.8)

    def _update_box_spec_panel(self, g):
        p = g.p
        concrete = g.outer_area - g.inner_area

        def style_txt(style, r, dx, dy):
            if style == CornerStyle.FILLET and r > 0:
                return f"R{r * 1000:.0f}"
            if style == CornerStyle.CHAMFER and dx > 0 and dy > 0:
                return f"{dx * 1000:.0f}×{dy * 1000:.0f}"
            return "직각"

        top_txt = style_txt(p.box_style_top, p.box_fillet_top_r,
                            p.box_chamfer_top_dx, p.box_chamfer_top_dy)
        bot_txt = style_txt(p.box_style_bot, p.box_fillet_bot_r,
                            p.box_chamfer_bot_dx, p.box_chamfer_bot_dy)

        self.spec_label.config(text=(
            f"내공면적 {g.inner_area:.2f}㎡  |  콘크리트 {concrete:.2f}㎡  |  "
            f"B {p.box_width:.2f} × H {p.box_height:.2f}m\n"
            f"tw {p.box_wall_t * 1000:.0f}mm  |  "
            f"ts {p.box_slab_t * 1000:.0f}mm  |  "
            f"상단 {top_txt}  |  하단 {bot_txt}  |  SL {g.SL:.2f}m"))

    # ---------------------------------------------------------------
    # DXF
    # ---------------------------------------------------------------
    def open_dxf(self):
        path = filedialog.askopenfilename(
            title="DXF 파일 선택",
            filetypes=[("DXF", "*.dxf"), ("All files", "*.*")])
        if not path:
            return
        self.dxf_path = path
        if self.dxf.load(path, force=True) is not None:
            self.update_plot()

    def save_dxf(self):
        if not self._guard_overlap("DXF 저장"):
            return
        path = filedialog.asksaveasfilename(
            title="DXF 저장", defaultextension=".dxf",
            initialfile="TUNNEL_output.dxf",
            filetypes=[("DXF", "*.dxf")])
        if not path:
            return
        try:
            self._write_dxf(path)
        except Exception as e:
            messagebox.showerror("저장 실패", str(e))
            return

        overlap_note = ""
        if self.params.kind in (TunnelType.NATM_2ARCH, TunnelType.NATM_3ARCH):
            mg = compute_multi_arch(self.params)
            info = check_multi_arch_overlap(mg)
            if info.has_overlap:
                n = len(info.pairs)
                style = self.hatch_style.get()
                style_txt = {"solid": "단색",
                             HATCH_STYLE_PATTERN: "ANSI31",
                             HATCH_STYLE_BOTH: "단색+ANSI31"}.get(style, style)
                overlap_note = (f"\n\n⚠ 겹침 {n}개소가 OVERLAP 레이어의 "
                                f"HATCH({style_txt})로 포함되었습니다.")

        messagebox.showinfo("저장 완료", path + overlap_note)

    def _write_dxf(self, path: str):
        doc = ezdxf.new(dxfversion="R2018")
        msp = doc.modelspace()

        if OVERLAP_LAYER not in doc.layers:
            doc.layers.add(OVERLAP_LAYER, color=1)

        for line in self.ax.lines:
            xs, ys = line.get_data()
            for i in range(len(xs) - 1):
                msp.add_line(start=(xs[i], ys[i]),
                             end=(xs[i + 1], ys[i + 1]))

        for patch in self.ax.patches:
            if isinstance(patch, Circle):
                msp.add_circle(center=patch.center, radius=patch.radius)
            elif isinstance(patch, Arc):
                r = patch.width / 2
                s, e = patch.theta1 % 360, patch.theta2 % 360
                if e <= s:
                    e += 360
                msp.add_arc(center=patch.center, radius=r,
                            start_angle=s, end_angle=e)
            elif isinstance(patch, MplRect):
                x, y = patch.get_xy()
                w, h = patch.get_width(), patch.get_height()
                pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
                msp.add_lwpolyline(pts, close=True)

        self._write_overlap_hatches(msp)
        doc.saveas(path)

    def _write_overlap_hatches(self, msp):
        if self.params.kind not in (TunnelType.NATM_2ARCH, TunnelType.NATM_3ARCH):
            return
        mg = compute_multi_arch(self.params)
        info = check_multi_arch_overlap(mg)
        if not info.has_overlap:
            return

        geoms = [g.polygon for g in mg.arches]
        style = self.hatch_style.get()

        for (i, j) in info.pairs:
            inter = geoms[i].intersection(geoms[j])
            if inter.is_empty:
                continue

            if style in (HATCH_STYLE_SOLID, HATCH_STYLE_BOTH):
                add_hatch_for_polygon(msp, inter, color=1, solid=True,
                                      alpha=70, layer=OVERLAP_LAYER)
            if style in (HATCH_STYLE_PATTERN, HATCH_STYLE_BOTH):
                add_hatch_for_polygon(msp, inter, color=1, solid=False,
                                      pattern=HATCH_STYLE_PATTERN,
                                      scale=0.3, alpha=70,
                                      layer=OVERLAP_LAYER)

            polys = ([inter] if inter.geom_type == "Polygon"
                     else list(getattr(inter, "geoms", [])))
            for poly in polys:
                if poly.is_empty:
                    continue
                pts = [(x, y) for x, y in poly.exterior.coords]
                if pts and pts[0] != pts[-1]:
                    pts.append(pts[0])
                msp.add_lwpolyline(pts, close=True,
                                   dxfattribs={"layer": OVERLAP_LAYER})

    # ---------------------------------------------------------------
    def close(self):
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# =============================================================================
def _fill_polygon(ax, poly, color='#d0d4da', alpha=0.5):
    xs, ys = poly.exterior.xy
    ax.fill(xs, ys, facecolor=color, edgecolor='none', alpha=alpha)


if __name__ == "__main__":
    TunnelApp().run()