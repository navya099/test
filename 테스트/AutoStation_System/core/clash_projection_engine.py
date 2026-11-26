import math
from shapely.geometry import Polygon
from core.alignment_engine import get_curve_point_and_normal, build_corridor_polygon, interpolate_1d
from core.section_engine import compute_box_section_at_sta

def build_existing_corridors(cfg):
    ex_list = []
    for ex in cfg.get("existing_stations", []):
        al = ex["alignment"]
        raw_p = build_corridor_polygon(al, al["left_w"], al["right_w"], step=0.5)
        gap_p = raw_p.buffer(ex["clearance_gap"], join_style=1, resolution=32)
        ex_list.append({"cfg": ex, "raw_poly": raw_p, "gap_poly": gap_p, "is_shallow": False})

    for sh in cfg.get("shallow_existing_structures", []):
        al = sh["alignment"]
        raw_p = build_corridor_polygon(al, al["left_w"], al["right_w"], step=0.5)
        gap_p = raw_p.buffer(sh["clearance_gap"], join_style=2)
        ex_list.append({"cfg": sh, "raw_poly": raw_p, "gap_poly": gap_p, "is_shallow": True})

    return ex_list

def get_shallow_el_at_xy(sh_cfg, px, py):
    al = sh_cfg["alignment"]
    length = al["length"]
    best_s, min_d = 0.0, 1e9
    for i in range(int(length) + 1):
        s = float(i)
        (cx, cy), _ = get_curve_point_and_normal(al, s)
        d = math.hypot(px - cx, py - cy)
        if d < min_d:
            min_d, best_s = d, s
    el_top = interpolate_1d(sh_cfg["el_top_profile"], "s", "el_top", best_s)
    return el_top - sh_cfg["box_total_height"], el_top

def build_trimmed_plan_polygons(cfg, existing_objs):
    """층별 신설 평면 폴리곤에서 동일 심도 기존 구조물을 곡선 불리언 차집합(Trim) 처리"""
    prop = cfg["proposed_station"]
    al = cfg["alignments"][prop["alignment_ref"]]
    length = al["length"]
    step = 0.5
    results = {}

    for lvl in prop["levels_definition"]:
        if lvl.get("is_void"):
            continue
        lvl_name = lvl["level_name"]
        wt = lvl["wall_t"]
        ft = lvl["finishes"]["wall_t"]

        segments, cur_l, cur_r = [], [], []
        el_samples = []
        for i in range(int(length / step) + 1):
            sta = min(i * step, length)
            l_geo, _, _, _ = compute_box_section_at_sta(prop, sta)
            if lvl_name in l_geo:
                g = l_geo[lvl_name]
                (cx, cy), (nx, ny) = get_curve_point_and_normal(al, sta)
                cur_l.append((cx + nx * g["out_left"], cy + ny * g["out_left"]))
                cur_r.append((cx - nx * g["out_right"], cy - ny * g["out_right"]))
                el_samples.append((g["el_box_bot"], g["el_box_top"]))
            else:
                if cur_l:
                    segments.append((cur_l, cur_r))
                    cur_l, cur_r = [], []
        if cur_l:
            segments.append((cur_l, cur_r))

        lvl_el_bot = min(e[0] for e in el_samples) if el_samples else -20.0
        lvl_el_top = max(e[1] for e in el_samples) if el_samples else 0.0

        trimmed_outers = []
        for l_pts, r_pts in segments:
            poly = Polygon(l_pts + list(reversed(r_pts))).buffer(0)
            for ex_obj in existing_objs:
                ex = ex_obj["cfg"]
                if ex_obj["is_shallow"]:
                    c = ex_obj["raw_poly"].centroid
                    ex_eb, ex_et = get_shallow_el_at_xy(ex, c.x, c.y)
                else:
                    ex_eb, ex_et = ex["el_bottom"], ex["el_top"]

                # 수직 표고(EL)가 겹치는 경우에만 평면 불리언 절단 수행
                if min(lvl_el_top, ex_et) - max(lvl_el_bot, ex_eb) > 0.05:
                    poly = poly.difference(ex_obj["gap_poly"])
            if not poly.is_empty:
                trimmed_outers.append(poly)

        inners = [p.buffer(-wt, join_style=1, resolution=32) for p in trimmed_outers if not p.is_empty]
        finishes = [p.buffer(-(wt + ft), join_style=1, resolution=32) for p in trimmed_outers if not p.is_empty]
        results[lvl_name] = {
            "outer": trimmed_outers,
            "inner": inners,
            "finish": finishes,
            "el_range": (lvl_el_bot, lvl_el_top)
        }

    return results
