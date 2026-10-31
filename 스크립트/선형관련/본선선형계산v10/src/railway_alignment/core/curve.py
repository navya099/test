
import math
from shapely.geometry.linestring  import LineString

from src.railway_alignment.core.cant import dictionary_cubicparabola
from src.railway_alignment.core.constant_config import Config
from src.railway_alignment.core.math_util import calculate_bearing_n, calculate_distance, find_direction, \
    format_distance
from src.railway_alignment.core.models import StationRow, CurveParams
from src.railway_alignment.core.station_builder import build_station_group
import logging
logger = logging.getLogger(__name__)

# ============================================================
# 선형 계산 (수식 원본 유지)
# ============================================================
def calculate_theta_pc(m: float, z: float, rc: float) -> float:
    return math.atan(m * (z * 0.001) / (2 * rc))

def calculate_cubic_parabola_parameter(
    m: float, z: float, direction: int, theta_pc: float, rc: float, ia_rad: float
) -> list[float]:
    x1 = m * (z * 0.001)
    x2 = x1 - rc * math.sin(theta_pc)
    w13 = rc * direction
    L = x1 * (1 + (math.tan(theta_pc) ** 2) / 10)
    Y = (x1 ** 2) / (6 * rc)
    w15 = (x1 ** 2) / (6 * w13)
    F = Y - rc * (1 - math.cos(theta_pc))
    S = F / math.cos(ia_rad / 2)
    K = F * math.tan(ia_rad / 2)
    W = (rc + F) * math.tan(ia_rad / 2)
    TL = x2 + W
    Lc = rc * (ia_rad - 2 * theta_pc)
    CL = Lc + 2 * L
    SL = rc * (1 / math.cos(ia_rad / 2) - 1) + S
    RIA = ia_rad - 2 * theta_pc
    C = math.atan(Y / x1)
    XB = math.pi / 2 - theta_pc
    B = math.pi / 2 - C - XB
    return [x1, x2, w13, L, Y, w15, F, S, K, W, TL, Lc, CL, SL, RIA, C, B]


def calculate_simplecurve_parameter(direction: int, rc: float, ia_rad: float) -> list[float]:
    TL = rc * math.tan(ia_rad / 2)
    CL = rc * ia_rad
    SL = rc * (1 / math.cos(ia_rad / 2) - 1)
    S = rc * (1 - math.cos(ia_rad / 2))
    W13 = rc * direction
    return [TL, CL, SL, S, W13]


def calculate_sp_pc_bearing(w13: float, v10: float, x10: float) -> float:
    result = v10 - x10 if w13 < 0 else v10 + x10
    return result + 360 if result < 0 else (result - 360 if result > 360 else result)


def calculate_o_pc_bearing(v10: float, theta_pc: float, w13: float) -> float:
    x10 = math.degrees(theta_pc)
    if w13 > 0:
        r = v10 + x10 - 90
        return r + 360 if r < 0 else r
    r = v10 - x10 + 90
    return r - 360 if r > 360 else r


def calculate_cp_xy(k21, n21, w13, w18, p10, v11) -> tuple[float, float]:
    a1 = w13 * math.cos(math.radians(w18 + 90))
    a2 = w13 * math.cos(math.radians(w18 - 90 + (180 * p10) / (math.pi * w13)))
    b1 = w13 * math.sin(math.radians(w18 + 90))
    b2 = w13 * math.sin(math.radians(w18 - 90 + (180 * p10) / (math.pi * w13)))
    return k21 + a1 + a2, n21 + b1 + b2


def calculate_spiral_coordinates(
    bp_xy, ip_xy, ep_xy, h1, h2, tl, x1, y, sp_pc_bearing, rc, lc, w13
):
    sp_xy = (
        math.cos(math.radians(h1 + 180)) * tl + ip_xy[0],
        math.sin(math.radians(h1 + 180)) * tl + ip_xy[1],
    )
    pc_xy = (
        sp_xy[0] + x1 * math.cos(math.radians(h1)) + y * math.cos(math.radians(h1 + 90)),
        sp_xy[1] + x1 * math.sin(math.radians(h1)) + y * math.sin(math.radians(h1 + 90)),
    )
    cp_xy = calculate_cp_xy(pc_xy[0], pc_xy[1], w13, sp_pc_bearing, lc, h2)
    ps_xy = (
        math.cos(math.radians(h2)) * tl + ip_xy[0],
        math.sin(math.radians(h2)) * tl + ip_xy[1],
    )
    return sp_xy, pc_xy, cp_xy, ps_xy


