"""
alignment_wrapper.py
최상위 래퍼: BP, PIDATA(PI1, PI2, ...), EP 로 선형 생성.

사용 예:
    from alignment_wrapper import create_alignment_from_pi, PIDATA

    align = create_alignment_from_pi(
        name="도로1",
        points=[
            (167204.4669, 560844.3363),                    # BP
            PIDATA("PI1", 167546.0896, 559400.2873, R=600, L1=162.3, L2=162.3),
            PIDATA("PI2", 167576.2915, 559240.9558, R=500, L1=162.43, L2=162.43),
            (167494.3509, 558860.3856),                    # EP
        ],
    )
    align.export_dxf("output.dxf", spiral_tolerance=1e-6)
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
from scipy.optimize import root
from scipy.special import fresnel

# 기존 엔진 import (파일명 환경에 맞게 수정)
from alignment import (
    Alignment,
    AlignmentLine,
    AlignmentArc,
    AlignmentSpiral,
    CivilDocument,
    _az_to_unit_vec,
    _wrap_angle_diff,
)


# ===========================================================================
# PIDATA
# ===========================================================================
@dataclass
class PIDATA:
    """PI(교점) 데이터. Civil 3D PI 테이블과 1:1 대응.

    Attributes:
        name: PI 이름 (예: "PI1")
        x, y: PI 좌표
        R:    원호 반지름 [m]. R=0 이면 직선으로 통과.
        L1:   진입 완화곡선 길이 [m]. 0 이면 완화곡선 없음.
        L2:   진출 완화곡선 길이 [m]. 0 이면 완화곡선 없음.
        side: 'left' | 'right' | None. None 이면 Δ 부호로 자동.
        spiral_type: '258' (JCubic) | '257' (Clothoid). None 이면 래퍼 기본값.
    """
    name: str
    x: float
    y: float
    R: float = 0.0
    L1: float = 0.0
    L2: float = 0.0
    side: Optional[str] = None
    spiral_type: Optional[str] = None

    @property
    def pt(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def __repr__(self) -> str:
        return (f"PIDATA({self.name!r}, x={self.x:.4f}, y={self.y:.4f}, "
                f"R={self.R}, L1={self.L1}, L2={self.L2})")


# ===========================================================================
# 완화곡선 로컬 기하 (p, q, phi) — 단일/양방향
# ===========================================================================
def _spiral_local_geom(R: float, Ls: float, spiral_type: str
                        ) -> Tuple[float, float, float, float, float]:
    """완화곡선 로컬 기하 반환: (X0, Y0, phi0, p, q)"""
    if Ls <= 0.0:
        return 0.0, 0.0, 0.0, 0.0, 0.0

    if spiral_type in ("258", "JapaneseCubic", "SpiralType.JapaneseCubic"):
        gx, gw = np.polynomial.legendre.leggauss(16)
        X0 = Ls
        u = 0.5 * (gx + 1.0)
        u4 = u ** 4
        for _ in range(60):
            k = X0 / (2.0 * R)
            sq = np.sqrt(1.0 + (k * k) * u4)
            I = 0.5 * float(np.sum(gw * sq))
            f = X0 * I - Ls
            if abs(f) < 1e-13 * Ls:
                break
            dI = 0.5 * float(np.sum(gw * ((X0 / (4.0 * R * R)) * u4 / sq)))
            X0 -= f / (I + X0 * dI)
        Y0 = (X0 ** 3) / (6.0 * R * X0)
        phi0 = math.atan((X0 * X0) / (2.0 * R * X0))
    else:
        scale = math.sqrt(math.pi * R * Ls)
        S, C = fresnel(Ls / scale)
        X0 = scale * C
        Y0 = scale * S
        phi0 = (Ls * Ls) / (2.0 * R * Ls)

    p = Y0 - R * (1.0 - math.cos(phi0))
    q = X0 - R * math.sin(phi0)
    return X0, Y0, phi0, p, q


# ===========================================================================
# 편각/방위 계산
# ===========================================================================
def _az_between(p_from: Tuple[float, float], p_to: Tuple[float, float]) -> float:
    return math.atan2(p_to[0] - p_from[0], p_to[1] - p_from[1])


def _delta_at_pi(prev_pt, pi_pt, next_pt) -> float:
    az_in = _az_between(prev_pt, pi_pt)
    az_out = _az_between(pi_pt, next_pt)
    return _wrap_angle_diff(az_out, az_in)


# ===========================================================================
# 대칭 완화곡선 (L1 == L2): 닫힌 형태 정확 공식
# ===========================================================================
def _compute_symmetric(
    pi_pt, az_in, delta, R, Ls, spiral_type
) -> Dict:
    abs_delta = abs(delta)
    is_cw = delta > 0.0
    az_out = az_in + delta

    if Ls > 0.0:
        X0, Y0, phi0, p, q = _spiral_local_geom(R, Ls, spiral_type)
    else:
        X0 = Y0 = phi0 = p = q = 0.0

    T = (R + p) * math.tan(abs_delta / 2.0) + q

    tx_in, ty_in = _az_to_unit_vec(az_in)
    tx_out, ty_out = _az_to_unit_vec(az_out)

    ts = (pi_pt[0] - T * tx_in, pi_pt[1] - T * ty_in)
    st = (pi_pt[0] + T * tx_out, pi_pt[1] + T * ty_out)

    if Ls > 0.0:
        nx, ny = math.cos(az_in), -math.sin(az_in)
        v_signed = Y0 if is_cw else -Y0
        sc = (ts[0] + X0 * tx_in + v_signed * nx,
              ts[1] + X0 * ty_in + v_signed * ny)

        az_out_rev = az_out + math.pi
        txr, tyr = _az_to_unit_vec(az_out_rev)
        nxr, nyr = math.cos(az_out_rev), -math.sin(az_out_rev)
        v_signed_out = -Y0 if is_cw else Y0
        cs = (st[0] + X0 * txr + v_signed_out * nxr,
              st[1] + X0 * tyr + v_signed_out * nyr)
    else:
        sc, cs = ts, st

    arc_central = abs_delta - 2.0 * phi0
    arc_len = R * max(arc_central, 0.0)

    return dict(
        ts=ts, sc=sc, cs=cs, st=st,
        T=T, p1=p, q1=q, phi1=phi0,
        p2=p, q2=q, phi2=phi0,
        az_in=az_in, az_out=az_out, is_cw=is_cw,
        arc_len=arc_len, arc_central=arc_central,
        delta=delta, R=R, L1=Ls, L2=Ls,
        symmetric=True, pi=pi_pt,
    )


# ===========================================================================
# 비대칭 완화곡선 (L1 != L2): 수치 해
# ===========================================================================
def _compute_asymmetric(
    pi_pt, az_in, delta, R, L1, L2, spiral_type
) -> Dict:
    """L1 != L2 비대칭 완화곡선의 TS/SC/CS/ST 를 수치로 푼다.

    미지수: u = (T_in, T_out)
    방정식:
      (1) TS 에서 L1 진행한 SC 가 원호 위에 있어야 함
      (2) ST 에서 L2 역진행한 CS 가 같은 원호 위에 있어야 함
      (3) 원호의 두 끝 SC, CS 에서 접선 방향이 완화곡선 phi1, phi2 와 일치
    → 단순화: 원호중심 C 를 매개로 2 미지수 T_in, T_out 을 푼다.
    """
    abs_delta = abs(delta)
    is_cw = delta > 0.0
    az_out = az_in + delta

    _, _, phi1, p1, q1 = _spiral_local_geom(R, L1, spiral_type)
    _, _, phi2, p2, q2 = _spiral_local_geom(R, L2, spiral_type)

    # 로컬 좌표계: PI 원점, az_in = +Y
    tx_in, ty_in = _az_to_unit_vec(az_in)
    tx_out, ty_out = _az_to_unit_vec(az_out)

    # 회전 부호: is_cw=+1, ccw=-1
    sgn = 1.0 if is_cw else -1.0

    # 국소 좌표 변환 (PI 원점, az_in 을 +Y 축으로)
    # 회전: PI 원점 기준, az_in 만큼 반시계 회전
    def to_local(pt):
        dx = pt[0] - pi_pt[0]
        dy = pt[1] - pi_pt[1]
        c = math.cos(-az_in)
        s = math.sin(-az_in)
        return (dx * c - dy * s, dx * s + dy * c)

    def to_global(lp):
        c = math.cos(az_in)
        s = math.sin(az_in)
        return (pi_pt[0] + lp[0] * c - lp[1] * s,
                pi_pt[1] + lp[0] * s + lp[1] * c)

    # 로컬에서 az_out 방향 = delta 만큼 회전 (Y축 기준 시계방향 양)
    # 로컬 +Y = az_in. 로컬 az_out 방향 벡터 = (sin(delta), cos(delta))
    out_local = (math.sin(delta), math.cos(delta))

    def residual(x):
        T_in, T_out = x
        if T_in <= 0 or T_out <= 0:
            return [1e6, 1e6]

        # TS: PI 로부터 -Y 로 T_in
        ts_local = (0.0, -T_in)
        # ST: PI + T_out * out_local
        st_local = (T_out * out_local[0], T_out * out_local[1])

        # SC = TS + 진입 완화곡선 로컬좌표 변환
        #   진입완화: 진행 +Y 방향, 법선은 진행 우측(+X) * sgn
        #   로컬 (X0, Y0) 에서 X0 = 진행방향, Y0 = 좌측 오프셋
        #   여기서는 Civil3D 규약: 진행 +Y, 우측 = +X
        X0_1, Y0_1, _, _, _ = _spiral_local_geom(R, L1, spiral_type)
        sc_local = (
            ts_local[0] + sgn * Y0_1,
            ts_local[1] + X0_1,
        )

        # CS = ST - 진출 완화곡선 (역방향)
        X0_2, Y0_2, _, _, _ = _spiral_local_geom(R, L2, spiral_type)
        # 역방향 = out_local 반대로 진행
        cs_local = (
            st_local[0] - sgn * Y0_2 * out_local[1],   # 근사
            st_local[1] - X0_2 * out_local[1],
        )
        # 더 정확히는 진출 완화곡선을 out_local 방향으로 진행한 점을 ST 로 잡고,
        # 그 시작점이 CS. 여기서는 (2) SC, CS 가 원호 위에 있어야 함을 이용.
        # 원호: |SC - C| = |CS - C| = R, 접선방향 SC=+Y, CS=out_local
        # C 는 SC 에서 진행 우측으로 R 만큼
        C_local = (
            sc_local[0] + sgn * R,   # 우측
            sc_local[1] + 0.0,       # SC 접선 +Y 이므로 우측은 +X
        )
        # CS 는 C 로부터 거리 R, 각도: SC 에서 out_local 회전까지
        # 진출 완화곡선 방향 접선 = out_local. CS 에서 C 로 가는 벡터는 -out_local 회전
        # 접선방향 out_local 의 좌측 R 만큼 = C
        # 즉 C = CS + R * (out_local 의 좌측 법선)
        # 좌측 법선: out_local 회전 (+90° 시계방향 반전) = (-out_local[1], out_local[0]) * sgn
        # 검증 대신 수치 방정식으로 처리
        # 방정식 1: |CS - C| = R
        # 방정식 2: CS 에서 C 로의 벡터가 out_local 의 (좌/우) 법선과 평행
        #   -out_local 회전 후 방향
        ex = cs_local[0] - C_local[0]
        ey = cs_local[1] - C_local[1]
        f1 = ex * ex + ey * ey - R * R

        # 접선 방향 일치: CS 에서의 접선이 out_local 과 평행
        # C→CS 방향을 out_local 좌측법선(-out_local[1], out_local[0]) * sgn 로 매핑
        # 여기서는 단순화: CS - C 방향이 out_local 좌측법선과 평행
        tang_pred = (-out_local[1] * sgn, out_local[0] * sgn)  # 예상 C→CS
        f2 = ex * tang_pred[0] + ey * tang_pred[1]

        return [f1, f2]

    # 초기 추정: 대칭 근사
    T_in0 = q1 + (R + p1) * math.tan(abs_delta / 2.0)
    T_out0 = q2 + (R + p2) * math.tan(abs_delta / 2.0)
    sol = root(residual, [T_in0, T_out0], method='hybr')
    if not sol.success or sol.x[0] <= 0 or sol.x[1] <= 0:
        raise RuntimeError(
            f"비대칭 완화곡선 수렴 실패 (PI={pi_pt}, R={R}, "
            f"L1={L1}, L2={L2}, delta={math.degrees(delta):.4f}°): {sol.message}"
        )
    T_in, T_out = float(sol.x[0]), float(sol.x[1])

    # 최종 좌표 재계산 (글로벌)
    ts = (pi_pt[0] - T_in * tx_in, pi_pt[1] - T_in * ty_in)
    st = (pi_pt[0] + T_out * tx_out, pi_pt[1] + T_out * ty_out)

    nx_in, ny_in = math.cos(az_in), -math.sin(az_in)
    X0_1, Y0_1, _, _, _ = _spiral_local_geom(R, L1, spiral_type)
    v1 = Y0_1 if is_cw else -Y0_1
    sc = (ts[0] + X0_1 * tx_in + v1 * nx_in,
          ts[1] + X0_1 * ty_in + v1 * ny_in)

    az_out_rev = az_out + math.pi
    txr, tyr = _az_to_unit_vec(az_out_rev)
    nxr, nyr = math.cos(az_out_rev), -math.sin(az_out_rev)
    X0_2, Y0_2, _, _, _ = _spiral_local_geom(R, L2, spiral_type)
    v2 = -Y0_2 if is_cw else Y0_2
    cs = (st[0] + X0_2 * txr + v2 * nxr,
          st[1] + X0_2 * tyr + v2 * nyr)

    arc_central = abs_delta - phi1 - phi2
    arc_len = R * max(arc_central, 0.0)

    return dict(
        ts=ts, sc=sc, cs=cs, st=st,
        T=None, p1=p1, q1=q1, phi1=phi1,
        p2=p2, q2=q2, phi2=phi2,
        az_in=az_in, az_out=az_out, is_cw=is_cw,
        arc_len=arc_len, arc_central=arc_central,
        delta=delta, R=R, L1=L1, L2=L2,
        symmetric=False, pi=pi_pt,
    )


# ===========================================================================
# 디스패처
# ===========================================================================
def _compute_curve(
    pi_pt, az_in, delta, R, L1, L2, spiral_type
) -> Dict:
    """대칭/비대칭 자동 분기."""
    if abs(L1 - L2) < 1e-9:
        return _compute_symmetric(pi_pt, az_in, delta, R, max(L1, L2), spiral_type)
    return _compute_asymmetric(pi_pt, az_in, delta, R, L1, L2, spiral_type)


# ===========================================================================
# 최상위 래퍼
# ===========================================================================
def create_alignment_from_pi(
    name: str,
    points: Sequence[Union[Tuple[float, float], PIDATA]],
    *,
    starting_station: float = 0.0,
    spiral_type: str = "258",
) -> Alignment:
    """BP, PIDATA(PI1..), EP 로 선형 생성.

    Args:
        name: 선형 이름
        points: 점 목록.
            - (x, y) 튜플: BP 또는 EP
            - PIDATA 객체: PI (중간점)
            최소 2개. PIDATA 가 하나도 없으면 직선만 생성.
        starting_station: 시작 측점
        spiral_type: 기본 완화곡선 타입 ('258' JCubic, '257' Clothoid).
            PIDATA.spiral_type 이 있으면 개별 우선.

    Returns:
        Alignment (기존 엔진 객체). point_location, point_locations_many,
        export_dxf 등 모두 사용 가능.
    """
    if len(points) < 2:
        raise ValueError("points 는 최소 2개(BP, EP) 필요합니다.")

    # 좌표 추출 + PIDATA 인덱스 매핑
    pts: List[Tuple[float, float]] = []
    pi_data: Dict[int, PIDATA] = {}
    for i, p in enumerate(points):
        if isinstance(p, PIDATA):
            pts.append((p.x, p.y))
            pi_data[i] = p
        else:
            pts.append((float(p[0]), float(p[1])))

    # 중간 점이 PIDATA 가 아니면 경고 (직선 통과)
    # BP/EP 가 PIDATA 면 오류
    if 0 in pi_data or (len(points) - 1) in pi_data:
        raise ValueError("BP/EP 는 (x, y) 튜플이어야 합니다. PIDATA 는 중간 PI 에만.")

    subs: List = []
    cursor_pt = pts[0]
    cursor_station = starting_station

    def append_line_to(target_pt: Tuple[float, float]) -> None:
        nonlocal cursor_pt, cursor_station
        dx = target_pt[0] - cursor_pt[0]
        dy = target_pt[1] - cursor_pt[1]
        L = math.hypot(dx, dy)
        if L < 1e-12:
            return
        az = math.atan2(dx, dy)
        subs.append(AlignmentLine(
            start_station=cursor_station,
            end_station=cursor_station + L,
            length=L,
            start_pt=cursor_pt,
            end_pt=target_pt,
            direction=az,
        ))
        cursor_pt = target_pt
        cursor_station += L

    # ---- 각 PI 순회 ----
    for i in range(1, len(pts) - 1):
        pi = pts[i]
        prev_pt = pts[i - 1]
        next_pt = pts[i + 1]

        delta = _delta_at_pi(prev_pt, pi, next_pt)
        az_in = _az_between(prev_pt, pi)

        pinfo = pi_data.get(i)
        if pinfo is None or pinfo.R <= 0.0:
            # 곡선 없음 → 직선으로 PI 통과
            append_line_to(pi)
            continue

        # side / delta 부호
        if pinfo.side == "left":
            delta = -abs(delta)
        elif pinfo.side == "right":
            delta = abs(delta)
        # None 이면 자동

        stype = pinfo.spiral_type or spiral_type
        L1 = pinfo.L1
        L2 = pinfo.L2 if pinfo.L2 > 0 else pinfo.L1  # L2 미지정 → L1 동일

        # Δ 가 0 이면 그냥 직선
        if abs(delta) < 1e-9:
            append_line_to(pi)
            continue

        elem = _compute_curve(
            pi_pt=pi, az_in=az_in, delta=delta,
            R=pinfo.R, L1=L1, L2=L2, spiral_type=stype,
        )

        # (1) 현재 커서 → TS
        append_line_to(elem["ts"])

        # (2) 진입 완화곡선 TS → SC
        if L1 > 0.0:
            az_sc = az_in + (elem["phi1"] if elem["is_cw"] else -elem["phi1"])
            subs.append(AlignmentSpiral(
                start_station=cursor_station,
                end_station=cursor_station + L1,
                length=L1,
                start_pt=elem["ts"], end_pt=elem["sc"],
                radius_in=math.inf, radius_out=pinfo.R,
                direction_in=az_in, direction_out=az_sc,
                spiral_type=stype,
            ))
            cursor_pt = elem["sc"]
            cursor_station += L1
        else:
            az_sc = az_in

        # (3) 원호 SC → CS
        if elem["arc_len"] > 1e-9:
            az_cs = elem["az_out"] - (elem["phi2"] if elem["is_cw"] else -elem["phi2"])
            if elem["is_cw"]:
                nx, ny = math.cos(az_sc), -math.sin(az_sc)
            else:
                nx, ny = -math.cos(az_sc), math.sin(az_sc)
            cx = elem["sc"][0] + pinfo.R * nx
            cy = elem["sc"][1] + pinfo.R * ny
            subs.append(AlignmentArc(
                start_station=cursor_station,
                end_station=cursor_station + elem["arc_len"],
                length=elem["arc_len"],
                start_pt=elem["sc"], end_pt=elem["cs"],
                center_pt=(cx, cy), radius=pinfo.R, clockwise=elem["is_cw"],
                direction_in=az_sc, direction_out=az_cs,
            ))
            cursor_pt = elem["cs"]
            cursor_station += elem["arc_len"]
        else:
            az_cs = az_sc

        # (4) 진출 완화곡선 CS → ST
        if L2 > 0.0:
            subs.append(AlignmentSpiral(
                start_station=cursor_station,
                end_station=cursor_station + L2,
                length=L2,
                start_pt=elem["cs"], end_pt=elem["st"],
                radius_in=pinfo.R, radius_out=math.inf,
                direction_in=az_cs, direction_out=elem["az_out"],
                spiral_type=stype,
            ))
            cursor_pt = elem["st"]
            cursor_station += L2

    # ---- 마지막 접선: 커서 → EP ----
    append_line_to(pts[-1])

    align = Alignment(name=name, starting_station=starting_station)
    align.sub_entities = subs
    return align


# ===========================================================================
# 요약 / 저장 편의
# ===========================================================================
def print_alignment_summary(align: Alignment) -> None:
    """선형 요소 요약 출력."""
    print(f"\n=== {align.name} ===")
    print(f"  Length: {align.length:.6f} m  "
          f"(Station {align.starting_station:.3f} ~ {align.ending_station:.3f})")
    print(f"  {'#':>3} {'Type':<8} {'Station':>14} {'Length':>10} "
          f"{'Start (x, y)':>32} {'Az_in':>9} {'Az_out':>9}")
    for i, sub in enumerate(align.sub_entities, 1):
        tname = type(sub).__name__.replace("Alignment", "")
        az_in = getattr(sub, "direction",
                         getattr(sub, "direction_in", float("nan")))
        az_out = getattr(sub, "direction",
                          getattr(sub, "direction_out", float("nan")))
        print(f"  {i:>3} {tname:<8} {sub.start_station:>14.4f} "
              f"{sub.length:>10.4f} ({sub.start_pt[0]:>14.4f}, "
              f"{sub.start_pt[1]:>14.4f}) {math.degrees(az_in):>8.4f}° "
              f"{math.degrees(az_out):>8.4f}°")


def export_alignment_to_dxf(align: Alignment, path: str,
                             spiral_tolerance: float = 1e-6) -> None:
    """DXF 저장 (Civil 3D 호환)."""
    doc = CivilDocument()
    doc.alignments.append(align)
    doc.export_dxf(path, spiral_tolerance=spiral_tolerance)


def save_alignment_to_json(align: Alignment, path: str) -> None:
    """golden JSON 저장."""
    from alignment_api import _sub_to_dict
    data = {
        "name": align.name,
        "starting_station": align.starting_station,
        "ending_station": align.ending_station,
        "length": align.length,
        "entities": [],
        "checkpoints": [],
    }
    for i, sub in enumerate(align.sub_entities):
        data["entities"].append({
            "id": i + 1,
            "type": getattr(sub, "spiral_type", "257"),
            "class_name": type(sub).__name__,
            "sub_entities": [_sub_to_dict(sub)],
        })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)