"""matplotlib 렌더링."""
from __future__ import annotations
import math

import numpy as np
from matplotlib.patches import Arc, Circle, Rectangle as MplRect
from shapely.geometry import Polygon

from core.constants import TunnelType, CornerStyle, LABEL_Y_MARGIN
from core.geometry import (
    compute_multi_arch, check_multi_arch_overlap,
    compute_fl, compute_fl_for_arch,
)
from core.models import (
    TunnelParams, TunnelGeometry, MultiArchGeometry,
    BoxGeometry,
)


def _fill_polygon(ax, poly: Polygon, color='#d0d4da', alpha=0.5):
    xs, ys = poly.exterior.xy
    ax.fill(xs, ys, facecolor=color, edgecolor='none', alpha=alpha)


# ── DXF CAD 오버레이 ─────────────────────────────────
def draw_cad(ax, entities, translate_x=0, translate_y=0):
    if not entities:
        return
    for e in entities:
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


# ── 단일 NATM ────────────────────────────────────────
def draw_single_natm(ax, g: TunnelGeometry, p: TunnelParams):
    a_left, a_right = g.a.r1_angles

    # (1) 내공 아치 그리기 (기존 유지)
    def arc_inner(c, r, s, e, color):
        if e < s:
            e += 360.0
        ax.add_patch(Arc(c, 2 * r, 2 * r, angle=0,
                         theta1=s, theta2=e, color=color, lw=1.8))

    arc_inner(g.center_top, g.a.R1, a_right, a_left, '#d64545')
    arc_inner(g.left_center, g.a.R2, a_left, a_left + g.a.r2_angle, '#2f6fed')
    arc_inner(g.right_center, g.a.R2, a_right - g.a.r2_angle, a_right, '#2b8a3e')

    # (2) ★ 외곽선(Lining) 그리기
    if p.show_lining and g.lining_top_arc:
        def arc_outer(c, r, s, e):

            sweep = (e - s) % 360

            if sweep > 180:
                s, e = e, s

            if e < s:
                e += 360

            ax.add_patch(
                Arc(
                    c,
                    2 * r,
                    2 * r,
                    theta1=s,
                    theta2=e,
                    color='#333333',
                    lw=1.5
                )
            )
        # 상단 외곽 아치
        arc_outer(*g.lining_top_arc)
        # 좌측 외곽 아치
        arc_outer(*g.lining_left_arc)
        # 우측 외곽 아치
        arc_outer(*g.lining_right_arc)

        # 하단 외곽선
        if g.lining_bottom_line:
            pL, pR = g.lining_bottom_line
            ax.plot([pL[0], pR[0]], [pL[1], pR[1]], color='#333333', lw=1.5)

            
            # 바닥 오프셋 연장 라인 표시 (선택사항 - 좌우 끝점에서 수직으로 내려오는 선)
            # ax.plot([g.left_end[0], pL[0]], [g.left_end[1], pL[1]], color='#333333', lw=1.5, ls=':')
            # ax.plot([g.right_end[0], pR[0]], [g.right_end[1], pR[1]], color='#333333', lw=1.5, ls=':')

    # 하단
    for end, side, sign in ((g.left_end, p.sideL, +1),
                            (g.right_end, p.sideR, -1)):
        x = [end[0], end[0] + sign * side, end[0] + sign * side, 0]
        y = [end[1], end[1], end[1] - p.fl_to_culvert,
             end[1] - p.fl_to_culvert]
        ax.plot(x, y, 'k-', lw=1.2)

    # 중심선
    y_text = g.top_of_tunnel + LABEL_Y_MARGIN
    for x, label in ((-p.D / 2, 'CL of 하선'),
                     (0, 'CL of 터널'),
                     (p.D / 2, 'CL of 상선')):
        ax.axvline(x, color='gray', linestyle='--', linewidth=0.9)
        ax.text(x, y_text, label, ha='center', fontsize=9, color='#555555')

    # 치수선
    for c, e in ((g.center_top, g.top_end),
                 (g.center_top, g.top_start),
                 (g.left_center, g.left_end),
                 (g.right_center, g.right_end)):
        ax.plot([c[0], e[0]], [c[1], e[1]],
                linestyle='--', color='#888888', lw=0.8)

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

    # 각도
    _draw_angle_annotation(ax, g.top_start, g.center_top, g.top_end)
    _draw_angle_annotation(ax, g.left_end, g.left_center, g.top_start)
    _draw_angle_annotation(ax, g.top_end, g.right_center, g.right_end)

    # ★ 안전박스 (파라미터 반영)
    h = p.safeheight
    for end, side, sign in ((g.left_end, p.sideL, +1),
                            (g.right_end, p.sideR, -1)):
        x0, y0 = end
        x1 = x0 + sign * side
        ax.plot([x0, x0, x1, x1], [y0, y0 + h, y0 + h, y0],
                color='#9aa0a6', linestyle='--', lw=0.9)
        ax.plot([x0, x1], [y0 + h, y0], color='#9aa0a6', linestyle='--', lw=0.9)
        ax.plot([x1, x0], [y0 + h, y0], color='#9aa0a6', linestyle='--', lw=0.9)

    # SL 라인
    ax.axhline(g.SL, color='#9aa0a6', linestyle='--', linewidth=0.9)
    ax.text(g.left_end[0] - 0.6, g.SL, 'SL',
            fontsize=9, color='#555555', va='center')


