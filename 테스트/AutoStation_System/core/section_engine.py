import math
from shapely.geometry import Polygon
from core.alignment_engine import interpolate_1d

def get_interpolated_section_at_sta(prop_cfg, sta):
    sec_list = sorted(prop_cfg["section_stations"], key=lambda x: x["sta"])
    if sta <= sec_list[0]["sta"]:
        s = sec_list[0]
        return s["inner_left_w"], s["inner_right_w"], s["active_levels"]
    if sta >= sec_list[-1]["sta"]:
        s = sec_list[-1]
        return s["inner_left_w"], s["inner_right_w"], s["active_levels"]

    for i in range(len(sec_list) - 1):
        s0, s1 = sec_list[i], sec_list[i + 1]
        if s0["sta"] <= sta <= s1["sta"]:
            span = s1["sta"] - s0["sta"]
            ratio = 0.0 if span == 0 else (sta - s0["sta"]) / span
            lw = s0["inner_left_w"] + (s1["inner_left_w"] - s0["inner_left_w"]) * ratio
            rw = s0["inner_right_w"] + (s1["inner_right_w"] - s0["inner_right_w"]) * ratio
            lvls = s1["active_levels"] if (ratio > 0 and len(s1["active_levels"]) > len(s0["active_levels"])) else s0["active_levels"]
            if sta == s1["sta"]:
                lvls = s1["active_levels"]
            return lw, rw, lvls
    return sec_list[-1]["inner_left_w"], sec_list[-1]["inner_right_w"], sec_list[-1]["active_levels"]

def compute_box_section_at_sta(prop_cfg, sta):
    in_left, in_right, active_lvls = get_interpolated_section_at_sta(prop_cfg, sta)
    rl_el = interpolate_1d(prop_cfg["vertical_profile_rl"], "sta", "rl_el", sta)
    levels_geo = {}
    curr_el = rl_el - 1.5

    for idx, lvl in enumerate(prop_cfg["levels_definition"]):
        if lvl.get("is_void", False):
            v_bot = curr_el
            curr_el += lvl["void_height"]
            levels_geo[lvl["level_name"]] = {"is_void": True, "el_bot": v_bot, "el_top": curr_el}
            continue

        bot_t = lvl.get("bot_slab_t", 0.0)
        top_t = lvl.get("top_slab_t", 0.0)
        ch = lvl["clear_height"]

        if lvl["level_name"] not in active_lvls:
            curr_el += bot_t + ch + top_t
            continue

        box_bot = curr_el
        str_bot = box_bot + bot_t
        str_top = str_bot + ch
        box_top = str_top + top_t
        fin = lvl["finishes"]
        wt = lvl["wall_t"]

        levels_geo[lvl["level_name"]] = {
            "is_void": False,
            "index": idx,
            "wall_t": wt,
            "in_left": in_left,
            "in_right": in_right,
            "out_left": in_left + wt,
            "out_right": in_right + wt,
            "fin_left": in_left - fin["wall_t"],
            "fin_right": in_right - fin["wall_t"],
            "el_box_bot": box_bot,
            "el_str_bot": str_bot,
            "el_str_top": str_top,
            "el_box_top": box_top,
            "fin_floor_el": str_bot + fin["floor_t"],
            "fin_ceil_el": str_top - fin["ceiling_drop"],
            "haunch": lvl["haunch_size"],
            "columns": lvl.get("columns", None),
            "wall_fin_t": fin["wall_t"]
        }
        curr_el = box_top

    return levels_geo, rl_el, in_left, in_right

def compute_circular_arc_3pts(p1, p2, p3, num_pts=32):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    D = 2.0 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(D) < 1e-9:
        return [p1, p3]
    ux = ((x1**2 + y1**2) * (y2 - y3) + (x2**2 + y2**2) * (y3 - y1) + (x3**2 + y3**2) * (y1 - y2)) / D
    uy = ((x1**2 + y1**2) * (x3 - x2) + (x2**2 + y2**2) * (x1 - x3) + (x3**2 + y3**2) * (x2 - x1)) / D
    R = math.hypot(x1 - ux, y1 - uy)

    def norm(a):
        while a < 0:
            a += 2 * math.pi
        while a >= 2 * math.pi:
            a -= 2 * math.pi
        return a

    ang1, ang2, ang3 = math.atan2(y1 - uy, x1 - ux), math.atan2(y2 - uy, x2 - ux), math.atan2(y3 - uy, x3 - ux)
    a1, a2, a3 = norm(ang1), norm(ang2), norm(ang3)
    ccw = ((a2 - a1) % (2 * math.pi)) < ((a3 - a1) % (2 * math.pi))
    if ccw:
        span = (a3 - a1) % (2 * math.pi)
        angles = [ang1 + span * (i / num_pts) for i in range(num_pts + 1)]
    else:
        span = (a1 - a3) % (2 * math.pi)
        angles = [ang1 - span * (i / num_pts) for i in range(num_pts + 1)]
    return [(ux + R * math.cos(a), uy + R * math.sin(a)) for a in angles]

def build_tunnel_arch_loops(tun_cfg):
    hw = tun_cfg["inner_half_width"]
    el_sl = tun_cfg["springline_el"]
    el_cr = tun_cfg["crown_el"]
    el_sw = tun_cfg["sidewall_bottom_el"]
    el_inv = tun_cfg["invert_bottom_el"]

    crown = compute_circular_arc_3pts((hw, el_sl), (0.0, el_cr), (-hw, el_sl), 48)
    l_sw = compute_circular_arc_3pts((-hw, el_sl), (-hw * 0.96, (el_sl + el_sw) / 2.0), (-hw * 0.88, el_sw), 16)
    inv = compute_circular_arc_3pts((-hw * 0.88, el_sw), (0.0, el_inv), (hw * 0.88, el_sw), 24)
    r_sw = compute_circular_arc_3pts((hw * 0.88, el_sw), (hw * 0.96, (el_sl + el_sw) / 2.0), (hw, el_sl), 16)

    inner_poly = Polygon(crown[:-1] + l_sw[:-1] + inv[:-1] + r_sw[:-1]).buffer(0)
    lining_poly = inner_poly.buffer(tun_cfg["lining_thickness"], join_style=1, resolution=32)
    shotcrete_poly = lining_poly.buffer(tun_cfg["shotcrete_thickness"], join_style=1, resolution=32)
    return {"inner": inner_poly, "lining": lining_poly, "shotcrete": shotcrete_poly}
