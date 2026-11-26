import math
from shapely.geometry import LineString
from core.alignment_engine import get_curve_point_and_normal
from core.section_engine import compute_box_section_at_sta
from core.clash_projection_engine import get_shallow_el_at_xy

def draw_master_longitudinal_view(msp, cfg, existing_objs, base_offset=(20.0, 20.0)):
    bx, by = base_offset
    prop = cfg["proposed_station"]
    al = cfg["alignments"][prop["alignment_ref"]]
    L = al["length"]

    for el in range(-30, 20, 5):
        msp.add_line((bx, by + el), (bx + L, by + el), dxfattribs={"layer": "0_GRID_AXIS"})
        msp.add_text(f"EL {el:+3d}m", dxfattribs={"layer": "TEXT_ANNO", "height": 0.55}).set_placement((bx - 13.0, by + el - 0.25))

    for sta in range(0, int(L) + 1, 20):
        msp.add_line((bx + sta, by - 30.0), (bx + sta, by + 18.0), dxfattribs={"layer": "0_GRID_AXIS"})
        msp.add_text(f"STA.0+{sta:03d}", dxfattribs={"layer": "TEXT_ANNO", "height": 0.55}).set_placement((bx + sta - 3.5, by - 32.5))

    for key in ["GL", "weathered_rock", "soft_rock"]:
        pts = [(bx + p["sta"], by + p[key]) for p in cfg["ground_profile"]]
        msp.add_lwpolyline(pts, dxfattribs={"layer": "0_GROUND_STRATA"})

    step = 2.0
    num_steps = int(L / step) + 1
    for lvl in prop["levels_definition"]:
        if lvl.get("is_void"):
            continue
        lname = lvl["level_name"]
        segs, cur = [], []
        for i in range(num_steps):
            sta = min(i * step, L)
            l_geo, _, _, _ = compute_box_section_at_sta(prop, sta)
            if lname in l_geo:
                cur.append((sta, l_geo[lname]))
            else:
                if cur:
                    segs.append(cur)
                    cur = []
        if cur:
            segs.append(cur)

        for seg in segs:
            b_box = [(bx + s, by + g["el_box_bot"]) for s, g in seg]
            t_box = [(bx + s, by + g["el_box_top"]) for s, g in seg]
            b_str = [(bx + s, by + g["el_str_bot"]) for s, g in seg]
            t_str = [(bx + s, by + g["el_str_top"]) for s, g in seg]
            msp.add_lwpolyline(b_box, dxfattribs={"layer": "1_NEW_STR_CONCRETE"})
            msp.add_lwpolyline(t_box, dxfattribs={"layer": "1_NEW_STR_CONCRETE"})
            msp.add_lwpolyline(b_str, dxfattribs={"layer": "1_NEW_STR_CONCRETE"})
            msp.add_lwpolyline(t_str, dxfattribs={"layer": "1_NEW_STR_CONCRETE"})
            msp.add_line(b_box[0], t_box[0], dxfattribs={"layer": "1_NEW_STR_CONCRETE"})
            msp.add_line(b_box[-1], t_box[-1], dxfattribs={"layer": "1_NEW_STR_CONCRETE"})

    for ex_obj in existing_objs:
        ex = ex_obj["cfg"]
        raw_p = ex_obj["raw_poly"]
        ex_al = ex["alignment"]
        ex_cl_pts = [get_curve_point_and_normal(ex_al, min(i * 1.0, ex_al["length"]))[0]
                     for i in range(int(ex_al["length"]) + 1)]
        ex_cl = LineString(ex_cl_pts)

        hit_pts = []
        for i in range(int(L / 0.5) + 1):
            sta = min(i * 0.5, L)
            (cx, cy), (nx, ny) = get_curve_point_and_normal(al, sta)
            _, _, in_l, in_r = compute_box_section_at_sta(prop, sta)
            c_slice = LineString([(cx - nx * (in_r + 1.5), cy - ny * (in_r + 1.5)),
                                  (cx + nx * (in_l + 1.5), cy + ny * (in_l + 1.5))])
            if c_slice.intersects(raw_p):
                if ex_obj["is_shallow"]:
                    eb, et = get_shallow_el_at_xy(ex, cx, cy)
                elif ex["structure_type"] == "TUNNEL_ARCH":
                    d = c_slice.intersection(raw_p).distance(ex_cl)
                    ratio = min(1.0, d / max(0.1, ex_al["left_w"]))
                    af = math.sqrt(max(0.0, 1.0 - ratio**2))
                    tp = ex["tunnel_profile"]
                    et = tp["springline_el"] + (ex["el_top"] - tp["springline_el"]) * af
                    eb = tp["sidewall_bot_el"] - (tp["sidewall_bot_el"] - ex["el_bottom"]) * af
                else:
                    eb, et = ex["el_bottom"], ex["el_top"]
                hit_pts.append((sta, eb, et))

        if len(hit_pts) >= 2:
            top_l = [(bx + s, by + et) for s, eb, et in hit_pts]
            bot_l = [(bx + s, by + eb) for s, eb, et in reversed(hit_pts)]
            msp.add_lwpolyline(top_l + bot_l, close=True, dxfattribs={"layer": "PROJ_EX_CLASH"})
            gap = ex["clearance_gap"]
            g_top = [(bx + s, by + et + gap) for s, eb, et in hit_pts]
            g_bot = [(bx + s, by + eb - gap) for s, eb, et in reversed(hit_pts)]
            msp.add_lwpolyline(g_top + g_bot, close=True, dxfattribs={"layer": "PROJ_CLEARANCE_GAP"})

            mid_s, mid_eb, mid_et = hit_pts[len(hit_pts) // 2]
            msp.add_text(f"{ex['id']}", dxfattribs={"layer": "TEXT_ANNO", "height": 0.45}).set_placement((bx + mid_s - 6.0, by + (mid_eb + mid_et) / 2.0))

    msp.add_text("DEVELOPED LONGITUDINAL PROFILE WITH ALL EXISTING STRUCTURES PROJECTION",
                 dxfattribs={"layer": "TEXT_ANNO", "height": 0.80}).set_placement((bx, by + 20.0))