def _draw_angle_annotation(ax, p1, p2, p3, radius=1.0):
    v1 = np.array(p1) - np.array(p2)
    v2 = np.array(p3) - np.array(p2)
    cos = np.clip(v1 @ v2 / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1, 1)
    angle_deg = math.degrees(math.acos(cos))
    a1 = math.degrees(math.atan2(v1[1], v1[0]))
    a2 = math.degrees(math.atan2(v2[1], v2[0]))
    if a2 < a1:
        a2 += 360.0
    ax.add_patch(Arc(p2, 2 * radius, 2 * radius, angle=0,
                     theta1=a1, theta2=a2, color='#333333'))
    mid = math.radians((a1 + a2) / 2.0)
    ax.text(p2[0] + radius * 0.7 * math.cos(mid),
            p2[1] + radius * 0.7 * math.sin(mid),
            f'{angle_deg:.1f}°', fontsize=11, ha='center', color='#333333')


# ── 다중 아치 ────────────────────────────────────────
def draw_multi_arch(ax, mg: MultiArchGeometry, p: TunnelParams):
    palette = ['#2f6fed', '#2b8a3e', '#d64545']
    for i, (g, a) in enumerate(zip(mg.arches, mg.layout)):
        _draw_single_arch(ax, g, a, palette[i % len(palette)])

    ax.axvline(0, color='gray', linestyle='--', lw=0.9)
    ax.text(0, max(g.top_of_tunnel for g in mg.arches) + 1.2,
            'CL', ha='center', fontsize=9)
    ax.axhline(p.FL, color='#d64545', linestyle=':', lw=1)

    if p.kind == TunnelType.NATM_2ARCH:
        _draw_pillar(ax, mg, p)
    else:
        _draw_gaps(ax, mg, p)

    _draw_overlap_highlight(ax, mg)


def _draw_single_arch(ax, g: TunnelGeometry, a, color: str):
    def arc(c, r, s, e):

        sweep = (e - s) % 360

        # 항상 짧은 호 선택
        if sweep > 180:
            s, e = e, s

        if e < s:
            e += 360

        ax.add_patch(
            Arc(
                c,
                2 * r,
                2 * r,
                angle=0,
                theta1=s,
                theta2=e,
                color=color,
                lw=1.8
            )
        )

    a_left, a_right = a.r1_angles
    arc(g.center_top, a.R1, a_left, a_right)
    arc(g.left_center, a.R2, a_left, a_left + a.r2_angle)
    arc(g.right_center, a.R2, a_right - a.r2_angle, a_right)

    ax.plot([g.left_end[0], g.right_end[0]],
            [g.left_end[1], g.right_end[1]], 'k-', lw=1.2)
    ax.text(a.cx, g.top_of_tunnel + 0.4, a.label,
            ha='center', fontsize=10, color=color, fontweight='bold')


