from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import ezdxf

from alignment_dxf_aligner import TrackDatum, _to_world_3d
from buseong_alternatives import AlternativeVariant, get_default_alternatives
from buseong_mass_prototype import BuseongProjectSpec


@dataclass
class ElementBuildConfig:
    grid_x: float = 7.2
    grid_y: float = 7.2
    slab_thickness: float = 0.45
    wall_thickness: float = 0.30
    col_size: float = 0.60
    plan_z_rel: float = 1.20


def _ensure_korean_style(doc: ezdxf.document.Drawing, style_name: str = "KOREAN_TTF") -> str:
    if style_name not in doc.styles:
        doc.styles.add(style_name, font="malgun.ttf")
    return style_name


def _add_local_rect_lwpolyline(
    msp,
    datum: TrackDatum,
    layer: str,
    x0: float,
    y0: float,
    dx: float,
    dy: float,
    z_rel: float,
    closed: bool = True,
):
    pts_local = [
        (x0, y0, z_rel),
        (x0 + dx, y0, z_rel),
        (x0 + dx, y0 + dy, z_rel),
        (x0, y0 + dy, z_rel),
    ]
    pts_2d = [(_to_world_3d(datum, *p)[0], _to_world_3d(datum, *p)[1]) for p in pts_local]
    elev = _to_world_3d(datum, x0, y0, z_rel)[2]
    return msp.add_lwpolyline(pts_2d, close=closed, dxfattribs={"layer": layer, "elevation": elev})


def _add_local_column(
    msp,
    datum: TrackDatum,
    layer: str,
    cx: float,
    cy: float,
    z_bot_rel: float,
    height: float,
    col_size: float,
) -> None:
    half = 0.5 * col_size
    z_top_rel = z_bot_rel + height
    p_bot = _to_world_3d(datum, cx, cy, z_bot_rel)
    p_top = _to_world_3d(datum, cx, cy, z_top_rel)
    msp.add_line(p_bot, p_top, dxfattribs={"layer": layer})
    _add_local_rect_lwpolyline(
        msp,
        datum,
        layer,
        cx - half,
        cy - half,
        col_size,
        col_size,
        z_bot_rel,
        closed=True,
    )


def _add_local_wall_frame(
    msp,
    datum: TrackDatum,
    layer: str,
    x0: float,
    y0: float,
    dx: float,
    dy: float,
    z_bot_rel: float,
    height: float,
) -> None:
    z_top_rel = z_bot_rel + height
    corners_xy = [(x0, y0), (x0 + dx, y0), (x0 + dx, y0 + dy), (x0, y0 + dy)]
    for i in range(4):
        x_a, y_a = corners_xy[i]
        x_b, y_b = corners_xy[(i + 1) % 4]
        msp.add_line(
            _to_world_3d(datum, x_a, y_a, z_bot_rel),
            _to_world_3d(datum, x_b, y_b, z_bot_rel),
            dxfattribs={"layer": layer},
        )
        msp.add_line(
            _to_world_3d(datum, x_a, y_a, z_top_rel),
            _to_world_3d(datum, x_b, y_b, z_top_rel),
            dxfattribs={"layer": layer},
        )
        msp.add_line(
            _to_world_3d(datum, x_a, y_a, z_bot_rel),
            _to_world_3d(datum, x_a, y_a, z_top_rel),
            dxfattribs={"layer": layer},
        )


