from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import ezdxf
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString, box

from alignment_dxf_aligner import TrackDatum


def find_5k_sheets_by_tm_bbox(
    shp_path: str | Path,
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    index_crs: str = "EPSG:5174",
    verbose: bool = True,
) -> Optional[gpd.GeoDataFrame]:
    """
    TM 중부원점(EPSG:5186) 범위 내에 포함되는 1:5,000 도엽 정보를 조회합니다.
    """
    input_box = box(min_x, min_y, max_x, max_y)
    gdf_input = gpd.GeoDataFrame(geometry=[input_box], crs="EPSG:5186")

    if verbose:
        gdf_input_wgs84 = gdf_input.to_crs(epsg=4326)
        b_wgs = gdf_input_wgs84.geometry.iloc[0].bounds
        print("\n" + "=" * 60)
        print("[디버그] 입력 좌표 정보 (WGS84 위경도 변환값)")
        print(f" - 좌하단 (최소 경도, 최소 위도): {b_wgs[0]:.6f}, {b_wgs[1]:.6f}")
        print(f" - 우상단 (최대 경도, 최대 위도): {b_wgs[2]:.6f}, {b_wgs[3]:.6f}")
        print("=" * 60)

    gdf = gpd.read_file(shp_path, encoding="cp949")
    if gdf.crs is None:
        gdf.set_crs(index_crs, inplace=True)

    search_area_converted = gdf_input.to_crs(gdf.crs).geometry.iloc[0]
    matched = gdf[gdf.geometry.intersects(search_area_converted)]

    if matched.empty:
        if verbose:
            print("\n[안내] 입력하신 TM 좌표 영역 안에 포함되는 도엽이 없습니다.")
        return None

    sort_col = "MAP_NUM" if "MAP_NUM" in matched.columns else matched.columns[0]
    matched_sorted = matched.sort_values(by=sort_col)

    if verbose:
        print(f"\n[조회 완료] 검색 영역 내에 총 {len(matched_sorted)}개의 도엽이 발견되었습니다.")
        print("-" * 50)
        print(f"{'도엽코드 (MAP_NUM)':<18} | {'도엽명 (MAP_NAM)':<20}")
        print("-" * 50)
        for _, row in matched_sorted.iterrows():
            m_num = str(row.get("MAP_NUM", ""))
            m_nam = str(row.get("MAP_NAM", ""))
            print(f"{m_num:<18} | {m_nam:<20}")

    return matched_sorted


def _collect_line_coords(geom) -> List[Tuple[float, float, float]]:
    coords: List[Tuple[float, float, float]] = []
    if geom is None or geom.is_empty:
        return coords

    if isinstance(geom, LineString):
        for pt in geom.coords:
            x = float(pt[0])
            y = float(pt[1])
            z = float(pt[2]) if len(pt) > 2 else 0.0
            coords.append((x, y, z))
    elif isinstance(geom, MultiLineString):
        for part in geom.geoms:
            coords.extend(_collect_line_coords(part))
    elif hasattr(geom, "geoms"):
        for sub in geom.geoms:
            coords.extend(_collect_line_coords(sub))
    return coords