def _draw_pillar(ax, mg: MultiArchGeometry, p: TunnelParams):
    left_g, right_g = mg.arches[0], mg.arches[1]
    x_l, x_r = left_g.right_end[0], right_g.left_end[0]
    y_b = max(left_g.right_end[1], right_g.left_end[1])
    y_t = max(left_g.top_of_tunnel, right_g.top_of_tunnel)

    ax.add_patch(MplRect(
        (x_l, y_b), x_r - x_l, y_t - y_b,
        facecolor='#f0f0f0', edgecolor='#888888',
        hatch='///', alpha=0.6, linewidth=0.8))
    ax.text((x_l + x_r) / 2, y_b - 0.6,
            f'중벽 {p.pillar_w * 1000:.0f}',
            ha='center', fontsize=9, color='#666666')


def _draw_gaps(ax, mg: MultiArchGeometry, p: TunnelParams):
    central = mg.arches[0]
    left = mg.arches[1]
    right = mg.arches[2]

    def gap_arrow(x1, x2, y, label):
        ax.annotate('', xy=(x1, y), xytext=(x2, y),
                    arrowprops=dict(arrowstyle='<->', color='#333333', lw=1))
        ax.text((x1 + x2) / 2, y + 0.25, label, ha='center', fontsize=8)

    y_arrow = p.FL + 0.3
    gap_arrow(left.top_end[0], central.left_end[0],
              y_arrow, f'{p.gap_L * 1000:.0f}')
    gap_arrow(central.right_end[0], right.top_start[0],
              y_arrow, f'{p.gap_R * 1000:.0f}')


def _draw_overlap_highlight(ax, mg: MultiArchGeometry):
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
            ax.fill(xs, ys, facecolor='red', alpha=0.25,
                    edgecolor='red', linestyle='-', linewidth=1.2)
            cx, cy = poly.centroid.x, poly.centroid.y
            ax.text(cx, cy, f"겹침 {area:.2f}㎡",
                    ha='center', va='center', fontsize=9,
                    color='white', fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2",
                              facecolor="red", edgecolor="none", alpha=0.85))
    names = [f"{mg.layout[i].label}↔{mg.layout[j].label}"
             for i, j in info.pairs]
    y_top = max(g.top_of_tunnel for g in mg.arches) + 1.8
    ax.text(0, y_top, f"⚠ 아치 겹침: {', '.join(names)}",
            ha='center', fontsize=10, color='white',
            bbox=dict(boxstyle="round,pad=0.4",
                      facecolor="#d64545", edgecolor="none"))


