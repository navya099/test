"""
pi_alignment.py
Civil 3D 스타일 PI(교점) 기반 선형 생성 API.

사용 예:
    align = (PIBuilder("도로1")
        .pi(x=167204.47, y=560844.34, azimuth=2.909290715384003)   # 시작 PI
        .curve(delta_deg=30, R=600, Ls=162.3, side='right')          # 곡선
        .pi(x=167546.09, y=559400.29)                                # 다음 PI
        .build()
    )
    align.export_dxf("output.dxf")
"""
from __future__ import annotations

import json
import math
from typing import List, Optional, Tuple

import numpy as np
from scipy.special import fresnel

# 기존 엔진 import (파일명은 실제 환경에 맞게 수정)
from alignment import (   # 또는 alignment_api 의존 파일
    Alignment,
    AlignmentLine,
    AlignmentArc,
    AlignmentSpiral,
    CivilDocument,
    _az_to_unit_vec,
    _wrap_angle_diff,
)


# ===========================================================================
# 완화곡선 기하 파라미터 (p, q) 계산
# ===========================================================================
def _spiral_pq_JCubic(R: float, Ls: float) -> Tuple[float, float]:
    """Japanese Cubic Spiral 의 p(이동량), q(접선오프셋) 정확 계산."""
    # X0: s(X0) = Ls 를 만족하는 종점 X (뉴턴법, 16점 Gauss-Legendre)
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

    # 완화곡선 끝점 로컬 좌표 (s=Ls)
    Y0 = (X0 ** 3) / (6.0 * R * X0)          # = X0² / (6R)
    phi0 = math.atan((X0 * X0) / (2.0 * R * X0))  # = atan(X0/(2R))

    p = Y0 - R * (1.0 - math.cos(phi0))
    q = X0 - R * math.sin(phi0)
    return p, q, X0, Y0, phi0


def _spiral_pq_Clothoid(R: float, Ls: float) -> Tuple[float, float, float, float, float]:
    """표준 Clothoid 의 p, q (정확한 적분 기반)."""
    scale = math.sqrt(math.pi * R * Ls)
    S, C = fresnel(Ls / scale)
    X0 = scale * C
    Y0 = scale * S
    phi0 = (Ls * Ls) / (2.0 * R * Ls)   # = Ls / (2R)
    p = Y0 - R * (1.0 - math.cos(phi0))
    q = X0 - R * math.sin(phi0)
    return p, q, X0, Y0, phi0


def _spiral_pq(R: float, Ls: float, spiral_type: str) -> Tuple[float, float]:
    """완화곡선 타입에 따른 p, q 반환."""
    if spiral_type in ("258", "JapaneseCubic", "SpiralType.JapaneseCubic"):
        p, q, _, _, _ = _spiral_pq_JCubic(R, Ls)
    else:
        p, q, _, _, _ = _spiral_pq_Clothoid(R, Ls)
    return p, q


# ===========================================================================
# 편각(Δ) 계산 헬퍼
# ===========================================================================
def _delta_from_pi(prev_pi, curr_pi, next_pi) -> float:
    """세 PI 점으로부터 편각(교각, 라디안) 계산."""
    a1 = math.atan2(curr_pi[0] - prev_pi[0], curr_pi[1] - prev_pi[1])
    a2 = math.atan2(next_pi[0] - curr_pi[0], next_pi[1] - curr_pi[1])
    return _wrap_angle_diff(a2, a1)