def calculate_simplecurve_coordinates(v10, v11, tl, ip) -> list[tuple[float, float]]:
    bc = (
        math.cos(math.radians(v10 + 180)) * tl + ip[0],
        math.sin(math.radians(v10 + 180)) * tl + ip[1],
    )
    ec = (
        math.cos(math.radians(v11)) * tl + ip[0],
        math.sin(math.radians(v11)) * tl + ip[1],
    )
    return [bc, ec]





def cal_spiral_shiftx(sta, sp, pc, cp, ps, offset, w13, length) -> float:
    s, sp_i, pc_i, cp_i, ps_i = map(int, (sta, sp, pc, cp, ps))
    if sp_i >= s:
        return 0.0
    if pc_i > s or ps_i >= s:
        return offset - offset ** 5 / (40 * w13 ** 2 * length ** 2)
    return 0.0


def cal_spiral_shifty(sta, sp, pc, cp, ps, shiftx, w13, x1) -> float:
    s, sp_i, pc_i, cp_i, ps_i = map(int, (sta, sp, pc, cp, ps))
    if sp_i >= s:
        return 0.0
    if pc_i > s or ps_i >= s:
        return shiftx ** 3 / (6 * w13 * x1)
    return 0.0




# ============================================================
# 메인 선형 계산
# ============================================================
def calculate_curve(
    linestring: LineString,
    radius_list: list[float],
    angles: list[float],
    parameters: list[list[float]],
    unit: int = Config.DEFAULT_UNIT,
    start_sta: float = Config.DEFAULT_START_STA,
) -> tuple[list[list[list[StationRow]]], list[CurveParams], list[tuple[float, float]]]:
    """모든 IP의 선형 계산"""
    station_groups: list[list[list[StationRow]]] = []
    curves: list[CurveParams] = []
    polycurve: list[tuple[float, float]] = []

    tl_list: list[float] = []
    end_sta_list: list[float] = []
    end_xy_list: list[tuple[float, float]] = []

    bp_sta = start_sta
    coords = linestring.coords

    for i in range(len(coords) - 2):
        ia_rad = math.radians(angles[i])
        ia_deg = angles[i]

        bp_xy = (coords[i][0], coords[i][1])
        ip_xy = (coords[i + 1][0], coords[i + 1][1])
        ep_xy = (coords[i + 2][0], coords[i + 2][1])

        h1 = calculate_bearing_n(*bp_xy, *ip_xy)
        h2 = calculate_bearing_n(*ip_xy, *ep_xy)
        ip_dist1 = calculate_distance(*bp_xy, *ip_xy)
        ip_dist2 = calculate_distance(*ip_xy, *ep_xy)

        rc = radius_list[i]
        m, z, v = parameters[i]
        not_spiral_min = dictionary_cubicparabola(v)

        curve_type = "simplecurve" if rc >= not_spiral_min else "cubic"
        direction = find_direction(rc, h1, h2)
        curvedir = "RIGHT CURVE" if direction == 1 else "LEFT CURVE"

        is_last_ip = (i == len(coords) - 3)

        # ---------- 곡선 파라미터 계산 ----------
        if curve_type == "simplecurve":
            theta_pc = 0.0
            sc_params = calculate_simplecurve_parameter(direction, rc, ia_rad)
            tl, cl, sl, s_val, w13 = sc_params

            o_pc_bearing = calculate_o_pc_bearing(h1, theta_pc, w13)
            sp_pc_bearing = h1
            bc_xy, ec_xy = calculate_simplecurve_coordinates(h1, h2, tl, ip_xy)
            center_xy = (
                math.cos(math.radians(o_pc_bearing + 180)) * rc + bc_xy[0],
                math.sin(math.radians(o_pc_bearing + 180)) * rc + bc_xy[1],
            )

            if i == 0:
                ip_sta = bp_sta + ip_dist1
                bc_sta = ip_sta - tl
                ec_sta = bc_sta + cl
            else:
                bp_sta = end_sta_list[i - 1]
                ip_sta = bp_sta + ip_dist1 - tl_list[i - 1]
                bc_sta = ip_sta - tl
                ec_sta = bc_sta + cl

            end_sta_list.append(ec_sta)
            end_xy_list.append(ec_xy)

            curves.append(CurveParams(
                ip_no=i + 1, ip_xy=ip_xy, curve_type=curve_type, direction=curvedir,
                h1=h1, h2=h2, ia_degree=ia_deg, center_xy=center_xy, radius=rc,
                ip_distance1=ip_dist1, ip_distance2=ip_dist2, m=m, z=z, v=v,
                params=sc_params, o_pc_bearing=o_pc_bearing,
                sp_pc_bearing=sp_pc_bearing, theta_pc=theta_pc, ip_sta=ip_sta,
                bc_sta=bc_sta, ec_sta=ec_sta, bc_xy=bc_xy, ec_xy=ec_xy,
            ))

        else:  # cubic
            theta_pc = calculate_theta_pc(m, z, rc)
            cb_params = calculate_cubic_parabola_parameter(m, z, direction, theta_pc, rc, ia_rad)
            x1, x2, w13, L, Y, w15, F, S, K, W, tl, lc, cl, sl, ria, C, B = cb_params

            o_pc_bearing = calculate_o_pc_bearing(h1, theta_pc, w13)
            sp_pc_bearing = calculate_sp_pc_bearing(w13, h1, math.degrees(theta_pc))
            sp_xy, pc_xy, cp_xy, ps_xy = calculate_spiral_coordinates(
                bp_xy, ip_xy, ep_xy, h1, h2, tl, x1, w15, sp_pc_bearing, rc, lc, w13
            )
            center_xy = (
                math.cos(math.radians(o_pc_bearing + 180)) * rc + pc_xy[0],
                math.sin(math.radians(o_pc_bearing + 180)) * rc + pc_xy[1],
            )

            if i == 0:
                ip_sta = bp_sta + ip_dist1
            else:
                bp_sta = end_sta_list[i - 1]
                ip_sta = bp_sta + ip_dist1 - tl_list[i - 1]

            sp_sta = ip_sta - tl
            pc_sta = sp_sta + L
            cp_sta = pc_sta + lc
            ps_sta = cp_sta + L

            if bp_sta > sp_sta:
                logger.warning(
                    "곡선겹침 IP%d: BP=%s, SP=%s",
                    i + 1, format_distance(bp_sta), format_distance(sp_sta),
                )

            end_sta_list.append(ps_sta)
            end_xy_list.append(ps_xy)

            curves.append(CurveParams(
                ip_no=i + 1, ip_xy=ip_xy, curve_type=curve_type, direction=curvedir,
                h1=h1, h2=h2, ia_degree=ia_deg, center_xy=center_xy, radius=rc,
                ip_distance1=ip_dist1, ip_distance2=ip_dist2, m=m, z=z, v=v,
                params=cb_params, o_pc_bearing=o_pc_bearing,
                sp_pc_bearing=sp_pc_bearing, theta_pc=theta_pc, ip_sta=ip_sta,
                sp_sta=sp_sta, pc_sta=pc_sta, cp_sta=cp_sta, ps_sta=ps_sta,
                sp_xy=sp_xy, pc_xy=pc_xy, cp_xy=cp_xy, ps_xy=ps_xy,
            ))

        tl_list.append(tl)

        # 변경 후
        prev_xy = end_xy_list[i - 1] if i > 0 else bp_xy
        end_sta = _compute_end_sta(
            curves[-1],
            base_sta=(curves[-1].ec_sta if curves[-1].curve_type == "simplecurve"
                      else curves[-1].ps_sta),
            ec_xy=(curves[-1].ec_xy or curves[-1].ps_xy),
            ep_xy=ep_xy,
            is_last_ip=is_last_ip,
        )
        station_group = build_station_group(
            curve=curves[-1],
            bp_sta=bp_sta,
            bp_xy=prev_xy,
            end_sta=end_sta,
            unit=unit,
        )
        station_groups.append([station_group])
        polycurve.extend(row.coord for row in station_group)

    return station_groups, curves, polycurve


def _compute_end_sta(curve: CurveParams, base_sta: float, ec_xy, ep_xy, is_last_ip) -> float:
    """마지막 IP면 EP까지 연장"""
    if not is_last_ip:
        return base_sta
    end_xy = ec_xy
    return base_sta + calculate_distance(end_xy[0], end_xy[1], ep_xy[0], ep_xy[1])

