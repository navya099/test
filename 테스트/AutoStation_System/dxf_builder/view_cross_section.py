import math
from shapely.geometry import Polygon
from core.alignment_engine import get_curve_point_and_normal
from core.section_engine import compute_box_section_at_sta, build_tunnel_arch_loops
from core.clash_projection_engine import get_shallow_el_at_xy

def draw_master_cross_sections(msp, cfg, existing_objs, base_offset=(240.0, 260.0)):
    bx, by = base_offset
    prop = cfg["proposed_station"]
    al = cfg["alignments"][prop["alignment_ref"]]

    for idx, sec in enumerate(cfg["target_cross_sections"]):
        sx = bx + idx * 85.0
        sy = by
        target_sta = sec["sta"]
        proj_win = sec["proj_window_m"]

        levels_geo, rl_el, in_l, in_r = compute_box_section_at_sta(prop, target_sta)
        ordered = [g for g in levels_geo.values() if not g.get("is_void")]

        # 표고 그리드 및 중심선
        for el in range(-25, 20, 5):
            msp.add_line((sx - 35.0, sy + el), (sx + 30.0, sy + el), dxfattribs={"layer": "0_GRID_AXIS"})
        msp.add_line((sx, sy - 27.0), (sx, sy + 18.0), dxfattribs={"layer": "0_CENTERLINE"})

        # 외벽 계단식 단차 외곽 루프
        r_out, l_out = [], []
        for g in ordered:
            r_out.extend([(sx + g["out_right"], sy + g["el_box_bot"]), (sx + g["out_right"], sy + g["el_box_top"])])
        for g in reversed(ordered):
            l_out.extend([(sx - g["out_left"], sy + g["el_box_top"]), (sx - g["out_left"], sy + g["el_box_bot"])])
        msp.add_lwpolyline(r_out + l_out, close=True, dxfattribs={"layer": "1_NEW_STR_CONCRETE"})

        # 층별 내공 및 내장 마감선
        for g in ordered:
            yb, yt = sy + g["el_str_bot"], sy + g["el_str_top"]
            xl, xr, hn = g["in_left"], g["in_right"], g["haunch"]
            msp.add_lwpolyline([(sx - xl + hn, yb), (sx + xr - hn, yb), (sx + xr, yb + hn), (sx + xr, yt - hn),
                                (sx + xr - hn, yt), (sx - xl + hn, yt), (sx - xl, yt - hn), (sx - xl, yb + hn)],
                               close=True, dxfattribs={"layer": "1_NEW_STR_CONCRETE"})
            y_fl, y_cl = sy + g["fin_floor_el"], sy + g["fin_ceil_el"]
            msp.add_line((sx - xl, y_fl), (sx + xr, y_fl), dxfattribs={"layer": "2_NEW_FIN_CEIL_FL"})
            msp.add_line((sx - xl, y_cl), (sx + xr, y_cl), dxfattribs={"layer": "2_NEW_FIN_CEIL_FL"})
            msp.add_line((sx - g["fin_left"], y_fl), (sx - g["fin_left"], y_cl), dxfattribs={"layer": "2_NEW_FIN_WALL"})
            msp.add_line((sx + g["fin_right"], y_fl), (sx + g["fin_right"], y_cl), dxfattribs={"layer": "2_NEW_FIN_WALL"})

        # 기존 3개 정거장 + 지하차도 + 지하보도 횡단 투영
        (cx, cy), (nx, ny) = get_curve_point_and_normal(al, target_sta)
        tx, ty = ny, -nx
        scan_box = Polygon([
            (cx - tx * proj_win - nx * 60.0, cy - ty * proj_win - ny * 60.0),
            (cx + tx * proj_win - nx * 60.0, cy + ty * proj_win - ny * 60.0),
            (cx + tx * proj_win + nx * 60.0, cy + ty * proj_win + ny * 60.0),
            (cx - tx * proj_win + nx * 60.0, cy - ty * proj_win + ny * 60.0)
        ])

        for ex_obj in existing_objs:
            ex = ex_obj["cfg"]
            inter = scan_box.intersection(ex_obj["raw_poly"])
            if inter.is_empty:
                continue
            coords = list(inter.exterior.coords) if inter.geom_type == "Polygon" else [c for g in inter.geoms for c in g.exterior.coords]
            lat_xs = [-(px - cx) * nx - (py - cy) * ny for px, py in coords]
            x0, x1 = min(lat_xs), max(lat_xs)
            if ex_obj["is_shallow"]:
                eb, et = get_shallow_el_at_xy(ex, cx, cy)
            else:
                eb, et = ex["el_bottom"], ex["el_top"]
            gap = ex["clearance_gap"]

            msp.add_lwpolyline([(sx + x0, sy + eb), (sx + x1, sy + eb), (sx + x1, sy + et), (sx + x0, sy + et)],
                               close=True, dxfattribs={"layer": "PROJ_EX_OVERHEAD"})
            msp.add_lwpolyline([(sx + x0 - gap, sy + eb - gap), (sx + x1 + gap, sy + eb - gap),
                                (sx + x1 + gap, sy + et + gap), (sx + x0 - gap, sy + et + gap)],
                               close=True, dxfattribs={"layer": "PROJ_CLEARANCE_GAP"})
            msp.add_text(ex["id"], dxfattribs={"layer": "TEXT_ANNO", "height": 0.40}).set_placement((sx + x0, sy + et + gap + 0.3))

        msp.add_text(sec["title"], dxfattribs={"layer": "TEXT_ANNO", "height": 0.55}).set_placement((sx - 35.0, sy - 30.0))

    # 우측에 대단면 아치 터널 표준 단면(V11 모듈) 함께 작도
    if "tunnel_station_sample" in cfg:
        tx, ty = bx + 175.0, by - 5.0
        loops = build_tunnel_arch_loops(cfg["tunnel_station_sample"])
        for key, layer in [("shotcrete", "1_TUNNEL_LINING"), ("lining", "1_TUNNEL_LINING"), ("inner", "1_TUNNEL_LINING")]:
            pts = [(tx + x, ty + y) for x, y in loops[key].exterior.coords]
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})
        msp.add_text("REFERENCE LARGE-SECTION ARCH TUNNEL PROFILE",
                     dxfattribs={"layer": "TEXT_ANNO", "height": 0.55}).set_placement((tx - 11.0, ty - 6.0))