# ===========================================================================
# PI 기반 곡선 요소 계산
# ===========================================================================
def _compute_curve_elements(
    pi_pt: Tuple[float, float],
    az_in: float,
    delta: float,
    R: float,
    Ls: float,
    spiral_type: str = "258",
) -> dict:
    """PI, 편각, R, Ls 로부터 TS/SC/CS/ST 및 접선장 계산.

    Args:
        pi_pt: PI 좌표
        az_in: PI 직전 접선 방위각 (rad)
        delta: 편각 (rad, 부호: +우회전 CW, -좌회전 CCW)
        R: 원호 반지름
        Ls: 완화곡선 길이 (Ls=0 → 완화곡선 없음)

    Returns:
        dict with ts, sc, cs, st, T, az_in, az_out, is_cw, arc_len, ...
    """
    if R <= 0:
        raise ValueError("R 은 양수여야 합니다.")
    if Ls < 0:
        raise ValueError("Ls 는 0 이상이어야 합니다.")

    is_cw = delta > 0.0
    abs_delta = abs(delta)

    # 완화곡선이 없으면 순수 원호
    if Ls == 0.0:
        p, q = 0.0, 0.0
    else:
        p, q = _spiral_pq(R, Ls, spiral_type)

    # 접선장 T = (R + p)·tan(Δ/2) + q
    T = (R + p) * math.tan(abs_delta / 2.0) + q

    # PI 직전/직후 접선 방향
    tx_in, ty_in = _az_to_unit_vec(az_in)      # PI 로 들어오는 방향
    az_out = az_in + delta                      # PI 이후 방향
    tx_out, ty_out = _az_to_unit_vec(az_out)

    px, py = pi_pt
    # TS: PI 에서 접선 역방향으로 T 만큼
    ts = (px - T * tx_in, py - T * ty_in)
    # ST: PI 에서 접선 정방향으로 T 만큼
    st = (px + T * tx_out, py + T * ty_out)

    # SC, CS: TS/ST 에서 완화곡선 Ls 진행한 점
    if Ls > 0.0:
        sc = _advance_along_spiral(ts, az_in, R, Ls, is_cw, is_entry=True,
                                    spiral_type=spiral_type)
        # CS 는 ST 에서 역방향 진입(즉 exit spiral 의 시작)
        cs = _advance_along_spiral(st, az_out + math.pi, R, Ls, is_cw,
                                    is_entry=True, spiral_type=spiral_type)
    else:
        sc = ts
        cs = st

    # 원호 길이
    phi0 = 0.0 if Ls == 0.0 else (
        _spiral_pq_JCubic(R, Ls)[4] if spiral_type in ("258", "JapaneseCubic")
        else _spiral_pq_Clothoid(R, Ls)[4]
    )
    arc_central_angle = abs_delta - 2.0 * phi0
    arc_len = R * arc_central_angle

    return {
        "pi": pi_pt,
        "ts": ts, "sc": sc, "cs": cs, "st": st,
        "T": T, "p": p, "q": q, "phi0": phi0,
        "az_in": az_in, "az_out": az_out,
        "is_cw": is_cw, "arc_len": arc_len,
        "arc_central_angle": arc_central_angle,
    }


def _advance_along_spiral(start_pt, az_in, R, Ls, is_cw, is_entry,
                           spiral_type) -> Tuple[float, float]:
    """주어진 시작점/방위각에서 완화곡선을 Ls 진행한 끝점."""
    if spiral_type in ("258", "JapaneseCubic", "SpiralType.JapaneseCubic"):
        _, _, X0, Y0, _ = _spiral_pq_JCubic(R, Ls)
        u, v = X0, Y0
    else:
        _, _, X0, Y0, _ = _spiral_pq_Clothoid(R, Ls)
        u, v = X0, Y0
    v_signed = v if is_cw else -v
    tx, ty = _az_to_unit_vec(az_in)
    nx, ny = math.cos(az_in), -math.sin(az_in)
    return start_pt[0] + u * tx + v_signed * nx, start_pt[1] + u * ty + v_signed * ny


