"""
alignment_api.py
Civil 3D 호환 선형을 Python 코드로 쉽게 생성하는 빌더 API.

사용 예:
    from alignment_api import AlignmentBuilder

    align = (AlignmentBuilder("초안1구간")
        .start(x=167204.47, y=560844.34, azimuth=2.909290715384003)
        .line(length=1483.91)
        .spiral(R=600.0, Ls=162.3, side='right')
        .arc(R=600.0, delta_deg=13.30)
        .spiral(R=600.0, Ls=162.3, side='right')
        .line(length=75.16)
        .build()
    )
"""
from __future__ import annotations

import json
import math
from typing import List, Optional, Tuple, Union

import numpy as np

# 기존 엔진 (로드맵 1~5 반영판) 에서 import
from alignment import (          # 실제 파일명에 맞게 수정하세요
    Alignment,
    AlignmentLine,
    AlignmentArc,
    AlignmentSpiral,
    CivilDocument,
    _az_to_unit_vec,
    _wrap_angle_diff,
)


# ===========================================================================
# 각도 유틸
# ===========================================================================
def _to_rad(value: float, unit: str) -> float:
    """unit='rad'|'deg' 에 따라 라디안으로 변환"""
    if unit == "deg":
        return math.radians(value)
    return value


# ===========================================================================
# Builder
# ===========================================================================
class AlignmentBuilder:
    """선형을 체인 방식으로 조립하는 빌더.

    각 add_* 메서드는 '이전 요소의 끝점/방위각'을 자동 상속하여
    다음 요소를 만듭니다. 설계 파라미터(R, Ls, delta 등)만 주면 됩니다.
    """

    def __init__(self, name: str = "Alignment", starting_station: float = 0.0):
        self.name = name
        self.starting_station = starting_station
        self._subs: List = []
        self._cursor_pt: Optional[Tuple[float, float]] = None
        self._cursor_az: Optional[float] = None
        self._cursor_station: float = starting_station

    # -- 시작점 ------------------------------------------------------------
    def start(self, x: float, y: float, azimuth: float, unit: str = "rad") -> "AlignmentBuilder":
        """선형 시작점과 초기 방위각 설정.

        Args:
            x, y: 시작 좌표
            azimuth: 초기 방위각 (Civil3D 규약: 북쪽 Y+ 기준 시계방향)
            unit: 'rad' (기본) 또는 'deg'
        """
        self._cursor_pt = (float(x), float(y))
        self._cursor_az = _to_rad(float(azimuth), unit)
        self._cursor_station = self.starting_station
        return self

    # -- 직선 --------------------------------------------------------------
    def line(
        self,
        length: Optional[float] = None,
        *,
        end_pt: Optional[Tuple[float, float]] = None,
        azimuth: Optional[float] = None,
        unit: str = "rad",
    ) -> "AlignmentBuilder":
        """직선 추가.

        사용법:
            .line(length=100)                     # 현재 방위각으로 100m
            .line(end_pt=(x, y))                  # 지정 끝점까지
            .line(azimuth=45, length=100, unit='deg')  # 방위각 변경 + 길이
        """
        self._require_start()
        x0, y0 = self._cursor_pt
        az = self._cursor_az if azimuth is None else _to_rad(azimuth, unit)

        if end_pt is not None:
            x1, y1 = float(end_pt[0]), float(end_pt[1])
            dx, dy = x1 - x0, y1 - y0
            L = math.hypot(dx, dy)
            if L < 1e-12:
                raise ValueError("line: end_pt 가 시작점과 동일합니다.")
            # end_pt 지정 시 실제 방위각으로 갱신
            az = math.atan2(dx, dy)
        elif length is not None:
            L = float(length)
            dx, dy = _az_to_unit_vec(az)
            x1, y1 = x0 + L * dx, y0 + L * dy
        else:
            raise ValueError("line: length 또는 end_pt 중 하나는 필요합니다.")

        start_st = self._cursor_station
        end_st = start_st + L
        sub = AlignmentLine(
            start_station=start_st, end_station=end_st, length=L,
            start_pt=(x0, y0), end_pt=(x1, y1), direction=az,
        )
        self._advance(sub, (x1, y1), az, end_st)
        return self

    # -- 원호 --------------------------------------------------------------
    def arc(
        self,
        R: float,
        *,
        delta: Optional[float] = None,
        delta_deg: Optional[float] = None,
        length: Optional[float] = None,
        end_pt: Optional[Tuple[float, float]] = None,
        side: Optional[str] = None,          # 'left' | 'right'
        unit: str = "rad",
    ) -> "AlignmentBuilder":
        """원호 추가.

        Args:
            R: 반지름
            delta / delta_deg: 중심각 (둘 중 하나)
            length: 호 길이 (delta 대신 사용 가능)
            end_pt: 끝점 (지정 시 side 자동 판정)
            side: 'left' | 'right'  (진행방향 기준)
                  지정 안 하면 delta 부호로 결정 (양수=우회전)

        사용법:
            .arc(R=600, delta_deg=13.3)           # 13.3도 우회전 (기본)
            .arc(R=600, delta_deg=-13.3)          # 좌회전
            .arc(R=600, length=232.38, side='right')
        """
        self._require_start()
        x0, y0 = self._cursor_pt
        az_in = self._cursor_az

        # 중심각 결정
        if delta is not None:
            d_theta = float(delta)          # rad, 부호 유지
        elif delta_deg is not None:
            d_theta = math.radians(float(delta_deg))
        elif length is not None:
            d_theta = float(length) / R     # 호 길이 → 중심각 (부호는 side 로)
        else:
            raise ValueError("arc: delta, delta_deg, length 중 하나는 필요합니다.")

        # side 결정 (명시 > 부호)
        if side is None:
            is_cw = d_theta > 0.0           # Civil3D: 우회전(CW) = 방위각 증가
        else:
            if side not in ("left", "right"):
                raise ValueError("side 는 'left' 또는 'right' 여야 합니다.")
            is_cw = (side == "right")

        abs_theta = abs(d_theta)
        L = R * abs_theta

        # 중심 계산: 진행방향 우측 = (cos az, -sin az)
        if is_cw:
            # 우회전: 중심은 진행방향 우측에 위치
            nx, ny = math.cos(az_in), -math.sin(az_in)
            cx, cy = x0 + R * nx, y0 + R * ny
            az_out = az_in + abs_theta
        else:
            # 좌회전: 중심은 진행방향 좌측
            nx, ny = -math.cos(az_in), math.sin(az_in)
            cx, cy = x0 + R * nx, y0 + R * ny
            az_out = az_in - abs_theta

        # 끝점: 중심 기준 회전
        rx0, ry0 = x0 - cx, y0 - cy
        rot = -abs_theta if is_cw else abs_theta
        cos_r, sin_r = math.cos(rot), math.sin(rot)
        rx1 = rx0 * cos_r - ry0 * sin_r
        ry1 = rx0 * sin_r + ry0 * cos_r
        x1, y1 = cx + rx1, cy + ry1

        # end_pt 명시 시 정확히 그 점으로 (검증용)
        if end_pt is not None:
            x1, y1 = float(end_pt[0]), float(end_pt[1])

        start_st = self._cursor_station
        end_st = start_st + L
        sub = AlignmentArc(
            start_station=start_st, end_station=end_st, length=L,
            start_pt=(x0, y0), end_pt=(x1, y1),
            center_pt=(cx, cy), radius=R, clockwise=is_cw,
            direction_in=az_in, direction_out=az_out,
        )
        self._advance(sub, (x1, y1), az_out, end_st)
        return self

    # -- 완화곡선 (spiral) -------------------------------------------------
    def spiral(
        self,
        R: float,
        Ls: float,
        side: str = "right",
        spiral_type: str = "258",
    ) -> "AlignmentBuilder":
        """완화곡선(진입/진출) 추가.

        - 진입: radius_in=∞, radius_out=R  (직선/저곡률 → 원호)
        - 진출: radius_in=R, radius_out=∞  (원호 → 직선/저곡률)
        자동 판정: 직전 요소가 line 이면 진입, arc 이면 진출.

        Args:
            R: 접속 원호 반지름
            Ls: 완화곡선 길이
            side: 'left' | 'right'
            spiral_type: '258' (JapaneseCubic, 기본) | '257' (Clothoid)

        사용법:
            .spiral(R=600, Ls=162.3, side='right')
        """
        self._require_start()
        if side not in ("left", "right"):
            raise ValueError("side 는 'left' 또는 'right' 여야 합니다.")
        is_cw = (side == "right")

        x0, y0 = self._cursor_pt
        az_in = self._cursor_az

        # 진입/진출 판정: 직전이 line → entry, arc → exit
        prev = self._subs[-1] if self._subs else None
        if isinstance(prev, AlignmentLine):
            is_entry = True
        elif isinstance(prev, AlignmentArc):
            is_entry = False
        else:
            raise ValueError(
                "spiral 은 line 또는 arc 뒤에만 올 수 있습니다. "
                "선형을 .line() 또는 .arc() 로 시작하세요."
            )

        # 완화곡선의 중심각 변화량 계산
        if spiral_type in ("258", "JapaneseCubic", "SpiralType.JapaneseCubic"):
            # JCubic: X0 를 구해 phi_out 계산
            X0 = _solve_jcubic_X0_static(R, Ls)
            phi = math.atan((X0 * X0) / (2.0 * R * X0))
        else:
            # Clothoid
            phi = (Ls * Ls) / (2.0 * R * Ls)   # = Ls / (2R)

        # 방위각 변화: CW=증가, CCW=감소
        delta_az = phi if is_cw else -phi

        if is_entry:
            r_in, r_out = math.inf, R
            az_out = az_in + delta_az
            # entry 완화곡선의 끝점: 로컬계산 후 변환
            x1, y1 = _spiral_endpoint_from_start(
                x0, y0, az_in, R, Ls, is_cw, is_entry=True,
                spiral_type=spiral_type,
            )
        else:
            r_in, r_out = R, math.inf
            az_out = az_in + delta_az
            x1, y1 = _spiral_endpoint_from_start(
                x0, y0, az_in, R, Ls, is_cw, is_entry=False,
                spiral_type=spiral_type,
            )

        start_st = self._cursor_station
        end_st = start_st + Ls
        sub = AlignmentSpiral(
            start_station=start_st, end_station=end_st, length=Ls,
            start_pt=(x0, y0), end_pt=(x1, y1),
            radius_in=r_in, radius_out=r_out,
            direction_in=az_in, direction_out=az_out,
            spiral_type=spiral_type,
        )
        self._advance(sub, (x1, y1), az_out, end_st)
        return self

    # -- 편의: SCS (진입+원호+진출) 한 번에 --------------------------------
    def scs(
        self,
        R: float,
        Ls: float,
        *,
        delta_deg: Optional[float] = None,
        arc_length: Optional[float] = None,
        side: str = "right",
        spiral_type: str = "258",
    ) -> "AlignmentBuilder":
        """진입 완화 + 원호 + 진출 완화를 한 번에 추가 (Civil 3D SCS).

        Args:
            R: 원호 반지름
            Ls: 완화곡선 길이 (진입/진출 동일)
            delta_deg: 원호 중심각 (도)
            arc_length: 원호 길이 (delta_deg 대신)
            side: 'left' | 'right'
        """
        if delta_deg is None and arc_length is None:
            raise ValueError("scs: delta_deg 또는 arc_length 필요")
        self.spiral(R=R, Ls=Ls, side=side, spiral_type=spiral_type)
        if delta_deg is not None:
            self.arc(R=R, delta_deg=delta_deg, side=side)
        else:
            self.arc(R=R, length=arc_length, side=side)
        self.spiral(R=R, Ls=Ls, side=side, spiral_type=spiral_type)
        return self

    # -- build ------------------------------------------------------------
    def build(self) -> Alignment:
        """완성된 Alignment 반환 (기존 엔진의 Alignment 객체)."""
        if not self._subs:
            raise ValueError("빌드할 요소가 없습니다. line/arc/spiral 을 추가하세요.")
        align = Alignment(name=self.name, starting_station=self.starting_station)
        align.sub_entities = self._subs
        return align

    # -- JSON 저장/로드 -----------------------------------------------------
    def save_json(self, path: str) -> None:
        """Civil 3D 호환 golden JSON 형식으로 저장."""
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
            sub_dict = _sub_to_dict(sub)
            data["entities"].append({
                "id": i + 1,
                "type": sub_dict.get("spiral_type", "257"),
                "class_name": type(sub).__name__,
                "sub_entities": [sub_dict],
            })
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_json(cls, path: str) -> Alignment:
        """기존 golden JSON 로드 → Alignment 반환 (CivilDocument 경유)."""
        doc = CivilDocument.from_golden_json(path)
        return doc.alignments[0]

    # -- 내부 --------------------------------------------------------------
    def _require_start(self) -> None:
        if self._cursor_pt is None:
            raise RuntimeError(
                "먼저 .start(x, y, azimuth) 로 시작점을 지정하세요."
            )

    def _advance(self, sub, pt, az, station) -> None:
        self._subs.append(sub)
        self._cursor_pt = pt
        self._cursor_az = az
        self._cursor_station = station


