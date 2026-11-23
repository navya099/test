from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import ezdxf

from buseong_alternatives import AlternativeVariant, get_default_alternatives, validate_areas
from buseong_mass_prototype import (
    BuseongProjectSpec,
    _add_box_3d,
    _add_curved_roof_3d,
)


@dataclass
class TrackDatum:
    origin_x: float
    origin_y: float
    origin_z: float
    yaw_rad: float          # +Y(선로 진행 방향)가 월드 좌표계에서 향하는 각도(rad)
    track_gauge_offset: float = 6.0  # 선로 중심에서 좌·우 승강장 안쪽면까지 반폭(m)
    source_desc: str = "DEFAULT_ORIGIN"

    @property
    def yaw_deg(self) -> float:
        return math.degrees(self.yaw_rad)


def _extract_2d_points_from_dxf(dxf_path: Path, layer_filter: Optional[str] = None) -> List[Tuple[float, float, float]]:
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    pts: List[Tuple[float, float, float]] = []

    for ent in msp:
        if layer_filter and ent.dxf.layer.lower() != layer_filter.lower():
            continue

        dxftype = ent.dxftype()
        if dxftype == "LINE":
            s = ent.dxf.start
            e = ent.dxf.end
            pts.append((float(s.x), float(s.y), float(s.z)))
            pts.append((float(e.x), float(e.y), float(e.z)))
        elif dxftype == "LWPOLYLINE":
            elev = float(getattr(ent.dxf, "elevation", 0.0))
            for x, y, *_ in ent.get_points():
                pts.append((float(x), float(y), elev))
        elif dxftype == "POLYLINE":
            for v in ent.vertices:
                loc = v.dxf.location
                pts.append((float(loc.x), float(loc.y), float(loc.z)))

    return pts


def extract_track_datum(
    dxf_path: Optional[Path],
    layer_filter: Optional[str] = None,
    station_anchor: Optional[Tuple[float, float, float]] = None,
    default_rail_z: float = 12.0,
) -> TrackDatum:
    """
    선로 중심선 또는 승강장 DXF에서 주 방향(yaw)과 기준점(origin)을 추출.
    - station_anchor를 넘기면 선형 점군 중 해당 앵커에 가장 가까운 점을 기준점으로 사용.
    - 생략하면 점군 중심(centroid)을 기준점으로 사용.
    """
    if dxf_path is None or not dxf_path.exists():
        return TrackDatum(
            origin_x=0.0,
            origin_y=0.0,
            origin_z=default_rail_z,
            yaw_rad=0.0,
            source_desc="FALLBACK_ORIGIN",
        )

    pts = _extract_2d_points_from_dxf(dxf_path, layer_filter=layer_filter)
    if len(pts) < 2 and layer_filter:
        # 지정 레이어에 선형이 적을 경우 전체 모델스페이스로 재시도
        pts = _extract_2d_points_from_dxf(dxf_path, layer_filter=None)

    if len(pts) < 2:
        return TrackDatum(
            origin_x=0.0,
            origin_y=0.0,
            origin_z=default_rail_z,
            yaw_rad=0.0,
            source_desc=f"FALLBACK_NO_GEOM({dxf_path.name})",
        )

    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    zs = [p[2] for p in pts if abs(p[2]) > 1e-6]
    cz = (sum(zs) / len(zs)) if zs else default_rail_z

    # PCA(2x2 공분산 행렬) 주성분 벡터로 선로 주축 방향 계산
    s_xx = sum((p[0] - cx) ** 2 for p in pts) / len(pts)
    s_yy = sum((p[1] - cy) ** 2 for p in pts) / len(pts)
    s_xy = sum((p[0] - cx) * (p[1] - cy) for p in pts) / len(pts)

    trace = s_xx + s_yy
    det = s_xx * s_yy - s_xy**2
    disc = max(trace**2 - 4.0 * det, 0.0)
    lam1 = 0.5 * (trace + math.sqrt(disc))

    if abs(s_xy) > 1e-9:
        vx = lam1 - s_yy
        vy = s_xy
    else:
        vx, vy = (1.0, 0.0) if s_xx >= s_yy else (0.0, 1.0)

    # 로컬 +Y 축이 선로 진행 방향(vx, vy)과 일치하도록 yaw 계산:
    # 회전 변환: x_w = x_l * cos(yaw) - y_l * sin(yaw), y_w = x_l * sin(yaw) + y_l * cos(yaw)
    # 따라서 로컬 (0, 1) -> (-sin(yaw), cos(yaw))
    yaw_rad = math.atan2(-vx, vy)

    if station_anchor is not None:
        ax, ay, az = station_anchor
        nearest = min(pts, key=lambda p: (p[0] - ax) ** 2 + (p[1] - ay) ** 2)
        ox, oy = nearest[0], nearest[1]
        oz = az if az is not None else (nearest[2] if abs(nearest[2]) > 1e-6 else cz)
        desc = f"DXF_ANCHOR({dxf_path.name})"
    else:
        ox, oy, oz = cx, cy, cz
        desc = f"DXF_CENTROID({dxf_path.name})"

    return TrackDatum(
        origin_x=ox,
        origin_y=oy,
        origin_z=oz,
        yaw_rad=yaw_rad,
        source_desc=desc,
    )


