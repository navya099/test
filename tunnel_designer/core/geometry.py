"""기하 계산 (NATM / Box / 다중 아치)."""
from __future__ import annotations
import math
from dataclasses import replace

import numpy as np
from shapely.geometry import LineString, Polygon
from scipy.optimize import brentq, minimize_scalar

from .constants import (
    ARC_SAMPLES, POLYGON_ARC_POINTS,
    TunnelType, CornerStyle,
)
from .models import (
    ArchParams, TunnelParams,
    TunnelGeometry, MultiArchGeometry, BoxGeometry, OverlapInfo, AlignResult,
)


# ── 공통 유틸 ────────────────────────────────────────
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
    sa = math.degrees(math.atan2(start_point[1] - center[1],
                                 start_point[0] - center[0]))
    return _polar(center, radius, sa + angle_deg)


def find_start_point(center, radius, end_point, angle_deg):
    ea = math.degrees(math.atan2(end_point[1] - center[1],
                                 end_point[0] - center[0]))
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


# ── 단일 아치 ────────────────────────────────────────
def compute_geometry_from_arch(a: ArchParams, FL: float = 0.0,
                               ts: float = 0.4, ts_slab: float = 0.4,
                               show_lining: bool = False) -> TunnelGeometry:
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
    right_arc = arc_to_linestring(right_center, a.R2,
                                  a_right - a.r2_angle, a_right)
    bottom = LineString([left_arc.coords[-1], right_arc.coords[-1]])

    coords = (list(left_arc.coords[::-1]) + list(top_arc.coords)
              + list(right_arc.coords) + list(bottom.coords[::-1]))
    polygon = Polygon(coords)

    _, sl_pt = find_extreme_x_on_arc(left_center, a.R2,
                                      a_left, a_left + a.r2_angle)

    # 외곽선 기본값
    lining_top_arc = None
    lining_left_arc = None
    lining_right_arc = None
    lining_bottom_line = None

    if show_lining and ts > 0:
        # 1. 바닥선 오프셋 (target_y)
        target_y = left_end[1] - ts_slab

        # 2. 상단 아치 오프셋 (중심 동일, 반지름 +ts)
        lining_top_arc = (center_top, a.R1 + ts, a_right, a_left)

        # 3. 좌측 아치 오프셋 (중심 동일, 반지름 +ts)
        lc_off = left_center
        lr_off = a.R2 + ts

        # 좌측 아치의 시작 각도는 상단 아치와의 접점 방향
        ang_start_L = math.degrees(math.atan2(top_start[1] - lc_off[1], top_start[0] - lc_off[0]))

        # 바닥선과의 교점을 구해 끝 각도(End Angle) 연장
        dy = target_y - lc_off[1]
        if abs(dy) <= lr_off:
            dx = math.sqrt(lr_off ** 2 - dy ** 2)
            ang_end_L = math.degrees(math.atan2(dy, -dx))  # 우측(x+) 방향 교점
        else:
            ang_end_L = ang_start_L + a.r2_angle  # 범위 초과 시 기본값
        lining_left_arc = (lc_off, lr_off, ang_start_L, ang_end_L)

        # 4. 우측 아치 오프셋
        rc_off = right_center
        rr_off = a.R2 + ts

        ang_start_R = math.degrees(math.atan2(top_end[1] - rc_off[1], top_end[0] - rc_off[0]))

        dy_r = target_y - rc_off[1]
        if abs(dy_r) <= rr_off:
            dx_r = math.sqrt(rr_off ** 2 - dy_r ** 2)
            ang_end_R = math.degrees(math.atan2(dy_r, dx_r))  # 좌측(x-) 방향 교점
        else:
            ang_end_R = ang_start_R - a.r2_angle
        lining_right_arc = (rc_off, rr_off, ang_start_R, ang_end_R)

        # 5. 바닥 오프셋선 (좌우 연장된 아치의 끝점을 연결)
        p_bot_L = _polar(lc_off, lr_off, ang_end_L)
        p_bot_R = _polar(rc_off, rr_off, ang_end_R)
        lining_bottom_line = (p_bot_L, p_bot_R)

        print(
            "LEFT SWEEP =",
            (ang_end_L - ang_start_L) % 360
        )

        print(
            "RIGHT SWEEP =",
            (ang_end_R - ang_start_R) % 360
        )
    return TunnelGeometry(
        a=a, center_top=center_top,
        left_center=left_center, right_center=right_center,
        top_start=top_start, top_end=top_end,
        left_end=left_end, right_end=right_end,
        polygon=polygon, area=polygon.area,
        SL=sl_pt[1], A=abs(left_end[0] - a.cx),
        top_of_tunnel=a.R1_Y + a.R1 - FL,
        lining_top_arc=lining_top_arc,
        lining_left_arc=lining_left_arc,
        lining_right_arc=lining_right_arc,
        lining_bottom_line=lining_bottom_line,
    )


