"""
선형 계산 (핵심)
==================
curve.py 리팩터:
- tl_list/end_sta_list/end_xy_list 3개 리스트 제거 → prev_* 로컬 변수
- bp_sta 재할당 → prev_end_sta로 명확화
- curves[-1] 반복 참조 → curve 로컬 변수
- ec_xy or ps_xy falsy 오판 → curve_type 명시 분기
- center_xy / ip_sta 계산 중복 → 헬퍼로 통합
- _compute_end_sta 인라인화 (내부 전용)
"""

import math
import logging

from shapely.geometry.linestring import LineString

from src.railway_alignment.core.cant import dictionary_cubicparabola
from src.railway_alignment.core.constants import Config
from src.railway_alignment.core.math_util import (
    calculate_bearing_n,
    calculate_distance,
    find_direction,
    format_distance,
)
from src.railway_alignment.core.models import StationRow, CurveParams
from src.railway_alignment.core.station_builder import build_station_group

logger = logging.getLogger(__name__)


# ============================================================
# 기하 계산 (수식 원본 유지)
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
# 내부 헬퍼 (리팩터)
# ============================================================
def _shift_by_bearing(bearing_deg: float, dist: float, ref_xy) -> tuple[float, float]:
    """ref_xy에서 (bearing_deg + 180) 방향으로 dist만큼 이동한 좌표.

    곡선 중심(center_xy) 계산에 사용.
    """
    rad = math.radians(bearing_deg + 180)
    return (math.cos(rad) * dist + ref_xy[0], math.sin(rad) * dist + ref_xy[1])


def _compute_ip_sta(
    i: int, prev_end_sta: float, ip_dist1: float, prev_tl: float,
) -> float:
    """IP 정측점 계산.

    - 첫 IP: BP + 거리
    - 이후 IP: 이전 곡선 종점 + 거리 - 이전 접선장
    """
    if i == 0:
        return prev_end_sta + ip_dist1
    return prev_end_sta + ip_dist1 - prev_tl


def _resolve_end_xy(curve: CurveParams) -> tuple[float, float]:
    """곡선 타입에 따라 종점 좌표(ec_xy 또는 ps_xy) 반환."""
    end_xy = curve.ec_xy if curve.curve_type == "simplecurve" else curve.ps_xy
    if end_xy is None:
        raise ValueError(
            f"IP{curve.ip_no}: {curve.curve_type} 종점 좌표가 없습니다."
        )
    return end_xy


