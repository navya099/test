from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import List, Optional, Tuple

import ezdxf
import geopandas as gpd
from shapely.geometry import LineString, box

from alignment_dxf_aligner import TrackDatum, build_aligned_alternative_dxf
from buseong_alternatives import get_default_alternatives
from buseong_mass_prototype import BuseongProjectSpec
from ngii_track_loader import find_5k_sheets_by_tm_bbox


def extract_2d_polyline_track_datum_from_dxf(
    dxf_path: str | Path,
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    layer_name: str = "A0151111",
    boundary_dxf_path: Optional[str | Path] = None,
    default_rail_z: float = 12.0,
) -> TrackDatum:
    """
    DXF 수치지도에서 지정 레이어(기본 'A0151111')의 2D 폴리선(LWPOLYLINE / 2D POLYLINE)을 읽어
    부지 영역(폴리곤 또는 TM BBOX) 내 선형으로 TrackDatum(기준점, 선로 방위각)을 산출합니다.
    """
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    # 클리핑용 폴리곤 구성(부지 경계 DXF가 있으면 폴리곤 사용, 없으면 TM BBOX 사용)
    clip_poly = box(min_x, min_y, max_x, max_y)
    if boundary_dxf_path and Path(boundary_dxf_path).exists():
        b_doc = ezdxf.readfile(boundary_dxf_path)
        b_msp = b_doc.modelspace()
        for ent in b_msp:
            if ent.dxftype() == "LWPOLYLINE" and ent.closed:
                b_pts = [(float(p[0]), float(p[1])) for p in ent.get_points()]
                if len(b_pts) >= 3:
                    from shapely.geometry import Polygon
                    poly = Polygon(b_pts)
                    if poly.is_valid and not poly.is_empty:
                        clip_poly = poly
                        break

    collected_coords: List[Tuple[float, float, float]] = []

    for ent in msp:
        if ent.dxf.layer.strip().upper() != layer_name.strip().upper():
            continue

        dxftype = ent.dxftype()
        raw_xy: List[Tuple[float, float]] = []

        if dxftype == "LWPOLYLINE":
            raw_xy = [(float(p[0]), float(p[1])) for p in ent.get_points()]
        elif dxftype == "POLYLINE" and not ent.is_3d_polyline:
            raw_xy = [
                (float(v.dxf.location.x), float(v.dxf.location.y))
                for v in ent.vertices
            ]

        if len(raw_xy) < 2:
            continue

        line = LineString(raw_xy)
        clipped_geom = line.intersection(clip_poly)
        if clipped_geom.is_empty:
            continue

        parts = (
            list(clipped_geom.geoms)
            if hasattr(clipped_geom, "geoms")
            else [clipped_geom]
        )
        for part in parts:
            if isinstance(part, LineString) and len(part.coords) >= 2:
                for x, y in part.coords:
                    collected_coords.append((float(x), float(y), default_rail_z))

    if len(collected_coords) < 2:
        return TrackDatum(
            origin_x=0.5 * (min_x + max_x),
            origin_y=0.5 * (min_y + max_y),
            origin_z=default_rail_z,
            yaw_rad=0.0,
            source_desc=f"FALLBACK_NO_2DPOLY_IN_BOUNDS({layer_name})",
        )

    cx = sum(p[0] for p in collected_coords) / len(collected_coords)
    cy = sum(p[1] for p in collected_coords) / len(collected_coords)

    s_xx = sum((p[0] - cx) ** 2 for p in collected_coords) / len(collected_coords)
    s_yy = sum((p[1] - cy) ** 2 for p in collected_coords) / len(collected_coords)
    s_xy = sum((p[0] - cx) * (p[1] - cy) for p in collected_coords) / len(collected_coords)

    trace = s_xx + s_yy
    det = s_xx * s_yy - s_xy**2
    lam1 = 0.5 * (trace + math.sqrt(max(trace**2 - 4.0 * det, 0.0)))

    if abs(s_xy) > 1e-9:
        vx = lam1 - s_yy
        vy = s_xy
    else:
        vx, vy = (1.0, 0.0) if s_xx >= s_yy else (0.0, 1.0)

    yaw_rad = math.atan2(-vx, vy)

    return TrackDatum(
        origin_x=cx,
        origin_y=cy,
        origin_z=default_rail_z,
        yaw_rad=yaw_rad,
        source_desc=f"NGII_DXF_2DPOLY({Path(dxf_path).name}:{layer_name})",
    )


def run_buseong_dxf_pipeline(
    ngii_dxf_path: str | Path,
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    index_shp_path: Optional[str | Path] = None,
    boundary_dxf_path: Optional[str | Path] = None,
    layer_name: str = "A0151111",
    default_rail_z: float = 12.0,
    out_dir: Path = Path("output/buseong_dxf_run"),
) -> List[dict]:
    if index_shp_path and Path(index_shp_path).exists():
        find_5k_sheets_by_tm_bbox(index_shp_path, min_x, min_y, max_x, max_y)

    datum = extract_2d_polyline_track_datum_from_dxf(
        dxf_path=ngii_dxf_path,
        min_x=min_x,
        min_y=min_y,
        max_x=max_x,
        max_y=max_y,
        layer_name=layer_name,
        boundary_dxf_path=boundary_dxf_path,
        default_rail_z=default_rail_z,
    )

    print(
        f"\n[선로 기준점 산출] source={datum.source_desc}, "
        f"origin=({datum.origin_x:.3f}, {datum.origin_y:.3f}, {datum.origin_z:.3f}), "
        f"yaw={datum.yaw_deg:.2f} deg"
    )

    spec = BuseongProjectSpec.default_buseong()
    variants = get_default_alternatives()
    results: List[dict] = []

    out_dir.mkdir(parents=True, exist_ok=True)
    for v in variants:
        dxf_out = out_dir / f"{v.alt_id}_buseong.dxf"
        row = build_aligned_alternative_dxf(spec, v, datum, dxf_out)
        results.append(row)

    (out_dir / "alternatives_summary.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if results:
        with (out_dir / "alternatives_summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)

    return results


if __name__ == "__main__":
    INDEX_SHP = r"E:\백업\C\download230817\Compressed\indexmap\c5000.SHP"
    NGII_DXF = r"C:\Users\ADMINI~1\AppData\Local\Temp\BNZ.6b03db1817c8af2\36701066.dxf"  # 실제 수치지도 DXF 경로로 변경
    BOUNDARY_DXF = None                 # 닫힌 부지경계 폴리선 DXF가 있으면 경로 지정

    # 예시 TM 좌표(EPSG:5186)
    center = 213075.7146, 472129.6704
    bound_size = 100
    half_bound_size = bound_size /2
    min_x, min_y = center[0] - half_bound_size, center[1] - half_bound_size
    max_x, max_y = center[0] + half_bound_size, center[1] + half_bound_size

    summary = run_buseong_dxf_pipeline(
        ngii_dxf_path=NGII_DXF,
        min_x=min_x,
        min_y=min_y,
        max_x=max_x,
        max_y=max_y,
        index_shp_path=INDEX_SHP,
        boundary_dxf_path=BOUNDARY_DXF,
        layer_name="A0151111",
        default_rail_z=12.0,
    )
    print("\n[생성 완료 요약]")
    print(json.dumps(summary, ensure_ascii=False, indent=2))