def compute_fl_for_arch(a: ArchParams) -> float:
    a_left, a_right = a.r1_angles
    center_top = (a.cx, a.R1_Y)
    left_center, _ = find_side_center(center_top, a.R1,
                                       a_left, a_right, a.R2)
    top_start = _polar(center_top, a.R1, a_left)
    left_end = find_end_point(left_center, a.R2, top_start, a.r2_angle)
    return left_end[1]


def compute_fl(p: TunnelParams, R1_Y: float) -> float:
    a = ArchParams(R1=p.R1, top_angle=p.top_angle, R2=p.R2,
                   r2_angle=p.r2_angle, R1_Y=R1_Y, cx=0.0)
    return compute_fl_for_arch(a) - p.fl_to_culvert


def fit_R1_Y_to_FL(p: TunnelParams, tol: float = 1e-4,
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
        res = minimize_scalar(lambda y: abs(f(y)),
                              bounds=(lo, hi), method='bounded')
        return float(res.x), bool(res.success)


# ── 다중 아치 ────────────────────────────────────────
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
    return MultiArchGeometry(arches=geoms, total_area=total,
                              bbox=(min(xs), min(ys), max(xs), max(ys)),
                              layout=layout)


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
        has_overlap=bool(pairs), pairs=pairs, overlap_areas=areas,
        min_gap=min((g for _, _, g in gaps), default=float('inf')),
        gap_details=gaps,
    )


def fit_arch_R1_Y_to_FL(a: ArchParams, target_floor_y: float,
                        fl_to_culvert: float, tol: float = 1e-4,
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
        new_FL.append(compute_fl_for_arch(replace(a, R1_Y=new_y))
                      - p.fl_to_culvert)

    return AlignResult(labels=labels, old_R1Y=old_R1Y, new_R1Y=new_R1Y,
                        old_FL=old_FL, new_FL=new_FL,
                        success=success, target_FL=target_FL)


# ── Box ─────────────────────────────────────────────
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
        p, box_fillet_top_r=r_top, box_fillet_bot_r=r_bot,
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


def _box_inner_polygon(p: TunnelParams) -> list[tuple[float, float]]:
    """박스 내공 폴리곤 (LB → RB → RT → LT, 반시계)."""
    B, H = p.box_width, p.box_height
    x_L, x_R = -B / 2, B / 2
    y_B, y_T = p.FL, p.FL + H

    pts: list[tuple[float, float]] = []

    # LB (좌하단)
    if p.box_style_bot == CornerStyle.CHAMFER:
        dx, dy = p.box_chamfer_bot_dx, p.box_chamfer_bot_dy
        if dx > 0 and dy > 0:
            pts.extend([(x_L, y_B + dy), (x_L + dx, y_B)])
        else:
            pts.append((x_L, y_B))
    elif p.box_style_bot == CornerStyle.FILLET:
        pts.extend(_fillet_corner(
            (x_L, y_B), (x_R, y_B), (x_L, y_T), p.box_fillet_bot_r)[0])
    else:
        pts.append((x_L, y_B))

    # RB (우하단)
    if p.box_style_bot == CornerStyle.CHAMFER:
        dx, dy = p.box_chamfer_bot_dx, p.box_chamfer_bot_dy
        if dx > 0 and dy > 0:
            pts.extend([(x_R - dx, y_B), (x_R, y_B + dy)])
        else:
            pts.append((x_R, y_B))
    elif p.box_style_bot == CornerStyle.FILLET:
        pts.extend(_fillet_corner(
            (x_R, y_B), (x_L, y_B), (x_R, y_T), p.box_fillet_bot_r)[0])
    else:
        pts.append((x_R, y_B))

    # RT (우상단)
    if p.box_style_top == CornerStyle.CHAMFER:
        dx, dy = p.box_chamfer_top_dx, p.box_chamfer_top_dy
        if dx > 0 and dy > 0:
            pts.extend([(x_R, y_T - dy), (x_R - dx, y_T)])
        else:
            pts.append((x_R, y_T))
    elif p.box_style_top == CornerStyle.FILLET:
        pts.extend(_fillet_corner(
            (x_R, y_T), (x_R, y_B), (x_L, y_T), p.box_fillet_top_r)[0])
    else:
        pts.append((x_R, y_T))

    # LT (좌상단)
    if p.box_style_top == CornerStyle.CHAMFER:
        dx, dy = p.box_chamfer_top_dx, p.box_chamfer_top_dy
        if dx > 0 and dy > 0:
            pts.extend([(x_L + dx, y_T), (x_L, y_T - dy)])
        else:
            pts.append((x_L, y_T))
    elif p.box_style_top == CornerStyle.FILLET:
        pts.extend(_fillet_corner(
            (x_L, y_T), (x_L, y_B), (x_R, y_T), p.box_fillet_top_r)[0])
    else:
        pts.append((x_L, y_T))

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

    outer = Polygon([(x_L - tw, y_B - ts), (x_R + tw, y_B - ts),
                     (x_R + tw, y_T + ts), (x_L - tw, y_T + ts)])

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
        top_of_tunnel=y_T + ts,
        SL=y_B + p.safeheight, A=B / 2,
        fillet_arcs=fillet_arcs,
    )