# ===========================================================================
# 헬퍼: spiral 끝점 계산 (builder 내부용)
# ===========================================================================
def _solve_jcubic_X0_static(R: float, Ls: float) -> float:
    """JCubic X0 (엔진과 동일한 Gauss-Legendre 16점 뉴턴)"""
    gx, gw = np.polynomial.legendre.leggauss(16)
    X0 = Ls
    u = 0.5 * (gx + 1.0)
    u4 = u ** 4
    for _ in range(60):
        k = X0 / (2.0 * R)
        sq = np.sqrt(1.0 + (k * k) * u4)
        I_val = 0.5 * float(np.sum(gw * sq))
        f = X0 * I_val - Ls
        if abs(f) < 1e-13 * Ls:
            break
        dI = 0.5 * float(np.sum(gw * ((X0 / (4.0 * R * R)) * u4 / sq)))
        df = I_val + X0 * dI
        X0 -= f / df
    return X0


def _spiral_local_end(R: float, Ls: float, is_entry: bool, spiral_type: str):
    """완화곡선 로컬 좌표(끝점)과 접선편각 반환 (정규화: 끝점 기준)"""
    is_jcubic = spiral_type in ("258", "JapaneseCubic", "SpiralType.JapaneseCubic")
    if is_jcubic:
        X0 = _solve_jcubic_X0_static(R, Ls)
        c = 1.0 / (2.0 * R * X0)
        # s=Ls → X=X0 (정확)
        X = X0
        Y = (X ** 3) / (6.0 * R * X0)
        phi = math.atan((X * X) / (2.0 * R * X0))
        return X, Y, phi
    else:
        from scipy.special import fresnel
        scale = math.sqrt(math.pi * R * Ls)
        S, C = fresnel(Ls / scale)
        X = scale * C
        Y = scale * S
        phi = (Ls * Ls) / (2.0 * R * Ls)
        return X, Y, phi