# ── Box ─────────────────────────────────────────────
def draw_box(ax, g: BoxGeometry):
    p = g.p
    tw, ts = p.box_wall_t, p.box_slab_t

    # 1. 외곽선
    oxs, oys = g.outer.exterior.xy
    ax.plot(oxs, oys, color='#555555', lw=1.6)

    # 2. 내공 및 기둥 그리기 (MultiPolygon 대응)
    # g.inner는 Polygon 또는 MultiPolygon일 수 있음
    polygons = [g.inner] if g.inner.geom_type == 'Polygon' else list(g.inner.geoms)
    for poly in polygons:
        xs, ys = poly.exterior.xy
        ax.plot(xs, ys, color='#2f6fed', lw=2.0)
        # 내부에 구멍(interiors)이 있다면(기둥 제외 등) 구멍도 그려줌
        for interior in poly.interiors:
            hxs, hys = interior.xy
            ax.plot(hxs, hys, color='#2f6fed', lw=2.0)

    # 3. 해칭 (외곽 - 내공)
    try:
        wall_poly = g.outer.difference(g.inner)
        geoms = ([wall_poly] if wall_poly.geom_type == 'Polygon'
                 else list(wall_poly.geoms))
        for poly in geoms:
            if poly.is_empty or not poly.is_valid:
                continue
            xs, ys = poly.exterior.xy
            ax.fill(xs, ys, facecolor='#d0d4da', edgecolor='none', alpha=0.55)
            for interior in poly.interiors:
                hxs, hys = interior.xy
                ax.fill(hxs, hys, facecolor='white', edgecolor='none')  # 내부 뚫기
    except Exception as e:
        print(f"[box fill error] {e}")

    # ... (필렛 라벨, 치수선 등 기존 코드 유지) ...

    for center, r, a1, a2 in g.fillet_arcs:
        if a2 < a1:
            a2 += 360
        ax.add_patch(Arc(center, 2 * r, 2 * r, angle=0,
                         theta1=a1, theta2=a2, color='#d64545', lw=1.2))

    # 필렛 라벨
    if p.box_style_top == CornerStyle.FILLET and p.box_fillet_top_r > 0:
        ax.text(g.cx_right - p.box_fillet_top_r - 0.35,
                g.ceiling_y - p.box_fillet_top_r - 0.35,
                f'R{p.box_fillet_top_r * 1000:.0f}',
                fontsize=8, color='#d64545')
    if p.box_style_bot == CornerStyle.FILLET and p.box_fillet_bot_r > 0:
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
            f'ts={ts * 1000:.0f}', va='center', fontsize=8, color='#666666')

    ax.axvline(0, color='gray', linestyle='--', lw=0.9)
    ax.text(0, g.top_of_tunnel + 1.0, 'CL', ha='center', fontsize=9)

    ax.axhline(g.floor_y, color='#d64545', linestyle=':', lw=1)
    ax.text(g.cx_right + tw + 0.9, g.floor_y, 'FL',
            fontsize=9, color='#d64545', va='center')
    ax.axhline(g.SL, color='#9aa0a6', linestyle='--', lw=0.9)
    ax.text(g.cx_left - tw - 0.9, g.SL, 'SL',
            fontsize=9, color='#555555', va='center')

    # ★ 안전박스 (파라미터 반영)
    h = p.safeheight
    for x0, sign, side in ((g.cx_left, +1, p.sideL),
                            (g.cx_right, -1, p.sideR)):
        x1 = x0 + sign * min(side, p.box_width / 2 - 0.1)
        y0 = g.floor_y
        ax.plot([x0, x0, x1, x1], [y0, y0 + h, y0 + h, y0],
                color='#9aa0a6', linestyle='--', lw=0.8)
        ax.plot([x0, x1], [y0 + h, y0], color='#9aa0a6', linestyle='--', lw=0.8)
        ax.plot([x1, x0], [y0 + h, y0], color='#9aa0a6', linestyle='--', lw=0.8)

    # ★ 중앙 기둥 치수선 (선택)
    if p.box_columns > 0 and p.box_col_width > 0:
        # 기둥 간격에 대한 치수 표시 예시 (필요시 구현)
        pass

# ── 스펙 텍스트 (사이드 패널용) ──────────────────────
def spec_single_natm(g: TunnelGeometry, p: TunnelParams) -> str:
    new_fl = compute_fl(p, g.a.R1_Y)
    ok = abs(new_fl - p.FL) <= 0.02
    mark = "✅" if ok else "⚠️"
    return (
        f"면적 {g.area:.2f}㎡   |   A {g.A:.2f}m   |   "
        f"SL {g.SL:.2f}m   |   편평률 {g.top_of_tunnel / (g.A * 2):.2f}\n"
        f"R2/R1 {g.a.R2 / g.a.R1:.2f}   |   "
        f"FL {new_fl:.3f}m (목표 {p.FL:.3f}m)   {mark}")


def spec_multi_arch(mg: MultiArchGeometry, p: TunnelParams) -> str:
    fls = [compute_fl_for_arch(a) - p.fl_to_culvert for a in mg.layout]
    fl_spread = max(fls) - min(fls)
    unified = ("✅ 통일" if fl_spread < 0.02
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
    return "\n".join(lines)


def spec_box(g: BoxGeometry) -> str:
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

    return (
        f"내공면적 {g.inner_area:.2f}㎡  |  콘크리트 {concrete:.2f}㎡  |  "
        f"B {p.box_width:.2f} × H {p.box_height:.2f}m\n"
        f"tw {p.box_wall_t * 1000:.0f}mm  |  "
        f"ts {p.box_slab_t * 1000:.0f}mm  |  "
        f"상단 {top_txt}  |  하단 {bot_txt}  |  SL {g.SL:.2f}m")