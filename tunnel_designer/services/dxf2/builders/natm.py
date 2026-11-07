"""NATM 단일 아치 DXF 빌더 (draw_single_natm 로직 이식)."""
from __future__ import annotations
import math

from core.constants import TunnelType
from core.models import TunnelParams, ArchParams
from core.geometry import compute_geometry_from_arch
from services.dxf2.document import DocumentParams
from services.dxf2.layers import (
    LAYER_TUNNEL, LAYER_CONCRETE, LAYER_CENTERLINE, LAYER_HIDL,
    LAYER_TEXT, LAYER_RAIL, LAYER_SAFE, LAYER_DIM,
    STYLE_T25, STYLE_T35, HEIGHT_T25, HEIGHT_T35,
)
from services.dxf2.engine import (
    dim_horizontal, dim_vertical, text_std,
)
from services.dxf2.registry import register


# ═══════════════════════════════════════════════════════════
# 좌표 변환
# ═══════════════════════════════════════════════════════════
def _t(pt: tuple[float, float], d: DocumentParams) -> tuple[float, float]:
    """터널 좌표(m) → 도면 좌표(mm)."""
    return (
        pt[0] * 1000.0 + d.base_x,
        pt[1] * 1000.0 + d.base_y,
    )


def _len(v_m: float) -> float:
    """m 단위 길이 → 도면 mm."""
    return v_m * 1000.0


def _add_arc(msp, center, radius, start_deg, end_deg,
             layer: str, linetype: str | None = None):
    """DXF ARC (반시계 보장)."""
    if end_deg < start_deg:
        end_deg += 360.0
    attribs = {"layer": layer}
    if linetype:
        attribs["linetype"] = linetype
    msp.add_arc(
        center=center, radius=radius,
        start_angle=start_deg, end_angle=end_deg,
        dxfattribs=attribs,
    )


def _add_line(msp, p1, p2, layer: str, linetype: str | None = None):
    attribs = {"layer": layer}
    if linetype:
        attribs["linetype"] = linetype
    msp.add_line(p1, p2, dxfattribs=attribs)


def _add_polyline(msp, pts, layer: str, closed: bool = False):
    msp.add_lwpolyline(
        pts, close=closed,
        dxfattribs={"layer": layer},
    )


