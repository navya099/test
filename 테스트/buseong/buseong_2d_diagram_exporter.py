from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import ezdxf

from alignment_dxf_aligner import TrackDatum
from buseong_alternatives import AlternativeVariant, get_default_alternatives
from buseong_mass_prototype import BuseongProjectSpec


@dataclass
class Diagram2DConfig:
    grid_x: float = 7.2
    grid_y: float = 7.2
    plan_offset: Tuple[float, float] = (0.0, 0.0)
    trans_sec_offset: Tuple[float, float] = (140.0, 0.0)
    long_elev_offset: Tuple[float, float] = (270.0, 0.0)
    text_height: float = 1.3
    font_file: str = "malgun.ttf"


def _ensure_text_style(doc: ezdxf.document.Drawing, style_name: str = "KOR_STYLE", font_file: str = "malgun.ttf") -> str:
    if style_name not in doc.styles:
        try:
            doc.styles.add(style_name, font=font_file)
        except Exception:
            doc.styles.add(style_name, font="arial.ttf")
    return style_name


def _get_zones_layout(spec: BuseongProjectSpec, variant: AlternativeVariant, concourse_rel_z: float = 0.0) -> List[dict]:
    wy = variant.concourse_width_y
    pass_zone = spec.zones["여객시설"]
    staff_zone = spec.zones["역무시설"]
    util_zone = spec.zones["지원시설"]
    circ_zone = spec.zones["교통면적"]

    pass_dx = pass_zone.total_area / wy
    pass_x0 = -0.5 * pass_dx
    pass_y0 = -0.5 * wy

    staff_dx = staff_zone.total_area / wy
    staff_x0 = pass_x0 - staff_dx
    staff_y0 = pass_y0 + variant.staff_offset_y

    util_dx = util_zone.total_area / wy
    util_x0 = pass_x0 + pass_dx
    util_y0 = pass_y0 + variant.utility_offset_y

    circ_dy = circ_zone.total_area / max(pass_dx, 1.0)
    circ_y0 = pass_y0 + wy

    exp_area = spec.planned_gfa * spec.expansion_ratio
    exp_dx = exp_area / wy
    exp_x0 = util_x0 + util_dx + variant.expansion_gap_x
    exp_y0 = util_y0

    return [
        {
            "key": "여객시설",
            "label": "여객(콘코스)",
            "diag_layer": "DIAG_PASSENGER",
            "x0": pass_x0,
            "y0": pass_y0,
            "dx": pass_dx,
            "dy": wy,
            "z0": concourse_rel_z,
            "h": pass_zone.height,
        },
        {
            "key": "역무시설",
            "label": "역무클러스터",
            "diag_layer": "DIAG_STAFF",
            "x0": staff_x0,
            "y0": staff_y0,
            "dx": staff_dx,
            "dy": wy,
            "z0": concourse_rel_z,
            "h": staff_zone.height,
        },
        {
            "key": "지원시설",
            "label": "지원/설비",
            "diag_layer": "DIAG_UTILITY",
            "x0": util_x0,
            "y0": util_y0,
            "dx": util_dx,
            "dy": wy,
            "z0": concourse_rel_z,
            "h": util_zone.height,
        },
        {
            "key": "교통면적",
            "label": "교통/코어",
            "diag_layer": "DIAG_CIRCULATION",
            "x0": pass_x0,
            "y0": circ_y0,
            "dx": pass_dx,
            "dy": circ_dy,
            "z0": concourse_rel_z,
            "h": circ_zone.height,
        },
        {
            "key": "장래확장",
            "label": "장래증축(예약)",
            "diag_layer": "DIAG_EXPANSION",
            "x0": exp_x0,
            "y0": exp_y0,
            "dx": exp_dx,
            "dy": wy,
            "z0": concourse_rel_z,
            "h": pass_zone.height,
        },
    ]


