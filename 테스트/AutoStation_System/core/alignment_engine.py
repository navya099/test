import math
from shapely.geometry import Polygon

def interpolate_1d(pts_list, x_key, y_key, target_x):
    pts = sorted(pts_list, key=lambda p: p[x_key])
    if target_x <= pts[0][x_key]:
        return pts[0][y_key]
    if target_x >= pts[-1][x_key]:
        return pts[-1][y_key]
    for i in range(len(pts) - 1):
        x0, x1 = pts[i][x_key], pts[i + 1][x_key]
        if x0 <= target_x <= x1:
            t = 0.0 if x1 == x0 else (target_x - x0) / (x1 - x0)
            return pts[i][y_key] + (pts[i + 1][y_key] - pts[i][y_key]) * t
    return pts[-1][y_key]

def get_curve_point_and_normal(al_cfg, sta):
    sx, sy = al_cfg["start_xy"]
    az0 = math.radians(al_cfg["start_azimuth_deg"])
    R = al_cfg.get("curve_radius", 0.0)

    if not R or R == 0:
        cx = sx + sta * math.cos(az0)
        cy = sy + sta * math.sin(az0)
        az = az0
    else:
        az = az0 + sta / R
        center_x = sx - R * math.sin(az0)
        center_y = sy + R * math.cos(az0)
        cx = center_x + R * math.sin(az)
        cy = center_y - R * math.cos(az)

    nx, ny = -math.sin(az), math.cos(az)
    return (cx, cy), (nx, ny)

def transform_local_to_global(origin, normal, local_x, local_y):
    ox, oy = origin
    nx, ny = normal
    tx, ty = ny, -nx
    return (ox + local_x * tx + local_y * nx, oy + local_x * ty + local_y * ny)

def build_corridor_polygon(al_cfg, left_w, right_w, step=0.5):
    length = al_cfg["length"]
    num_steps = int(length / step) + 1
    l_pts, r_pts = [], []
    for i in range(num_steps):
        sta = min(i * step, length)
        (cx, cy), (nx, ny) = get_curve_point_and_normal(al_cfg, sta)
        l_pts.append((cx + nx * left_w, cy + ny * left_w))
        r_pts.append((cx - nx * right_w, cy - ny * right_w))
    return Polygon(l_pts + list(reversed(r_pts))).buffer(0)