def _to_world_3d(datum: TrackDatum, x_l: float, y_l: float, z_l: float) -> Tuple[float, float, float]:
    c = math.cos(datum.yaw_rad)
    s = math.sin(datum.yaw_rad)
    xw = datum.origin_x + (x_l * c - y_l * s)
    yw = datum.origin_y + (x_l * s + y_l * c)
    zw = datum.origin_z + z_l
    return (xw, yw, zw)


def _add_aligned_box(
    msp,
    datum: TrackDatum,
    layer: str,
    x0: float,
    y0: float,
    z0: float,
    dx: float,
    dy: float,
    dz: float,
) -> None:
    x1, y1, z1 = x0 + dx, y0 + dy, z0 + dz
    corners_local = [
        (x0, y0, z0),  # 0
        (x1, y0, z0),  # 1
        (x1, y1, z0),  # 2
        (x0, y1, z0),  # 3
        (x0, y0, z1),  # 4
        (x1, y0, z1),  # 5
        (x1, y1, z1),  # 6
        (x0, y1, z1),  # 7
    ]
    w = [_to_world_3d(datum, *p) for p in corners_local]
    faces = [
        (w[0], w[3], w[2], w[1]),
        (w[4], w[5], w[6], w[7]),
        (w[0], w[1], w[5], w[4]),
        (w[1], w[2], w[6], w[5]),
        (w[2], w[3], w[7], w[6]),
        (w[3], w[0], w[4], w[7]),
    ]
    for f in faces:
        msp.add_3dface(f, dxfattribs={"layer": layer})


def _add_aligned_roof(
    msp,
    datum: TrackDatum,
    layer: str,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    z_base: float,
    rise: float,
    nu: int,
    nv: int,
) -> None:
    cx = 0.5 * (x_min + x_max)
    half_w = max(0.5 * (x_max - x_min), 1e-6)

    grid: List[List[Tuple[float, float, float]]] = []
    for i in range(nu + 1):
        u = i / nu
        xl = x_min + u * (x_max - x_min)
        norm_x = (xl - cx) / half_w
        zl = z_base + rise * max(0.0, 1.0 - norm_x**2)
        row = []
        for j in range(nv + 1):
            v = j / nv
            yl = y_min + v * (y_max - y_min)
            row.append(_to_world_3d(datum, xl, yl, zl))
        grid.append(row)

    for i in range(nu):
        for j in range(nv):
            p1 = grid[i][j]
            p2 = grid[i + 1][j]
            p3 = grid[i + 1][j + 1]
            p4 = grid[i][j + 1]
            msp.add_3dface([p1, p2, p3, p4], dxfattribs={"layer": layer})