def export_enhanced_2d_diagram_dxf(
    spec: BuseongProjectSpec,
    variant: AlternativeVariant,
    output_dxf: Path,
    cfg: Diagram2DConfig = Diagram2DConfig(),
    concourse_rel_z: float = 0.0,
) -> Path:
    doc = ezdxf.new(setup=True)
    msp = doc.modelspace()
    style_name = _ensure_text_style(doc, font_file=cfg.font_file)

    layer_defs = {
        "DIAG_PASSENGER": 3,
        "DIAG_STAFF": 5,
        "DIAG_UTILITY": 1,
        "DIAG_CIRCULATION": 4,
        "DIAG_ROOF": 2,
        "DIAG_INFRA": 6,
        "DIAG_EXPANSION": 7,
        "DRAW_GRID_LEVEL": 8,
        "DRAW_CUT_SEC": 7,
        "DRAW_ANNO": 7,
    }
    for lname, col in layer_defs.items():
        if lname not in doc.layers:
            doc.layers.add(name=lname, color=col)

    zones = _get_zones_layout(spec, variant, concourse_rel_z=concourse_rel_z)
    ox_p, oy_p = cfg.plan_offset
    ox_t, oy_t = cfg.trans_sec_offset
    ox_l, oy_l = cfg.long_elev_offset

    # ---------------------------------------------------------
    # 1. 2D 평면 다이어그램 (X-Y)
    # ---------------------------------------------------------
    msp.add_text(
        f"[{variant.alt_id}] 평면 조닝 & 그리드 다이어그램",
        height=cfg.text_height,
        dxfattribs={"layer": "DRAW_ANNO", "style": style_name},
    ).set_placement((ox_p, oy_p - 14.0))

    # 승강장(상대식 2개소 축약 표시) 및 연결통로 기준선
    plat_z_rel = concourse_rel_z - 5.5
    for side_x0 in (-6.0 - spec.platform_width, 6.0):
        p_rect = [
            (ox_p + side_x0, oy_p - 0.5 * spec.platform_length),
            (ox_p + side_x0 + spec.platform_width, oy_p - 0.5 * spec.platform_length),
            (ox_p + side_x0 + spec.platform_width, oy_p + 0.5 * spec.platform_length),
            (ox_p + side_x0, oy_p + 0.5 * spec.platform_length),
        ]
        msp.add_lwpolyline(p_rect, close=True, dxfattribs={"layer": "DIAG_INFRA"})

    for z in zones:
        x0, y0, dx, dy = float(z["x0"]), float(z["y0"]), float(z["dx"]), float(z["dy"])
        pts = [(ox_p + x0, oy_p + y0), (ox_p + x0 + dx, oy_p + y0), (ox_p + x0 + dx, oy_p + y0 + dy), (ox_p + x0, oy_p + y0 + dy)]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": str(z["diag_layer"])})

        # 중심 라벨
        msp.add_text(
            str(z["label"]),
            height=cfg.text_height * 0.85,
            dxfattribs={"layer": "DRAW_ANNO", "style": style_name},
        ).set_placement((ox_p + x0 + 0.5 * dx, oy_p + y0 + 0.5 * dy))

        # 모듈 그리드(기존 매스 블록 대상)
        if str(z["key"]) != "장래확장":
            nx = max(1, int(math.floor(dx / cfg.grid_x)))
            ny = max(1, int(math.floor(dy / cfg.grid_y)))
            for i in range(nx + 1):
                gx = ox_p + x0 + (i * dx / nx)
                msp.add_line((gx, oy_p + y0), (gx, oy_p + y0 + dy), dxfattribs={"layer": "DRAW_GRID_LEVEL"})
            for j in range(ny + 1):
                gy = oy_p + y0 + (j * dy / ny)
                msp.add_line((ox_p + x0, gy), (ox_p + x0 + dx, gy), dxfattribs={"layer": "DRAW_GRID_LEVEL"})

    # ---------------------------------------------------------
    # 2. 2D 횡단면도 (X-Z, 콘코스/승강장 레벨선 및 곡선 지붕)
    # ---------------------------------------------------------
    msp.add_text(
        f"[{variant.alt_id}] 횡단면도 (X-Z)",
        height=cfg.text_height,
        dxfattribs={"layer": "DRAW_ANNO", "style": style_name},
    ).set_placement((ox_t, oy_t - 14.0))

    main_zones = [z for z in zones if str(z["key"]) != "장래확장"]
    max_h = max(float(z["h"]) for z in main_zones)
    roof_z_base = concourse_rel_z + max_h + variant.roof_clearance_z

    x_min_all = min(float(z["x0"]) for z in main_zones) - variant.overhang_x
    x_max_all = max(float(z["x0"]) + float(z["dx"]) for z in main_zones) + variant.overhang_x

    # 레벨 기준선(승강장 RL, 콘코스 GL, 지붕 기준선)
    for lvl_z, lvl_name in [
        (plat_z_rel, f"승강장 EL {plat_z_rel:+.1f}m"),
        (concourse_rel_z, f"콘코스 EL {concourse_rel_z:+.1f}m"),
        (roof_z_base, f"지붕기준 EL {roof_z_base:+.1f}m"),
    ]:
        msp.add_line(
            (ox_t + x_min_all - 4.0, oy_t + lvl_z),
            (ox_t + x_max_all + 4.0, oy_t + lvl_z),
            dxfattribs={"layer": "DRAW_GRID_LEVEL"},
        )
        msp.add_text(
            lvl_name,
            height=cfg.text_height * 0.75,
            dxfattribs={"layer": "DRAW_ANNO", "style": style_name},
        ).set_placement((ox_t + x_max_all + 4.5, oy_t + lvl_z))

    # 주 단면 블록(교통면적은 후면 오프셋 표시로 구분)
    for z in main_zones:
        x0, dx, z0, h = float(z["x0"]), float(z["dx"]), float(z["z0"]), float(z["h"])
        layer_sec = "DIAG_CIRCULATION" if str(z["key"]) == "교통면적" else "DRAW_CUT_SEC"
        s_pts = [
            (ox_t + x0, oy_t + z0),
            (ox_t + x0 + dx, oy_t + z0),
            (ox_t + x0 + dx, oy_t + z0 + h),
            (ox_t + x0, oy_t + z0 + h),
        ]
        msp.add_lwpolyline(s_pts, close=True, dxfattribs={"layer": layer_sec})

    # 횡단 곡선 지붕
    arch_pts: List[Tuple[float, float]] = []
    half_x = max(0.5 * (x_max_all - x_min_all), 1e-6)
    cx_mid = 0.5 * (x_min_all + x_max_all)
    for idx in range(33):
        xl = x_min_all + (idx / 32) * (x_max_all - x_min_all)
        norm = (xl - cx_mid) / half_x
        zl = roof_z_base + variant.arch_rise * max(0.0, 1.0 - norm**2)
        arch_pts.append((ox_t + xl, oy_t + zl))
    msp.add_lwpolyline(arch_pts, close=False, dxfattribs={"layer": "DIAG_ROOF"})

    # ---------------------------------------------------------
    # 3. 2D 종단·입면도 (Y-Z)
    # ---------------------------------------------------------
    msp.add_text(
        f"[{variant.alt_id}] 종단·입면도 (Y-Z)",
        height=cfg.text_height,
        dxfattribs={"layer": "DRAW_ANNO", "style": style_name},
    ).set_placement((ox_l, oy_l - 14.0))

    y_min_all = min(float(z["y0"]) for z in main_zones) - variant.overhang_y
    y_max_all = max(float(z["y0"]) + float(z["dy"]) for z in main_zones) + variant.overhang_y

    msp.add_line(
        (ox_l + y_min_all - 3.0, oy_l + concourse_rel_z),
        (ox_l + y_max_all + 3.0, oy_l + concourse_rel_z),
        dxfattribs={"layer": "DRAW_GRID_LEVEL"},
    )

    for z in main_zones:
        y0, dy, z0, h = float(z["y0"]), float(z["dy"]), float(z["z0"]), float(z["h"])
        l_pts = [
            (ox_l + y0, oy_l + z0),
            (ox_l + y0 + dy, oy_l + z0),
            (ox_l + y0 + dy, oy_l + z0 + h),
            (ox_l + y0, oy_l + z0 + h),
        ]
        msp.add_lwpolyline(l_pts, close=True, dxfattribs={"layer": "DRAW_CUT_SEC"})

    long_arch_pts: List[Tuple[float, float]] = []
    half_y = max(0.5 * (y_max_all - y_min_all), 1e-6)
    cy_mid = 0.5 * (y_min_all + y_max_all)
    for idx in range(33):
        yl = y_min_all + (idx / 32) * (y_max_all - y_min_all)
        norm = (yl - cy_mid) / half_y
        zl = roof_z_base + (0.45 * variant.arch_rise) * max(0.0, 1.0 - norm**2)
        long_arch_pts.append((ox_l + yl, oy_l + zl))
    msp.add_lwpolyline(long_arch_pts, close=False, dxfattribs={"layer": "DIAG_ROOF"})

    output_dxf.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(output_dxf)
    return output_dxf


if __name__ == "__main__":
    spec = BuseongProjectSpec.default_buseong()
    variants = get_default_alternatives()
    out_dir = Path("output/diagrams_2d")
    for v in variants:
        p = export_enhanced_2d_diagram_dxf(spec, v, out_dir / f"{v.alt_id}_diagram_2d.dxf")
        print(f"생성 완료: {p}")