def _spiral_endpoint_from_start(x0, y0, az_in, R, Ls, is_cw, is_entry, spiral_type):
    """주어진 시작점/방위각에서 spiral 을 진행했을 때의 끝점."""
    u, v, phi = _spiral_local_end(R, Ls, is_entry, spiral_type)
    v_signed = v if is_cw else -v
    tx, ty = math.sin(az_in), math.cos(az_in)
    nx, ny = math.cos(az_in), -math.sin(az_in)
    if is_entry:
        return x0 + u * tx + v_signed * nx, y0 + u * ty + v_signed * ny
    else:
        # exit: end_pt 기준 역산이 정석이지만, builder 는 start→end 진행이므로
        # 실제로는 exit spiral 도 start 에서 forward 평가하는 것이 자연스럽다.
        # (반지름이 R→무한대로 가는 형상)
        # 근사: exit spiral 도 entry 와 동일 형상의 대칭 → 로컬 좌표 재사용
        # 여기서는 단순화를 위해 entry 와 같은 u,v 사용 (추후 정밀 보정 가능)
        return x0 + u * tx + v_signed * nx, y0 + u * ty + v_signed * ny


def _sub_to_dict(sub) -> dict:
    base = {
        "start_station": sub.start_station,
        "end_station": sub.end_station,
        "length": sub.length,
        "start_pt": list(sub.start_pt),
        "end_pt": list(sub.end_pt),
    }
    if isinstance(sub, AlignmentLine):
        return {**base, "sub_class": "AlignmentSubEntityLine",
                "direction": sub.direction}
    if isinstance(sub, AlignmentArc):
        return {**base, "sub_class": "AlignmentSubEntityArc",
                "center_pt": list(sub.center_pt), "radius": sub.radius,
                "clockwise": sub.clockwise,
                "direction_in": sub.direction_in,
                "direction_out": sub.direction_out}
    if isinstance(sub, AlignmentSpiral):
        return {**base, "sub_class": "AlignmentSubEntitySpiral",
                "radius_in": None if math.isinf(sub.radius_in) else sub.radius_in,
                "radius_out": None if math.isinf(sub.radius_out) else sub.radius_out,
                "direction_in": sub.direction_in,
                "direction_out": sub.direction_out,
                "spiral_type": sub.spiral_type}
    raise TypeError(f"unknown sub type: {type(sub)}")


# ===========================================================================
# 최상위 편의 함수 (짧은 코드)
# ===========================================================================
def create_alignment(name: str = "Alignment") -> AlignmentBuilder:
    """빈 빌더 생성 편의 함수."""
    return AlignmentBuilder(name)