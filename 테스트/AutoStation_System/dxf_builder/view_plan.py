from shapely.geometry import Polygon
from core.alignment_engine import get_curve_point_and_normal, transform_local_to_global
from core.clash_projection_engine import build_trimmed_plan_polygons, get_shallow_el_at_xy
from dxf_builder.dxf_setup import draw_shapely_geom

def draw_master_plan_views(msp, cfg, existing_objs, base_offset=(20.0, 260.0)):
    bx, by = base_offset
    prop = cfg["proposed_station"]
    al = cfg["alignments"][prop["alignment_ref"]]
    length = al["length"]

    trimmed_dict = build_trimmed_plan_polygons(cfg, existing_objs)
    lvl_names = [l["level_name"] for l in prop["levels_definition"] if not l.get("is_void")]

    for idx, lvl_name in enumerate(lvl_names):
        y_shift = by - idx * 95.0
        p_data = trimmed_dict[lvl_name]
        n_bot, n_top = p_data["el_range"]

        c_pts = []
        for i in range(int(length / 2.0) + 1):
            (cx, cy), _ = get_curve_point_and_normal(al, min(i * 2.0, length))
            c_pts.append((cx + bx, cy + y_shift))
        msp.add_lwpolyline(c_pts, dxfattribs={"layer": "0_CENTERLINE"})

        for p in p_data["outer"]:
            draw_shapely_geom(msp, p, "1_NEW_STR_CONCRETE", bx, y_shift)
        for p in p_data["inner"]:
            draw_shapely_geom(msp, p, "1_NEW_STR_CONCRETE", bx, y_shift)
        for p in p_data["finish"]:
            draw_shapely_geom(msp, p, "2_NEW_FIN_WALL", bx, y_shift)

        for ex_obj in existing_objs:
            ex = ex_obj["cfg"]
            if ex_obj["is_shallow"]:
                c = ex_obj["raw_poly"].centroid
                e_bot, e_top = get_shallow_el_at_xy(ex, c.x, c.y)
            else:
                e_bot, e_top = ex["el_bottom"], ex["el_top"]

            overlap = min(n_top, e_top) - max(n_bot, e_bot)
            if overlap > 0.05:
                draw_shapely_geom(msp, ex_obj["raw_poly"], "PROJ_EX_CLASH", bx, y_shift)
                draw_shapely_geom(msp, ex_obj["gap_poly"], "PROJ_CLEARANCE_GAP", bx, y_shift)
            elif e_bot >= n_top:
                draw_shapely_geom(msp, ex_obj["raw_poly"], "PROJ_EX_OVERHEAD", bx, y_shift)
            else:
                draw_shapely_geom(msp, ex_obj["raw_poly"], "PROJ_EX_UNDERNEATH", bx, y_shift)

        lvl_def = next(l for l in prop["levels_definition"] if l["level_name"] == lvl_name)
        cols = lvl_def.get("columns")
        if cols:
            curr_sta = cols["sta_start"]
            while curr_sta <= cols["sta_end"] + 1e-6:
                (cx, cy), (nx, ny) = get_curve_point_and_normal(al, curr_sta)
                origin = (cx + bx, cy + y_shift)
                for oy in cols["offsets_y"]:
                    pt = transform_local_to_global(origin, (nx, ny), 0.0, oy)
                    test_box = Polygon([(pt[0]-0.2, pt[1]-0.2), (pt[0]+0.2, pt[1]-0.2), (pt[0]+0.2, pt[1]+0.2), (pt[0]-0.2, pt[1]+0.2)])
                    if any(ip.contains(test_box) for ip in p_data["inner"]):
                        if cols["shape"] == "CIRCLE":
                            msp.add_circle(pt, radius=cols["diameter"] / 2.0, dxfattribs={"layer": "1_NEW_STR_COL"})
                        else:
                            dx, dy = cols["depth_x"], cols["width_y"]
                            corners = [transform_local_to_global(origin, (nx, ny), lx, oy + ly)
                                       for lx, ly in [(-dx/2, -dy/2), (dx/2, -dy/2), (dx/2, dy/2), (-dx/2, dy/2)]]
                            msp.add_lwpolyline(corners, close=True, dxfattribs={"layer": "1_NEW_STR_COL"})
                curr_sta += cols["sta_spacing"]

        if "B1" in lvl_name and "integrated_shaft" in cfg:
            sh = cfg["integrated_shaft"]
            scx, scy = sh["center_xy"][0] + bx, sh["center_xy"][1] + y_shift
            hl, hw = sh["outer_length_x"] / 2.0, sh["outer_width_y"] / 2.0
            msp.add_lwpolyline([(scx - hl, scy - hw), (scx + hl, scy - hw), (scx + hl, scy + hw), (scx - hl, scy + hw)],
                               close=True, dxfattribs={"layer": "4_SHAFT_STRUCTURE"})

        msp.add_text(f"PLAN VIEW [{lvl_name}] (EL {n_bot:.1f} ~ {n_top:.1f}m)",
                     dxfattribs={"layer": "TEXT_ANNO", "height": 0.75}).set_placement((bx, y_shift - 26.0))