# ═══════════════════════════════════════════════════════════
# 메인 빌더 (draw_single_natm 이식)
# ═══════════════════════════════════════════════════════════
@register(TunnelType.NATM)
def build_natm(msp, params: TunnelParams, doc_params: DocumentParams, doc):
    p = params
    d = doc_params

    a = ArchParams(
        R1=p.R1, top_angle=p.top_angle,
        R2=p.R2, r2_angle=p.r2_angle,
        R1_Y=p.R1_Y, cx=0.0, label="본선",
    )
    g = compute_geometry_from_arch(
        a, FL=p.FL,
        ts=p.ts, ts_slab=p.ts_slab,
        show_lining=p.show_lining,
    )
    a_left, a_right = a.r1_angles

    # ═══════════════════════════════════════════════════════
    # (1) 내공 아치 3개 (CR-TUNL)
    # ═══════════════════════════════════════════════════════
    _add_arc(msp, _t(g.center_top, d), _len(a.R1),
             a_right, a_left, LAYER_TUNNEL)       # 상단 R1
    _add_arc(msp, _t(g.left_center, d), _len(a.R2),
             a_left, a_left + a.r2_angle, LAYER_TUNNEL)  # 좌 R2
    _add_arc(msp, _t(g.right_center, d), _len(a.R2),
             a_right - a.r2_angle, a_right, LAYER_TUNNEL)  # 우 R2

    # ═══════════════════════════════════════════════════════
    # (2) 라이닝 외곽 (CS-CONC-MAJR)
    # ═══════════════════════════════════════════════════════
    if p.show_lining and g.lining_top_arc is not None:
        def _add_outer_arc(arc_tuple):
            c, r, s, e = arc_tuple
            sweep = (e - s) % 360
            if sweep > 180:
                s, e = e, s
            if e < s:
                e += 360
            _add_arc(msp, _t(c, d), _len(r), s, e, LAYER_CONCRETE)

        _add_outer_arc(g.lining_top_arc)
        _add_outer_arc(g.lining_left_arc)
        _add_outer_arc(g.lining_right_arc)

        if g.lining_bottom_line:
            pL, pR = g.lining_bottom_line
            _add_line(msp, _t(pL, d), _t(pR, d), LAYER_CONCRETE)

    # ═══════════════════════════════════════════════════════
    # (3) 하단 수평 계단식 (내공 → fl_to_culvert 아래)
    # ═══════════════════════════════════════════════════════
    for end, side, sign in ((g.left_end, p.sideL, +1),
                            (g.right_end, p.sideR, -1)):
        x = [
            end[0],
            end[0] + sign * side,
            end[0] + sign * side,
            0.0,
        ]
        y = [
            end[1],
            end[1],
            end[1] - p.fl_to_culvert,
            end[1] - p.fl_to_culvert,
        ]
        pts = [_t((x[i], y[i]), d) for i in range(len(x))]
        _add_polyline(msp, pts, LAYER_TUNNEL)

    # ═══════════════════════════════════════════════════════
    # (4) 트랙 CL + 터널 CL 라벨
    # ═══════════════════════════════════════════════════════
    y_text = g.top_of_tunnel + 0.5
    for t in p.get_tracks():
        x = t.offset_x
        # 트랙 CL 수직선
        _add_line(
            msp,
            _t((x, p.FL - 1.5), d),
            _t((x, y_text), d),
            LAYER_CENTERLINE,
            linetype="CENTER",
        )
        # 트랙 라벨
        text_std(
            msp,
            *_t((x, y_text + 0.3), d),
            s=f"C {t.label or 'T'}",
            style=STYLE_T25, height=HEIGHT_T25,
            layer=LAYER_TEXT,
        )

    # 터널 중심 CL 라벨
    text_std(
        msp,
        *_t((0, y_text + 0.3), d),
        s="C 터널",
        style=STYLE_T25, height=HEIGHT_T25,
        layer=LAYER_TEXT,
    )

    # ═══════════════════════════════════════════════════════
    # (5) R1/R2 지름선 + 반경 텍스트
    # ═══════════════════════════════════════════════════════
    # R1 (상단 아치 반지름) - 좌우 지름선
    for end_pt, ang in ((g.top_start, a_left), (g.top_end, a_right)):
        _add_line(
            msp,
            _t(g.center_top, d), _t(end_pt, d),
            LAYER_DIM,
            linetype="DASHED",
        )
        mid = (
            (g.center_top[0] + end_pt[0]) / 2,
            (g.center_top[1] + end_pt[1]) / 2,
        )
        text_std(
            msp,
            *_t((mid[0] - 0.3, mid[1] + 0.3), d),
            s=f"R1={a.R1 * 1000:.0f}",
            style=STYLE_T25, height=HEIGHT_T25,
            layer=LAYER_TEXT,
            rotation=ang,
        )

    # R2 (좌/우 아치 반지름)
    for center, end_pt in ((g.left_center, g.left_end),
                           (g.right_center, g.right_end)):
        _add_line(
            msp,
            _t(center, d), _t(end_pt, d),
            LAYER_DIM,
            linetype="DASHED",
        )
        mid = ((center[0] + end_pt[0]) / 2, (center[1] + end_pt[1]) / 2)
        rot = math.degrees(math.atan2(end_pt[1] - center[1],
                                       end_pt[0] - center[0]))
        text_std(
            msp,
            *_t(mid, d),
            s=f"R2={a.R2 * 1000:.0f}",
            style=STYLE_T25, height=HEIGHT_T25,
            layer=LAYER_TEXT,
            rotation=rot,
        )

    # ═══════════════════════════════════════════════════════
    # (6) 안전박스 (X자 사각형)
    # ═══════════════════════════════════════════════════════
    h = p.safeheight
    for end, side, sign in ((g.left_end, p.sideL, +1),
                            (g.right_end, p.sideR, -1)):
        x0, y0 = end
        x1 = x0 + sign * side
        # 사각형 외곽
        rect_pts = [
            _t((x0, y0), d),
            _t((x0, y0 + h), d),
            _t((x1, y0 + h), d),
            _t((x1, y0), d),
            _t((x0, y0), d),
        ]
        _add_polyline(msp, rect_pts, LAYER_HIDL)
        # X자
        _add_line(msp, _t((x0, y0), d), _t((x1, y0 + h), d), LAYER_CENTERLINE)
        _add_line(msp, _t((x1, y0), d), _t((x0, y0 + h), d), LAYER_CENTERLINE)

    # ═══════════════════════════════════════════════════════
    # (7) SL 라인
    # ═══════════════════════════════════════════════════════
    sl_x_left = g.left_end[0] - 0.5
    sl_x_right = g.right_end[0] + 0.5
    _add_line(
        msp,
        _t((sl_x_left, g.SL), d),
        _t((sl_x_right, g.SL), d),
        LAYER_HIDL,
    )
    text_std(
        msp,
        *_t((sl_x_left - 0.3, g.SL), d),
        s="S.L",
        style=STYLE_T25, height=HEIGHT_T25,
        layer=LAYER_TEXT,
    )

    # ═══════════════════════════════════════════════════════
    # (8) FL / RL 라벨
    # ═══════════════════════════════════════════════════════
    lbl_x = g.right_end[0] + 0.8
    text_std(
        msp,
        *_t((lbl_x, p.FL), d),
        s="F.L",
        style=STYLE_T25, height=HEIGHT_T25,
        layer=LAYER_TEXT,
    )
    text_std(
        msp,
        *_t((lbl_x, p.RL), d),
        s="R.L",
        style=STYLE_T25, height=HEIGHT_T25,
        layer=LAYER_TEXT,
    )

    # ═══════════════════════════════════════════════════════
    # (9) 치수선 (표준 DIMENSION)
    # ═══════════════════════════════════════════════════════
    # 트랙 CL 간격
    tracks = sorted(p.get_tracks(), key=lambda t: t.offset_x)
    y_dim = g.top_of_tunnel + 1.5
    for i in range(len(tracks) - 1):
        t1, t2 = tracks[i], tracks[i + 1]
        gap_mm = (t2.offset_x - t1.offset_x) * 1000.0
        dim_horizontal(
            msp,
            _t((t1.offset_x, 0), d)[0],
            _t((t2.offset_x, 0), d)[0],
            _t((0, y_dim), d)[1],
            override_text=f"{gap_mm:.0f}",
        )

    # 내공 폭 치수
    dim_horizontal(
        msp,
        _t(g.left_end, d)[0],
        _t(g.right_end, d)[0],
        _t((0, p.FL - 1.2), d)[1],
        override_text=f"{abs(g.right_end[0] - g.left_end[0]) * 1000:.0f}",
    )

    return msp