def _collect_zone_rects(
    spec: BuseongProjectSpec,
    variant: AlternativeVariant,
    concourse_rel_z: float = 0.0,
) -> List[Dict[str, float | str]]:
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

    return [
        {
            "key": "여객시설",
            "core_type": "CONCOURSE",
            "x0": pass_x0,
            "y0": pass_y0,
            "dx": pass_dx,
            "dy": wy,
            "z0": concourse_rel_z,
            "h": pass_zone.height,
        },
        {
            "key": "역무시설",
            "core_type": "CORE_VERTICAL",
            "x0": staff_x0,
            "y0": staff_y0,
            "dx": staff_dx,
            "dy": wy,
            "z0": concourse_rel_z,
            "h": staff_zone.height,
        },
        {
            "key": "지원시설",
            "core_type": "CORE_MEP",
            "x0": util_x0,
            "y0": util_y0,
            "dx": util_dx,
            "dy": wy,
            "z0": concourse_rel_z,
            "h": util_zone.height,
        },
        {
            "key": "교통면적",
            "core_type": "CORE_VERTICAL",
            "x0": pass_x0,
            "y0": circ_y0,
            "dx": pass_dx,
            "dy": circ_dy,
            "z0": concourse_rel_z,
            "h": circ_zone.height,
        },
    ]