def _resolve_end_sta(curve: CurveParams) -> float:
    """곡선 타입에 따라 종점 측점(ec_sta 또는 ps_sta) 반환."""
    end_sta = curve.ec_sta if curve.curve_type == "simplecurve" else curve.ps_sta
    if end_sta is None:
        raise ValueError(
            f"IP{curve.ip_no}: {curve.curve_type} 종점 측점이 없습니다."
        )
    return end_sta


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
    type_overrides: dict[int, str] | None = None,
) -> tuple[list[list[list[StationRow]]], list[CurveParams], list[tuple[float, float]]]:
    """모든 IP의 선형 계산.

    Parameters
    ----------
    linestring : LineString
        BP, IP1, ..., IPN, EP 순서의 좌표
    radius_list : list[float]
        각 IP의 곡선 반경 (IP1..IPN)
    angles : list[float]
        각 IP의 교각 (도)
    parameters : list[list[float]]
        각 IP의 [M, Z, V]
    unit : int
        측점 간격 (m)
    start_sta : float
        시작 측점 (BP)
    type_overrides : dict[int, str] | None
        ip_no(1-based) → "simplecurve"/"cubic" 타입 오버라이드
    """
    type_overrides = type_overrides or {}

    station_groups: list[list[list[StationRow]]] = []
    curves: list[CurveParams] = []
    polycurve: list[tuple[float, float]] = []

    coords = linestring.coords
    n_ips = len(coords) - 2

    # 반복문 상태 (이전 곡선의 종점 정보)
    prev_end_sta: float = start_sta
    prev_end_xy: tuple[float, float] = (coords[0][0], coords[0][1])   # BP
    prev_tl: float = 0.0

    for i in range(n_ips):
        ip_no = i + 1
        is_last_ip = (i == n_ips - 1)

        ia_deg = angles[i]
        ia_rad = math.radians(ia_deg)

        bp_xy = (coords[i][0], coords[i][1])
        ip_xy = (coords[i + 1][0], coords[i + 1][1])
        ep_xy = (coords[i + 2][0], coords[i + 2][1])

        h1 = calculate_bearing_n(*bp_xy, *ip_xy)
        h2 = calculate_bearing_n(*ip_xy, *ep_xy)
        ip_dist1 = calculate_distance(*bp_xy, *ip_xy)
        ip_dist2 = calculate_distance(*ip_xy, *ep_xy)

        rc = radius_list[i]
        m, z, v = parameters[i]
        # ✅ R=0: 직선 IP (곡선 없음, 꺾임만)
        if rc == 0:
            direction = find_direction(rc, h1, h2)
            curvedir = "RIGHT CURVE" if direction == 1 else "LEFT CURVE"

            ip_sta = _compute_ip_sta(i, prev_end_sta, ip_dist1, prev_tl)

            curve = CurveParams(
                ip_no=ip_no, ip_xy=ip_xy, curve_type="straight",
                direction=curvedir,
                h1=h1, h2=h2, ia_degree=ia_deg,
                center_xy=(math.nan, math.nan), radius=0.0,
                ip_distance1=ip_dist1, ip_distance2=ip_dist2,
                m=0, z=0, v=0, params=[0.0],
                o_pc_bearing=h1, sp_pc_bearing=h1,
                theta_pc=0.0, ip_sta=ip_sta,
                ps_xy=ep_xy if is_last_ip else ip_xy,  # ✅ 여기에 EP 저장!
                ep_xy=ep_xy if is_last_ip else None,  # ✅ 이 줄 추가
            )
            curves.append(curve)

            if is_last_ip:
                extended_sta = ip_sta + calculate_distance(
                    ip_xy[0], ip_xy[1], ep_xy[0], ep_xy[1],
                )
            else:
                extended_sta = ip_sta

            station_group = build_station_group(
                curve=curve, bp_sta=prev_end_sta, bp_xy=prev_end_xy,
                end_sta=extended_sta, unit=unit,
            )
            station_groups.append([station_group])
            polycurve.extend([row.coord for row in station_group])

            prev_end_sta = ip_sta
            prev_end_xy = ip_xy
            prev_tl = 0.0
            continue
        not_spiral_min = dictionary_cubicparabola(v)

        # 곡선 타입 결정 (오버라이드 우선)
        if ip_no in type_overrides:
            curve_type = type_overrides[ip_no]
        else:
            curve_type = "simplecurve" if rc >= not_spiral_min else "cubic"

        direction = find_direction(rc, h1, h2)
        curvedir = "RIGHT CURVE" if direction == 1 else "LEFT CURVE"

        # IP 정측점 (공통)
        ip_sta = _compute_ip_sta(i, prev_end_sta, ip_dist1, prev_tl)

        # ── 곡선별 파라미터 계산 ──
        if curve_type == "simplecurve":
            theta_pc = 0.0
            sc_params = calculate_simplecurve_parameter(direction, rc, ia_rad)
            tl, cl, sl, s_val, w13 = sc_params

            o_pc_bearing = calculate_o_pc_bearing(h1, theta_pc, w13)
            sp_pc_bearing = h1
            bc_xy, ec_xy = calculate_simplecurve_coordinates(h1, h2, tl, ip_xy)
            center_xy = _shift_by_bearing(o_pc_bearing, rc, bc_xy)

            bc_sta = ip_sta - tl
            ec_sta = bc_sta + cl

            curve = CurveParams(
                ip_no=ip_no, ip_xy=ip_xy, curve_type=curve_type,
                direction=curvedir,
                h1=h1, h2=h2, ia_degree=ia_deg,
                center_xy=center_xy, radius=rc,
                ip_distance1=ip_dist1, ip_distance2=ip_dist2,
                m=m, z=z, v=v, params=sc_params,
                o_pc_bearing=o_pc_bearing,
                sp_pc_bearing=sp_pc_bearing,
                theta_pc=theta_pc, ip_sta=ip_sta,
                bc_sta=bc_sta, ec_sta=ec_sta,
                bc_xy=bc_xy, ec_xy=ec_xy,
            )
            end_sta = ec_sta
            end_xy = ec_xy

        else:  # cubic
            theta_pc = calculate_theta_pc(m, z, rc)
            cb_params = calculate_cubic_parabola_parameter(
                m, z, direction, theta_pc, rc, ia_rad,
            )
            (x1, x2, w13, L, Y, w15, F, S, K, W,
             tl, lc, cl, sl, ria, C, B) = cb_params

            o_pc_bearing = calculate_o_pc_bearing(h1, theta_pc, w13)
            sp_pc_bearing = calculate_sp_pc_bearing(
                w13, h1, math.degrees(theta_pc),
            )
            sp_xy, pc_xy, cp_xy, ps_xy = calculate_spiral_coordinates(
                bp_xy, ip_xy, ep_xy, h1, h2, tl,
                x1, w15, sp_pc_bearing, rc, lc, w13,
            )
            center_xy = _shift_by_bearing(o_pc_bearing, rc, pc_xy)

            sp_sta = ip_sta - tl
            pc_sta = sp_sta + L
            cp_sta = pc_sta + lc
            ps_sta = cp_sta + L

            if prev_end_sta > sp_sta:
                logger.warning(
                    "곡선겹침 IP%d: BP=%s, SP=%s",
                    ip_no,
                    format_distance(prev_end_sta),
                    format_distance(sp_sta),
                )

            curve = CurveParams(
                ip_no=ip_no, ip_xy=ip_xy, curve_type=curve_type,
                direction=curvedir,
                h1=h1, h2=h2, ia_degree=ia_deg,
                center_xy=center_xy, radius=rc,
                ip_distance1=ip_dist1, ip_distance2=ip_dist2,
                m=m, z=z, v=v, params=cb_params,
                o_pc_bearing=o_pc_bearing,
                sp_pc_bearing=sp_pc_bearing,
                theta_pc=theta_pc, ip_sta=ip_sta,
                sp_sta=sp_sta, pc_sta=pc_sta,
                cp_sta=cp_sta, ps_sta=ps_sta,
                sp_xy=sp_xy, pc_xy=pc_xy,
                cp_xy=cp_xy, ps_xy=ps_xy,
            )
            end_sta = ps_sta
            end_xy = ps_xy

        curves.append(curve)

        # ── 마지막 IP면 EP까지 연장 ──
        if is_last_ip:
            extended_sta = end_sta + calculate_distance(
                end_xy[0], end_xy[1], ep_xy[0], ep_xy[1],
            )
        else:
            extended_sta = end_sta

        # ── 측점 그룹 생성 ──
        station_group = build_station_group(
            curve=curve,
            bp_sta=prev_end_sta,
            bp_xy=prev_end_xy,
            end_sta=extended_sta,
            unit=unit,
        )
        station_groups.append([station_group])
        polycurve.extend([row.coord for row in station_group])

        # ── 다음 반복용 상태 갱신 ──
        prev_end_sta = end_sta
        prev_end_xy = end_xy
        prev_tl = tl

    return station_groups, curves, polycurve