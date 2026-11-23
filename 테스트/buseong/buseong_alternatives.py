from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from buseong_mass_prototype import (
    BuseongProjectSpec,
    _add_box_3d,
    _add_curved_roof_3d,
    validate_areas,
)
import ezdxf


@dataclass
class AlternativeVariant:
    alt_id: str
    title: str
    concourse_width_y: float
    roof_clearance_z: float
    arch_rise: float
    overhang_x: float
    overhang_y: float
    staff_offset_y: float
    utility_offset_y: float
    expansion_gap_x: float


def get_default_alternatives() -> List[AlternativeVariant]:
    return [
        AlternativeVariant(
            alt_id="ALT-01",
            title="선형 통합 브릿지형",
            concourse_width_y=16.0,
            roof_clearance_z=1.2,
            arch_rise=3.6,
            overhang_x=3.5,
            overhang_y=4.5,
            staff_offset_y=0.0,
            utility_offset_y=0.0,
            expansion_gap_x=4.0,
        ),
        AlternativeVariant(
            alt_id="ALT-02",
            title="교차·분절 랜드마크형",
            concourse_width_y=14.0,
            roof_clearance_z=1.6,
            arch_rise=5.2,
            overhang_x=4.5,
            overhang_y=5.5,
            staff_offset_y=-3.0,
            utility_offset_y=3.0,
            expansion_gap_x=5.0,
        ),
        AlternativeVariant(
            alt_id="ALT-03",
            title="확장 연계·광폭형",
            concourse_width_y=20.0,
            roof_clearance_z=1.2,
            arch_rise=3.0,
            overhang_x=3.0,
            overhang_y=4.0,
            staff_offset_y=1.5,
            utility_offset_y=-1.5,
            expansion_gap_x=3.0,
        ),
    ]


def build_alternative_dxf(
    spec: BuseongProjectSpec,
    variant: AlternativeVariant,
    output_dxf: Path,
    concourse_z0: float = 12.0,
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

    # 1. 고정 인프라(상대식 승강장 2개소 + 선상연결통로)
    plat_z0 = concourse_z0 - 5.5
    plat_thickness = 1.1
    plat_y0 = -0.5 * spec.platform_length
    left_plat_x0 = -6.0 - spec.platform_width
    right_plat_x0 = 6.0

    _add_box_3d(
        msp,
        "INFRA_PLATFORM",
        left_plat_x0,
        plat_y0,
        plat_z0,
        spec.platform_width,
        spec.platform_length,
        plat_thickness,
    )
    _add_box_3d(
        msp,
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
    _add_box_3d(
        msp,
        "INFRA_OVERPASS",
        left_plat_x0,
        -0.5 * overpass_len,
        concourse_z0 - 0.6,
        overpass_w,
        overpass_len,
        0.6,
    )

    # 2. 조닝 블록 생성(대안별 오프셋/폭 반영)
    wy = variant.concourse_width_y
    pass_zone = spec.zones["여객시설"]
    staff_zone = spec.zones["역무시설"]
    util_zone = spec.zones["지원시설"]
    circ_zone = spec.zones["교통면적"]

    pass_dx = pass_zone.total_area / wy
    pass_x0 = -0.5 * pass_dx
    pass_y0 = -0.5 * wy

    _add_box_3d(
        msp,
        pass_zone.layer_name,
        pass_x0,
        pass_y0,
        concourse_z0,
        pass_dx,
        wy,
        pass_zone.height,
    )

    staff_dx = staff_zone.total_area / wy
    staff_x0 = pass_x0 - staff_dx
    _add_box_3d(
        msp,
        staff_zone.layer_name,
        staff_x0,
        pass_y0 + variant.staff_offset_y,
        concourse_z0,
        staff_dx,
        wy,
        staff_zone.height,
    )

    util_dx = util_zone.total_area / wy
    util_x0 = pass_x0 + pass_dx
    _add_box_3d(
        msp,
        util_zone.layer_name,
        util_x0,
        pass_y0 + variant.utility_offset_y,
        concourse_z0,
        util_dx,
        wy,
        util_zone.height,
    )

    circ_dy = circ_zone.total_area / max(pass_dx, 1.0)
    circ_y0 = pass_y0 + wy
    _add_box_3d(
        msp,
        circ_zone.layer_name,
        pass_x0,
        circ_y0,
        concourse_z0,
        pass_dx,
        circ_dy,
        circ_zone.height,
    )

    # 3. 곡선 지붕(최상단 매스 + roof_clearance_z 만큼 이격)
    max_top_z = concourse_z0 + max(
        pass_zone.height,
        staff_zone.height,
        util_zone.height,
        circ_zone.height,
    )
    roof_x_min = min(staff_x0, pass_x0) - variant.overhang_x
    roof_x_max = max(pass_x0 + pass_dx, util_x0 + util_dx) + variant.overhang_x
    roof_y_min = min(pass_y0, pass_y0 + variant.staff_offset_y, pass_y0 + variant.utility_offset_y) - variant.overhang_y
    roof_y_max = max(pass_y0 + wy, circ_y0 + circ_dy, pass_y0 + wy + variant.utility_offset_y) + variant.overhang_y

    _add_curved_roof_3d(
        msp,
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

    # 4. 장래 증축 매스
    exp_area = spec.planned_gfa * spec.expansion_ratio
    exp_dx = exp_area / wy
    exp_x0 = util_x0 + util_dx + variant.expansion_gap_x
    _add_box_3d(
        msp,
        "EXPANSION_GHOST",
        exp_x0,
        pass_y0 + variant.utility_offset_y,
        concourse_z0,
        exp_dx,
        wy,
        pass_zone.height,
    )

    output_dxf.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(output_dxf)

    span_x = round((roof_x_max - roof_x_min), 2)
    span_y = round((roof_y_max - roof_y_min), 2)
    max_roof_z = round(max_top_z + variant.roof_clearance_z + variant.arch_rise, 2)

    return {
        "alt_id": variant.alt_id,
        "title": variant.title,
        "dxf_file": str(output_dxf),
        "planned_gfa_m2": area_report["planned_gfa_m2"],
        "within_10pct_tolerance": area_report["within_10pct_tolerance"],
        "concourse_width_y_m": wy,
        "roof_clearance_z_m": variant.roof_clearance_z,
        "arch_rise_m": variant.arch_rise,
        "max_roof_elevation_m": max_roof_z,
        "envelope_span_x_m": span_x,
        "envelope_span_y_m": span_y,
    }


def generate_all_alternatives(out_dir: Path = Path("output/alternatives")) -> List[dict]:
    spec = BuseongProjectSpec.default_buseong()
    variants = get_default_alternatives()
    rows: List[dict] = []

    for v in variants:
        dxf_path = out_dir / f"{v.alt_id}_buseong.dxf"
        row = build_alternative_dxf(spec, v, dxf_path)
        rows.append(row)

    json_path = out_dir / "alternatives_summary.json"
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_path = out_dir / "alternatives_summary.csv"
    if rows:
        with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    return rows


if __name__ == "__main__":
    summary_rows = generate_all_alternatives()
    print(json.dumps(summary_rows, ensure_ascii=False, indent=2))