# ===========================================================================
# PIBuilder
# ===========================================================================
class PIBuilder:
    """PI(교점) 방식 선형 빌더.

    Civil 3D 와 동일한 입력(접선 + PI + R + Ls)으로 선형 생성.

    사용:
        b = PIBuilder("도로")
        b.start(x=..., y=..., azimuth=...)          # 최초 접선 시작점
        b.curve(delta_deg=30, R=600, Ls=162.3)      # 첫 PI 에서 곡선
        # 또는 PI 좌표 직접 지정:
        b.start_pi(x=..., y=..., azimuth=...)
        b.curve(delta_deg=30, R=600, Ls=162.3)
    """

    def __init__(self, name: str = "Alignment", starting_station: float = 0.0):
        self.name = name
        self.starting_station = starting_station
        self._subs: List = []
        self._cursor_pt: Optional[Tuple[float, float]] = None
        self._cursor_az: Optional[float] = None
        self._cursor_station: float = starting_station

    # -- 시작점 ------------------------------------------------------------
    def start(self, x: float, y: float, azimuth: float, unit: str = "rad") -> "PIBuilder":
        """접선 시작점(첫 요소의 시작점)과 방위각."""
        self._cursor_pt = (float(x), float(y))
        self._cursor_az = math.radians(azimuth) if unit == "deg" else float(azimuth)
        self._cursor_station = self.starting_station
        return self

    def start_pi(self, x: float, y: float, azimuth: float, unit: str = "rad",
                 lead_length: float = 0.0) -> "PIBuilder":
        """PI 좌표 + 접선 방위각으로 시작. lead_length 만큼 앞쪽 접선 생성."""
        az = math.radians(azimuth) if unit == "deg" else float(azimuth)
        px, py = float(x), float(y)
        if lead_length > 0:
            tx, ty = _az_to_unit_vec(az)
            start_pt = (px - lead_length * tx, py - lead_length * ty)
            self._cursor_pt = start_pt
            self._cursor_az = az
            self._cursor_station = self.starting_station
            # lead 접선 추가
            self.line(length=lead_length)
            # 이제 cursor 는 PI 위치에 있음
        else:
            self._cursor_pt = (px, py)
            self._cursor_az = az
            self._cursor_station = self.starting_station
        return self

    # -- 직선 (접선) -------------------------------------------------------
    def line(self, length: float) -> "PIBuilder":
        """현재 방위각으로 직선 추가."""
        self._require_start()
        if length <= 0:
            raise ValueError("line: length > 0 필요")
        x0, y0 = self._cursor_pt
        az = self._cursor_az
        dx, dy = _az_to_unit_vec(az)
        x1, y1 = x0 + length * dx, y0 + length * dy
        sub = AlignmentLine(
            start_station=self._cursor_station,
            end_station=self._cursor_station + length,
            length=length,
            start_pt=(x0, y0), end_pt=(x1, y1),
            direction=az,
        )
        self._advance(sub, (x1, y1), az, length)
        return self

    # -- PI 기반 곡선 -------------------------------------------------------
    def curve(
        self,
        *,
        delta_deg: Optional[float] = None,
        delta: Optional[float] = None,
        R: float,
        Ls: float = 0.0,
        Le: Optional[float] = None,     # Ls 와 동일 (Civil 3D 호환)
        pi: Optional[Tuple[float, float]] = None,
        side: Optional[str] = None,     # 'left'|'right' (미지정 시 delta 부호)
        spiral_type: str = "258",
    ) -> "PIBuilder":
        """PI 기반 곡선(진입 완화 + 원호 + 진출 완화) 추가.

        Args:
            delta_deg / delta: 편각 (도 또는 라디안). 부호로 회전방향 결정.
            R: 원호 반지름
            Ls: 진입 완화곡선 길이 (0 이면 순수 원호)
            Le: 진출 완화곡선 길이 (미지정 시 Ls 와 동일)
            pi: PI 좌표 (미지정 시 접선 교점을 자동 계산)
            side: 'left'|'right' (지정 시 delta 부호 무시)
            spiral_type: '258' (JCubic) | '257' (Clothoid)
        """
        self._require_start()
        if delta_deg is None and delta is None:
            raise ValueError("curve: delta_deg 또는 delta 필요")
        if Le is None:
            Le = Ls
        if Ls != Le:
            raise NotImplementedError("Ls ≠ Le 는 아직 미지원 (추후 확장)")

        d = math.radians(delta_deg) if delta_deg is not None else float(delta)
        if side is not None:
            if side == "right":
                d = abs(d)
            elif side == "left":
                d = -abs(d)
            else:
                raise ValueError("side 는 'left' 또는 'right'")

        az_in = self._cursor_az
        start_pt = self._cursor_pt

        # PI 자동 계산: 현재 접선이 다음 접선과 만나는 점
        if pi is None:
            # 접선 방향 az_in 에서 delta 만큼 꺾이는 PI 를 역산
            # TS 위치 = start_pt (곡선의 시작점이 현재 커서라고 가정)
            # T 를 먼저 계산하고 PI = TS + T·(접선방향)
            p, q = _spiral_pq(R, Ls, spiral_type) if Ls > 0 else (0.0, 0.0)
            T = (R + p) * math.tan(abs(d) / 2.0) + q
            tx, ty = _az_to_unit_vec(az_in)
            pi_pt = (start_pt[0] + T * tx, start_pt[1] + T * ty)
        else:
            pi_pt = (float(pi[0]), float(pi[1]))

        elem = _compute_curve_elements(
            pi_pt=pi_pt, az_in=az_in, delta=d, R=R, Ls=Ls,
            spiral_type=spiral_type,
        )

        ts, sc, cs, st = elem["ts"], elem["sc"], elem["cs"], elem["st"]
        az_out = elem["az_out"]
        is_cw = elem["is_cw"]

        # 현재 커서(ts) 에서 ts 로 이동하는 접선이 이미 있는지 확인
        # 없으면 ts 까지 직선 추가 (PI 자동계산 시 start_pt == ts 이므로 생략)
        cur = self._cursor_pt
        if math.hypot(cur[0] - ts[0], cur[1] - ts[1]) > 1e-9:
            # 커서에서 ts 까지 접선 직선 추가
            dx, dy = ts[0] - cur[0], ts[1] - cur[1]
            L_lead = math.hypot(dx, dy)
            az_lead = math.atan2(dx, dy)
            # 방위각이 az_in 과 일치하는지 확인
            if abs(_wrap_angle_diff(az_lead, az_in)) > 1e-9:
                raise ValueError(
                    f"커서({cur})에서 TS({ts})까지 방위각 불일치: "
                    f"{math.degrees(az_lead):.4f}° vs {math.degrees(az_in):.4f}°"
                )
            self.line(length=L_lead)

        # (1) 진입 완화곡선: TS → SC
        if Ls > 0:
            spir_in = AlignmentSpiral(
                start_station=self._cursor_station,
                end_station=self._cursor_station + Ls,
                length=Ls,
                start_pt=ts, end_pt=sc,
                radius_in=math.inf, radius_out=R,
                direction_in=az_in,
                direction_out=az_in + (elem["phi0"] if is_cw else -elem["phi0"]),
                spiral_type=spiral_type,
            )
            self._advance(spir_in, sc,
                          spir_in.direction_out, Ls)

        # (2) 원호: SC → CS
        arc_az_in = self._cursor_az
        arc_az_out = az_out + (-elem["phi0"] if is_cw else elem["phi0"])
        # 중심 계산
        if is_cw:
            nx, ny = math.cos(arc_az_in), -math.sin(arc_az_in)
        else:
            nx, ny = -math.cos(arc_az_in), math.sin(arc_az_in)
        cx = sc[0] + R * nx
        cy = sc[1] + R * ny
        arc = AlignmentArc(
            start_station=self._cursor_station,
            end_station=self._cursor_station + elem["arc_len"],
            length=elem["arc_len"],
            start_pt=sc, end_pt=cs,
            center_pt=(cx, cy), radius=R, clockwise=is_cw,
            direction_in=arc_az_in, direction_out=arc_az_out,
        )
        self._advance(arc, cs, arc_az_out, elem["arc_len"])

        # (3) 진출 완화곡선: CS → ST
        if Ls > 0:
            spir_out = AlignmentSpiral(
                start_station=self._cursor_station,
                end_station=self._cursor_station + Ls,
                length=Ls,
                start_pt=cs, end_pt=st,
                radius_in=R, radius_out=math.inf,
                direction_in=arc_az_out,
                direction_out=az_out,
                spiral_type=spiral_type,
            )
            self._advance(spir_out, st, az_out, Ls)

        return self

    # -- PI 점으로 자동 진행 ------------------------------------------------
    def through_pi(self, x: float, y: float, azimuth_to_next: float,
                    unit: str = "rad") -> "PIBuilder":
        """다음 PI 점을 지정하고 접선만 진행 (curve 는 별도 호출)."""
        self._require_start()
        cur = self._cursor_pt
        dx, dy = x - cur[0], y - cur[1]
        L = math.hypot(dx, dy)
        if L < 1e-9:
            raise ValueError("through_pi: 현재 커서와 PI 가 같습니다.")
        az_actual = math.atan2(dx, dy)
        if abs(_wrap_angle_diff(az_actual, self._cursor_az)) > 1e-6:
            raise ValueError(
                f"through_pi: 현재 접선방위 {math.degrees(self._cursor_az):.4f}° "
                f"와 PI 방향 {math.degrees(az_actual):.4f}° 가 다릅니다. "
                f"먼저 line() 으로 PI 까지 이동하거나 azimuth 를 조정하세요."
            )
        self.line(length=L)
        return self

    # -- build / export ----------------------------------------------------
    def build(self) -> Alignment:
        if not self._subs:
            raise ValueError("빌드할 요소가 없습니다.")
        align = Alignment(name=self.name, starting_station=self.starting_station)
        align.sub_entities = self._subs
        return align

    def export_dxf(self, path: str, spiral_tolerance: float = 1e-6) -> None:
        doc = CivilDocument()
        doc.alignments.append(self.build())
        doc.export_dxf(path, spiral_tolerance=spiral_tolerance)

    def save_json(self, path: str) -> None:
        from alignment_api import _sub_to_dict   # 재사용
        align = self.build()
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

    # -- 내부 --------------------------------------------------------------
    def _require_start(self) -> None:
        if self._cursor_pt is None:
            raise RuntimeError("먼저 .start(...) 또는 .start_pi(...) 를 호출하세요.")

    def _advance(self, sub, pt, az, length) -> None:
        self._subs.append(sub)
        self._cursor_pt = pt
        self._cursor_az = az
        self._cursor_station += length


# ===========================================================================
# 최상위 편의 함수
# ===========================================================================
def create_pi_alignment(name: str = "Alignment") -> PIBuilder:
    return PIBuilder(name)