def build_aligned_alternative_dxf(
    spec: BuseongProjectSpec,
    variant: AlternativeVariant,
    datum: TrackDatum,
    output_dxf: Path,
    concourse_rel_z: float = 0.0,
) -> dict:
    area_report = validate_areas(spec)

    doc = ezdxf.new(setup=True)
    msp = doc.modelspace()

    layer_colors = {
        "MASS_PASSENGER": 3,
        "MASS_STAFF": 5,
        "MASS_UTILITY": 1,
        "MASS_CIRCULATION": 4,
        "ROOF_CURVE": 2,
        "INFRA_PLATFORM": 8,
        "INFRA_OVERPASS": 6,
        "EXPANSION_GHOST": 7,
    }
    for lname, col in layer_colors.items():
        if lname not in doc.layers:
            doc.layers.add(name=lname, color=col)

    # 1. 고정 인프라: 상대식 승강장 2개소(220m x 7.5m x 2) + 선상연결통로(450m2)
    plat_z0 = concourse_rel_z - 5.5
    plat_thickness = 1.1
    plat_y0 = -0.5 * spec.platform_length
    left_plat_x0 = -datum.track_gauge_offset - spec.platform_width
    right_plat_x0 = datum.track_gauge_offset

    _add_aligned_box(
        msp,
        datum,
        "INFRA_PLATFORM",
        left_plat_x0,
        plat_y0,
        plat_z0,
        spec.platform_width,
        spec.platform_length,
        plat_thickness,
    )
    _add_aligned_box(
        msp,
        datum,
        "INFRA_PLATFORM",
        right_plat_x0,
        plat_y0,
        plat_z0,
        spec.platform_width,
        spec.platform_length,
        plat_thickness,
    )

    overpass_w = 6.0
    overpass_len = spec.overpass_area / overpass_w
    _add_aligned_box(
        msp,
        datum,
        "INFRA_OVERPASS",
        left_plat_x0,
        -0.5 * overpass_len,
        concourse_rel_z - 0.6,
        overpass_w,
        overpass_len,
        0.6,
    )

    # 2. 조닝 블록 생성
    wy = variant.concourse_width_y
    pass_zone = spec.zones["여객시설"]
    staff_zone = spec.zones["역무시설"]
    util_zone = spec.zones["지원시설"]
    circ_zone = spec.zones["교통면적"]

    pass_dx = pass_zone.total_area / wy
    pass_x0 = -0.5 * pass_dx
    pass_y0 = -0.5 * wy

    _add_aligned_box(
        msp,
        datum,
        pass_zone.layer_name,
        pass_x0,
        pass_y0,
        concourse_rel_z,
        pass_dx,
        wy,
        pass_zone.height,
    )

    staff_dx = staff_zone.total_area / wy
    staff_x0 = pass_x0 - staff_dx
    _add_aligned_box(
        msp,
        datum,
        staff_zone.layer_name,
        staff_x0,
        pass_y0 + variant.staff_offset_y,
        concourse_rel_z,
        staff_dx,
        wy,
        staff_zone.height,
    )

    util_dx = util_zone.total_area / wy
    util_x0 = pass_x0 + pass_dx
    _add_aligned_box(
        msp,
        datum,
        util_zone.layer_name,
        util_x0,
        pass_y0 + variant.utility_offset_y,
        concourse_rel_z,
        util_dx,
        wy,
        util_zone.height,
    )

    circ_dy = circ_zone.total_area / max(pass_dx, 1.0)
    circ_y0 = pass_y0 + wy
    _add_aligned_box(
        msp,
        datum,
        circ_zone.layer_name,
        pass_x0,
        circ_y0,
        concourse_rel_z,
        pass_dx,
        circ_dy,
        circ_zone.height,
    )

    # 3. 곡선 지붕
    max_top_z = concourse_rel_z + max(
        pass_zone.height,
        staff_zone.height,
        util_zone.height,
        circ_zone.height,
    )
    roof_x_min = min(staff_x0, pass_x0) - variant.overhang_x
    roof_x_max = max(pass_x0 + pass_dx, util_x0 + util_dx) + variant.overhang_x
    roof_y_min = min(pass_y0, pass_y0 + variant.staff_offset_y, pass_y0 + variant.utility_offset_y) - variant.overhang_y
    roof_y_max = max(pass_y0 + wy, circ_y0 + circ_dy, pass_y0 + wy + variant.utility_offset_y) + variant.overhang_y

    _add_aligned_roof(
        msp,
        datum,
        "ROOF_CURVE",
        x_min=roof_x_min,
        x_max=roof_x_max,
        y_min=roof_y_min,
        y_max=roof_y_max,
        z_base=max_top_z + variant.roof_clearance_z,
        rise=variant.arch_rise,
        nu=spec.roof.segments_u,
        nv=spec.roof.segments_v,
    )

    # 4. 장래 증축 볼륨
    exp_area = spec.planned_gfa * spec.expansion_ratio
    exp_dx = exp_area / wy
    exp_x0 = util_x0 + util_dx + variant.expansion_gap_x
    _add_aligned_box(
        msp,
        datum,
        "EXPANSION_GHOST",
        exp_x0,
        pass_y0 + variant.utility_offset_y,
        concourse_rel_z,
        exp_dx,
        wy,
        pass_zone.height,
    )

    output_dxf.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(output_dxf)

    return {
        "alt_id": variant.alt_id,
        "title": variant.title,
        "dxf_file": str(output_dxf),
        "origin_x": round(datum.origin_x, 3),
        "origin_y": round(datum.origin_y, 3),
        "origin_z": round(datum.origin_z, 3),
        "yaw_deg": round(datum.yaw_deg, 2),
        "datum_source": datum.source_desc,
        "planned_gfa_m2": area_report["planned_gfa_m2"],
        "within_10pct_tolerance": area_report["within_10pct_tolerance"],
    }


def run_aligned_alternatives(
    alignment_dxf: Optional[Path] = None,
    layer_filter: Optional[str] = None,
    station_anchor: Optional[Tuple[float, float, float]] = None,
    out_dir: Path = Path("output/aligned_alternatives"),
) -> List[dict]:
    spec = BuseongProjectSpec.default_buseong()
    datum = extract_track_datum(
        dxf_path=alignment_dxf,
        layer_filter=layer_filter,
        station_anchor=station_anchor,
    )
    variants = get_default_alternatives()
    results = []

    for v in variants:
        out_path = out_dir / f"{v.alt_id}_aligned.dxf"
        results.append(build_aligned_alternative_dxf(spec, v, datum, out_path))

    (out_dir / "aligned_summary.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return results


if __name__ == "__main__":
    # 실제 선로/승강장 DXF가 있으면 경로와 레이어명을 지정하세요.
    # 예: alignment_dxf=Path("input/buseong_track.dxf"), layer_filter="TRACK_CL"
    summary = run_aligned_alternatives(alignment_dxf=None)
    print(json.dumps(summary, ensure_ascii=False, indent=2))