def extract_track_datum_from_ngii_vector(
    map_vector_path: str | Path,
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    boundary_gdf: Optional[gpd.GeoDataFrame] = None,
    layer_keywords: Iterable[str] = ("철도", "선로", "RAIL", "TRACK", "CENTER"),
    explicit_layer_column: Optional[str] = None,
    explicit_layer_value: Optional[str] = None,
    source_crs: Optional[str] = "EPSG:5186",
    station_anchor: Optional[Tuple[float, float, Optional[float]]] = None,
    default_rail_z: float = 12.0,
    clipped_output_path: Optional[str | Path] = None,
) -> TrackDatum:
    """
    수치지도 벡터 파일(SHP/GPKG/GeoJSON)을 부지 경계(또는 TM BBOX)로 자른 뒤,
    선로 중심선 레이어를 추출해 TrackDatum으로 변환합니다.
    """
    gdf = gpd.read_file(map_vector_path, encoding="cp949")
    if gdf.crs is None and source_crs:
        gdf.set_crs(source_crs, inplace=True)
    if gdf.crs and str(gdf.crs) != "EPSG:5186":
        gdf = gdf.to_crs("EPSG:5186")

    # 클리핑 기준 폴리곤 구성(부지 폴리곤이 있으면 우선 사용, 없으면 TM BBOX 사용)
    if boundary_gdf is not None and not boundary_gdf.empty:
        clip_geom_gdf = boundary_gdf.to_crs("EPSG:5186") if str(boundary_gdf.crs) != "EPSG:5186" else boundary_gdf
    else:
        clip_geom_gdf = gpd.GeoDataFrame(geometry=[box(min_x, min_y, max_x, max_y)], crs="EPSG:5186")

    clipped = gpd.clip(gdf, clip_geom_gdf)
    if clipped.empty:
        return TrackDatum(
            origin_x=0.5 * (min_x + max_x),
            origin_y=0.5 * (min_y + max_y),
            origin_z=default_rail_z,
            yaw_rad=0.0,
            source_desc="FALLBACK_CLIP_EMPTY",
        )

    # 선로 중심선 레이어 필터링
    if explicit_layer_column and explicit_layer_value and explicit_layer_column in clipped.columns:
        track_gdf = clipped[clipped[explicit_layer_column].astype(str) == explicit_layer_value]
    else:
        keywords_upper = [k.upper() for k in layer_keywords]
        candidate_cols = [c for c in ["LAYER", "layer", "LNAME", "FTR_NAM", "NAME", "CLASS"] if c in clipped.columns]

        if candidate_cols:
            mask = gpd.pd.Series(False, index=clipped.index)
            for col in candidate_cols:
                col_str = clipped[col].astype(str).str.upper()
                for kw in keywords_upper:
                    mask = mask | col_str.str.contains(kw, na=False)
            track_gdf = clipped[mask]
        else:
            # 레이어 컬럼이 없는 단일 SHP인 경우 선형 지오메트리만 선택
            track_gdf = clipped[clipped.geometry.geom_type.isin(["LineString", "MultiLineString"])]

    if track_gdf.empty:
        track_gdf = clipped[clipped.geometry.geom_type.isin(["LineString", "MultiLineString"])]

    if clipped_output_path is not None and not track_gdf.empty:
        out_p = Path(clipped_output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        track_gdf.to_file(out_p, encoding="utf-8")

    pts: List[Tuple[float, float, float]] = []
    for geom in track_gdf.geometry:
        pts.extend(_collect_line_coords(geom))

    if len(pts) < 2:
        return TrackDatum(
            origin_x=0.5 * (min_x + max_x),
            origin_y=0.5 * (min_y + max_y),
            origin_z=default_rail_z,
            yaw_rad=0.0,
            source_desc="FALLBACK_NO_TRACK_LINE",
        )

    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    zs = [p[2] for p in pts if abs(p[2]) > 1e-6]
    cz = (sum(zs) / len(zs)) if zs else default_rail_z

    s_xx = sum((p[0] - cx) ** 2 for p in pts) / len(pts)
    s_yy = sum((p[1] - cy) ** 2 for p in pts) / len(pts)
    s_xy = sum((p[0] - cx) * (p[1] - cy) for p in pts) / len(pts)

    trace = s_xx + s_yy
    det = s_xx * s_yy - s_xy**2
    lam1 = 0.5 * (trace + math.sqrt(max(trace**2 - 4.0 * det, 0.0)))

    if abs(s_xy) > 1e-9:
        vx = lam1 - s_yy
        vy = s_xy
    else:
        vx, vy = (1.0, 0.0) if s_xx >= s_yy else (0.0, 1.0)

    yaw_rad = math.atan2(-vx, vy)

    if station_anchor is not None:
        ax, ay, az = station_anchor
        nearest = min(pts, key=lambda p: (p[0] - ax) ** 2 + (p[1] - ay) ** 2)
        ox, oy = nearest[0], nearest[1]
        oz = az if az is not None else (nearest[2] if abs(nearest[2]) > 1e-6 else cz)
        desc = f"NGII_CLIP_ANCHOR({Path(map_vector_path).name})"
    else:
        ox, oy, oz = cx, cy, cz
        desc = f"NGII_CLIP_CENTROID({Path(map_vector_path).name})"

    return TrackDatum(
        origin_x=ox,
        origin_y=oy,
        origin_z=oz,
        yaw_rad=yaw_rad,
        source_desc=desc,
    )


def extract_track_datum_from_dxf_bbox(
    dxf_path: str | Path,
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    layer_name: Optional[str] = None,
    default_rail_z: float = 12.0,
) -> TrackDatum:
    """
    DXF 형태 수치지도에서 지정 레이어 및 TM BBOX 내 선형 엔티티만 골라 TrackDatum을 생성합니다.
    """
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    pts: List[Tuple[float, float, float]] = []

    def inside_bbox(x: float, y: float) -> bool:
        return (min_x <= x <= max_x) and (min_y <= y <= max_y)

    for ent in msp:
        if layer_name and ent.dxf.layer.lower() != layer_name.lower():
            continue
        dxftype = ent.dxftype()
        if dxftype == "LINE":
            s, e = ent.dxf.start, ent.dxf.end
            for pt in ((s.x, s.y, s.z), (e.x, e.y, e.z)):
                if inside_bbox(float(pt[0]), float(pt[1])):
                    pts.append((float(pt[0]), float(pt[1]), float(pt[2])))
        elif dxftype == "LWPOLYLINE":
            elev = float(getattr(ent.dxf, "elevation", 0.0))
            for x, y, *_ in ent.get_points():
                if inside_bbox(float(x), float(y)):
                    pts.append((float(x), float(y), elev))
        elif dxftype == "POLYLINE":
            for v in ent.vertices:
                loc = v.dxf.location
                if inside_bbox(float(loc.x), float(loc.y)):
                    pts.append((float(loc.x), float(loc.y), float(loc.z)))

    if len(pts) < 2:
        return TrackDatum(
            origin_x=0.5 * (min_x + max_x),
            origin_y=0.5 * (min_y + max_y),
            origin_z=default_rail_z,
            yaw_rad=0.0,
            source_desc="FALLBACK_DXF_BBOX_EMPTY",
        )

    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    zs = [p[2] for p in pts if abs(p[2]) > 1e-6]
    cz = (sum(zs) / len(zs)) if zs else default_rail_z

    s_xx = sum((p[0] - cx) ** 2 for p in pts) / len(pts)
    s_yy = sum((p[1] - cy) ** 2 for p in pts) / len(pts)
    s_xy = sum((p[0] - cx) * (p[1] - cy) for p in pts) / len(pts)

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
        origin_z=cz,
        yaw_rad=yaw_rad,
        source_desc=f"DXF_BBOX({Path(dxf_path).name})",
    )


if __name__ == "__main__":
    SHP_FILE_PATH = r"E:\백업\C\download230817\Compressed\indexmap\c5000.SHP"
    min_x, min_y = 207478.0, 476116.0
    max_x, max_y = 207713.0, 476448.0

    sheets = find_5k_sheets_by_tm_bbox(SHP_FILE_PATH, min_x, min_y, max_x, max_y)
    if sheets is not None:
        print("\n[확인] 매칭 도엽 코드:", list(sheets.get("MAP_NUM", [])))