def build_elements_and_2d_drawings(
    spec: BuseongProjectSpec,
    variant: AlternativeVariant,
    datum: TrackDatum,
    out_dir: Path,
    elem_cfg: ElementBuildConfig = ElementBuildConfig(),
    concourse_rel_z: float = 0.0,
) -> Dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rects = _collect_zone_rects(spec, variant, concourse_rel_z=concourse_rel_z)

    # ---------------------------------------------------------
    # A. 3D 부재 및 코어 구분 모델 DXF
    # ---------------------------------------------------------
    doc_3d = ezdxf.new(setup=True)
    msp_3d = doc_3d.modelspace()

    elem_layers = {
        "ELEM_SLAB": 4,
        "ELEM_WALL": 7,
        "ELEM_COLUMN": 2,
        "CORE_VERTICAL": 5,
        "CORE_MEP": 1,
        "SPACE_CONCOURSE": 3,
    }
    for lname, col in elem_layers.items():
        if lname not in doc_3d.layers:
            doc_3d.layers.add(name=lname, color=col)

    for r in rects:
        x0, y0, dx, dy, z0, h = r["x0"], r["y0"], r["dx"], r["dy"], r["z0"], r["h"]
        ctype = str(r["core_type"])

        _add_local_rect_lwpolyline(msp_3d, datum, "ELEM_SLAB", x0, y0, dx, dy, z0, closed=True)
        _add_local_rect_lwpolyline(
            msp_3d,
            datum,
            "ELEM_SLAB",
            x0,
            y0,
            dx,
            dy,
            max(z0 + h - elem_cfg.slab_thickness, z0),
            closed=True,
        )
        _add_local_wall_frame(msp_3d, datum, "ELEM_WALL", x0, y0, dx, dy, z0, h)

        nx = max(1, int(math.floor(dx / elem_cfg.grid_x)))
        ny = max(1, int(math.floor(dy / elem_cfg.grid_y)))
        xs = [x0 + (i * dx / nx) for i in range(nx + 1)]
        ys = [y0 + (j * dy / ny) for j in range(ny + 1)]
        for gx in xs:
            for gy in ys:
                _add_local_column(
                    msp_3d,
                    datum,
                    "ELEM_COLUMN",
                    gx,
                    gy,
                    z0,
                    h,
                    elem_cfg.col_size,
                )

        target_layer = ctype if ctype != "CONCOURSE" else "SPACE_CONCOURSE"
        _add_local_rect_lwpolyline(
            msp_3d,
            datum,
            target_layer,
            x0 + 0.25,
            y0 + 0.25,
            max(dx - 0.5, 0.5),
            max(dy - 0.5, 0.5),
            z0 + 0.1,
            closed=True,
        )

    elements_dxf_path = out_dir / f"{variant.alt_id}_elements_cores.dxf"
    doc_3d.saveas(elements_dxf_path)

    # ---------------------------------------------------------
    # B. 2D 평면도 / 횡단면도 / 종단·입면도 DXF
    # ---------------------------------------------------------
    doc_2d = ezdxf.new(setup=True)
    msp_2d = doc_2d.modelspace()
    kor_style = _ensure_korean_style(doc_2d)

    view_layers = {
        "VIEW_PLAN_2D": 3,
        "VIEW_CORE_2D": 5,
        "VIEW_GRID_2D": 8,
        "VIEW_SEC_TRANS_2D": 1,
        "VIEW_SEC_LONG_2D": 6,
        "VIEW_ROOF_2D": 2,
        "VIEW_TEXT_2D": 7,
    }
    for lname, col in view_layers.items():
        if lname not in doc_2d.layers:
            doc_2d.layers.add(name=lname, color=col)

    plan_offset = (0.0, 0.0)
    trans_sec_offset = (120.0, 0.0)
    long_elev_offset = (230.0, 0.0)

    msp_2d.add_text(
        f"[{variant.alt_id}] 2D 평면도 (X-Y)",
        height=1.2,
        dxfattribs={"layer": "VIEW_TEXT_2D", "style": kor_style},
    ).set_placement((plan_offset[0], plan_offset[1] - 12.0))

    msp_2d.add_text(
        f"[{variant.alt_id}] 2D 횡단면도 (X-Z)",
        height=1.2,
        dxfattribs={"layer": "VIEW_TEXT_2D", "style": kor_style},
    ).set_placement((trans_sec_offset[0], trans_sec_offset[1] - 12.0))

    msp_2d.add_text(
        f"[{variant.alt_id}] 2D 종단·입면도 (Y-Z)",
        height=1.2,
        dxfattribs={"layer": "VIEW_TEXT_2D", "style": kor_style},
    ).set_placement((long_elev_offset[0], long_elev_offset[1] - 12.0))

    # 1) 평면도(X-Y)
    for r in rects:
        x0, y0, dx, dy = float(r["x0"]), float(r["y0"]), float(r["dx"]), float(r["dy"])
        ctype = str(r["core_type"])
        px0, py0 = plan_offset[0] + x0, plan_offset[1] + y0

        pts = [(px0, py0), (px0 + dx, py0), (px0 + dx, py0 + dy), (px0, py0 + dy)]
        msp_2d.add_lwpolyline(pts, close=True, dxfattribs={"layer": "VIEW_PLAN_2D"})

        if ctype in ("CORE_VERTICAL", "CORE_MEP"):
            msp_2d.add_lwpolyline(pts, close=True, dxfattribs={"layer": "VIEW_CORE_2D"})

        nx = max(1, int(math.floor(dx / elem_cfg.grid_x)))
        ny = max(1, int(math.floor(dy / elem_cfg.grid_y)))
        for i in range(nx + 1):
            gx = px0 + (i * dx / nx)
            msp_2d.add_line((gx, py0), (gx, py0 + dy), dxfattribs={"layer": "VIEW_GRID_2D"})
        for j in range(ny + 1):
            gy = py0 + (j * dy / ny)
            msp_2d.add_line((px0, gy), (px0 + dx, gy), dxfattribs={"layer": "VIEW_GRID_2D"})

    # 2) 횡단면도(X-Z): X축 구간별로 가장 높은 상부선과 코어 구분선만 깔끔하게 표현
    max_h = max(float(r["h"]) for r in rects)
    roof_z_base = concourse_rel_z + max_h + variant.roof_clearance_z
    x_all_min = min(float(r["x0"]) for r in rects) - variant.overhang_x
    x_all_max = max(float(r["x0"]) + float(r["dx"]) for r in rects) + variant.overhang_x

    # 승강장 기준선(상대식 2개소 레벨)
    plat_z = concourse_rel_z - 5.5
    msp_2d.add_line(
        (trans_sec_offset[0] + x_all_min, trans_sec_offset[1] + plat_z),
        (trans_sec_offset[0] + x_all_max, trans_sec_offset[1] + plat_z),
        dxfattribs={"layer": "VIEW_GRID_2D"},
    )

    # X 구간별 블록 윤곽(중복 블록은 코어/주매스 구분선으로만 표시)
    for r in rects:
        x0, dx, z0, h = float(r["x0"]), float(r["dx"]), float(r["z0"]), float(r["h"])
        sx0 = trans_sec_offset[0] + x0
        sz0 = trans_sec_offset[1] + z0
        rect_pts = [(sx0, sz0), (sx0 + dx, sz0), (sx0 + dx, sz0 + h), (sx0, sz0 + h)]
        if str(r["key"]) == "교통면적":
            # 교통면적은 후면(+Y) 배치 블록이므로 점선/코어 레이어로만 외곽 표시
            msp_2d.add_lwpolyline(rect_pts, close=True, dxfattribs={"layer": "VIEW_CORE_2D"})
        else:
            msp_2d.add_lwpolyline(rect_pts, close=True, dxfattribs={"layer": "VIEW_SEC_TRANS_2D"})

    arch_pts: List[Tuple[float, float]] = []
    half_span = max(0.5 * (x_all_max - x_all_min), 1e-6)
    cx_local = 0.5 * (x_all_min + x_all_max)
    for s_idx in range(25):
        xl = x_all_min + (s_idx / 24) * (x_all_max - x_all_min)
        norm_x = (xl - cx_local) / half_span
        zl = roof_z_base + variant.arch_rise * max(0.0, 1.0 - norm_x**2)
        arch_pts.append((trans_sec_offset[0] + xl, trans_sec_offset[1] + zl))
    msp_2d.add_lwpolyline(arch_pts, close=False, dxfattribs={"layer": "VIEW_ROOF_2D"})

    # 3) 종단·입면도(Y-Z): Y축 구간별 입면 블록 + 완만한 곡선 지붕 실루엣
    for r in rects:
        y0, dy, z0, h = float(r["y0"]), float(r["dy"]), float(r["z0"]), float(r["h"])
        ly0 = long_elev_offset[0] + y0
        lz0 = long_elev_offset[1] + z0
        rect_pts = [(ly0, lz0), (ly0 + dy, lz0), (ly0 + dy, lz0 + h), (ly0, lz0 + h)]
        msp_2d.add_lwpolyline(rect_pts, close=True, dxfattribs={"layer": "VIEW_SEC_LONG_2D"})

    y_all_min = min(float(r["y0"]) for r in rects) - variant.overhang_y
    y_all_max = max(float(r["y0"]) + float(r["dy"]) for r in rects) + variant.overhang_y
    half_y = max(0.5 * (y_all_max - y_all_min), 1e-6)
    cy_local = 0.5 * (y_all_min + y_all_max)
    long_roof_pts: List[Tuple[float, float]] = []
    for s_idx in range(25):
        yl = y_all_min + (s_idx / 24) * (y_all_max - y_all_min)
        norm_y = (yl - cy_local) / half_y
        zl = roof_z_base + (0.4 * variant.arch_rise) * max(0.0, 1.0 - norm_y**2)
        long_roof_pts.append((long_elev_offset[0] + yl, long_elev_offset[1] + zl))
    msp_2d.add_lwpolyline(long_roof_pts, close=False, dxfattribs={"layer": "VIEW_ROOF_2D"})

    drawings_2d_path = out_dir / f"{variant.alt_id}_plan_section_elevation_2d.dxf"
    doc_2d.saveas(drawings_2d_path)

    return {
        "elements_3d_dxf": elements_dxf_path,
        "drawings_2d_dxf": drawings_2d_path,
    }


if __name__ == "__main__":
    spec = BuseongProjectSpec.default_buseong()
    variants = get_default_alternatives()
    datum = TrackDatum(
        origin_x=213076.336,
        origin_y=472130.393,
        origin_z=12.0,
        yaw_rad=math.radians(-170.79),
        source_desc="BUSEONG_36701066_A0151111",
    )

    out_root = Path("output/elements_and_2d")
    for v in variants:
        paths = build_elements_and_2d_drawings(spec, v, datum, out_root / v.alt_id)
        print(v.alt_id, "->", {k: str(val) for k, val in paths.items()})