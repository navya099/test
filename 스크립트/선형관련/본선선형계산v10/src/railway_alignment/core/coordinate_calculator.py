"""
선형 좌표 계산 (Coordinate Calculator) 모듈
=============================================
곡선 타입별 계산기:
  - SimpleCurveCoordinateCalculator
  - CubicCoordinateCalculator
  - StraightCoordinateCalculator (R=0, PI에서 h1→h2 전환)
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

import numpy as np

from src.railway_alignment.core.math_util import calculate_distance
from src.railway_alignment.core.tangent_calculator import Zone, _classify_zone


# ============================================================
# 좌표 컨텍스트
# ============================================================
@dataclass(frozen=True)
class CurveGeometry:
    """좌표 계산에 필요한 기하 정보"""

    h1: float
    h2: float
    sp_pc_bearing: float
    w13: float

    sp_sta: float
    pc_sta: float
    cp_sta: float
    ps_sta: float

    bp_xy: tuple[float, float]
    sp_xy: tuple[float, float]
    center_xy: tuple[float, float]
    ps_xy: tuple[float, float]

    shiftx: float = 0.0
    shifty: float = 0.0

    # ✅ straight(직선 IP) 분기용
    bp_sta: float = 0.0


@dataclass(frozen=True)
class CoordinateResult:
    x: float
    y: float

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


# ============================================================
# 추상 베이스
# ============================================================
class CoordinateCalculator(ABC):
    @abstractmethod
    def compute(self, sta: float, offset: float, geometry: CurveGeometry) -> CoordinateResult:
        ...

    @staticmethod
    def _straight_from_bp(h: float, offset: float, bp: tuple[float, float]) -> CoordinateResult:
        rad = math.radians(h)
        return CoordinateResult(
            x=math.cos(rad) * offset + bp[0],
            y=math.sin(rad) * offset + bp[1],
        )

    @staticmethod
    def _straight_from_ps(h2: float, offset: float, ps: tuple[float, float]) -> CoordinateResult:
        rad = math.radians(h2)
        return CoordinateResult(
            x=math.cos(rad) * offset + ps[0],
            y=math.sin(rad) * offset + ps[1],
        )

    @staticmethod
    def _spiral_offset(
        h: float, shiftx: float, shifty: float,
        anchor: tuple[float, float], flip: bool = False,
    ) -> CoordinateResult:
        if not flip:
            x = math.cos(math.radians(h + 90)) * shifty + math.cos(math.radians(h)) * shiftx + anchor[0]
            y = math.sin(math.radians(h + 90)) * shifty + math.sin(math.radians(h)) * shiftx + anchor[1]
        else:
            x = math.cos(math.radians(h + 90)) * shifty + math.cos(math.radians(h + 180)) * shiftx + anchor[0]
            y = math.sin(math.radians(h + 90)) * shifty + math.sin(math.radians(h + 180)) * shiftx + anchor[1]
        return CoordinateResult(x=x, y=y)

    @staticmethod
    def _circular(
        sp_pc_bearing: float, offset: float,
        w13: float, center: tuple[float, float],
    ) -> CoordinateResult:
        angle = sp_pc_bearing - 90 + (180 * offset) / math.pi / w13
        return CoordinateResult(
            x=math.cos(math.radians(angle)) * w13 + center[0],
            y=math.sin(math.radians(angle)) * w13 + center[1],
        )


# ============================================================
# 단곡선
# ============================================================
class SimpleCurveCoordinateCalculator(CoordinateCalculator):
    def compute(self, sta, offset, geometry):
        bc = geometry.sp_sta
        ec = geometry.cp_sta

        if sta <= bc:
            return self._straight_from_bp(geometry.h1, offset, geometry.bp_xy)
        if sta <= ec:
            return self._circular(
                geometry.sp_pc_bearing, offset, geometry.w13, geometry.center_xy
            )
        return self._straight_from_ps(geometry.h2, offset, geometry.ps_xy)


# ============================================================
# 직선 IP (R=0): BP~IP는 h1, IP~EP는 h2
# ============================================================
class StraightCoordinateCalculator(CoordinateCalculator):
    """직선 IP: BP~IP는 h1 방향, IP~EP는 h2 방향 (선형 보간 방식)."""

    def compute(self, sta: float, offset: float, geometry: CurveGeometry) -> CoordinateResult:
        ip_sta = geometry.sp_sta
        bp_sta = geometry.bp_sta

        # 1. IP 교점과 정확히 일치하는 경우
        if abs(sta - ip_sta) < 1e-4:
            return CoordinateResult(x=geometry.sp_xy[0], y=geometry.sp_xy[1])

        # 2. BP ~ IP 구간 (교점 이전)
        if sta < ip_sta:
            total_len = ip_sta - bp_sta
            if total_len < 1e-6:
                return CoordinateResult(x=geometry.sp_xy[0], y=geometry.sp_xy[1])
            ratio = (sta - bp_sta) / total_len
            x = geometry.bp_xy[0] + (geometry.sp_xy[0] - geometry.bp_xy[0]) * ratio
            y = geometry.bp_xy[1] + (geometry.sp_xy[1] - geometry.bp_xy[1]) * ratio
            return CoordinateResult(x=x, y=y)

        # 3. IP ~ EP 구간 (교점 이후)
        else:
            ep_xy = geometry.ps_xy  # build_geometry_from_curve에서 마지막 IP일 때 EP 좌표가 들어감
            import math
            dist_ip_ep = math.hypot(ep_xy[0] - geometry.sp_xy[0], ep_xy[1] - geometry.sp_xy[1])
            ip_offset = sta - ip_sta
            if dist_ip_ep < 1e-6:
                return CoordinateResult(x=ep_xy[0], y=ep_xy[1])
            ratio = ip_offset / dist_ip_ep
            x = geometry.sp_xy[0] + (ep_xy[0] - geometry.sp_xy[0]) * ratio
            y = geometry.sp_xy[1] + (ep_xy[1] - geometry.sp_xy[1]) * ratio
            return CoordinateResult(x=x, y=y)


# ============================================================
# 3차포물선
# ============================================================
class CubicCoordinateCalculator(CoordinateCalculator):
    def compute(self, sta, offset, geometry):
        zone = _classify_zone(
            sta, geometry.sp_sta, geometry.pc_sta,
            geometry.cp_sta, geometry.ps_sta,
        )
        dispatch = {
            Zone.BEFORE_CURVE: self._bp_to_sp,
            Zone.ENTRY_SPIRAL: self._sp_to_pc,
            Zone.CIRCULAR: self._pc_to_cp,
            Zone.EXIT_SPIRAL: self._cp_to_ps,
            Zone.AFTER_CURVE: self._ps_to_ep,
        }
        return dispatch[zone](sta, offset, geometry)

    def _bp_to_sp(self, sta, offset, g):
        return self._straight_from_bp(g.h1, offset, g.bp_xy)

    def _sp_to_pc(self, sta, offset, g):
        return self._spiral_offset(h=g.h1, shiftx=g.shiftx, shifty=g.shifty, anchor=g.sp_xy, flip=False)

    def _pc_to_cp(self, sta, offset, g):
        return self._circular(g.sp_pc_bearing, offset, g.w13, g.center_xy)

    def _cp_to_ps(self, sta, offset, g):
        return self._spiral_offset(h=g.h2, shiftx=g.shiftx, shifty=g.shifty, anchor=g.ps_xy, flip=True)

    def _ps_to_ep(self, sta, offset, g):
        return self._straight_from_ps(g.h2, offset, g.ps_xy)


# ============================================================
# 팩토리
# ============================================================
def create_coordinate_calculator(curve):
    if curve.curve_type == "simplecurve":
        return SimpleCurveCoordinateCalculator()
    if curve.curve_type == "straight":
        return StraightCoordinateCalculator()
    return CubicCoordinateCalculator()


def build_geometry_from_curve(
    curve, bp_xy, shiftx: float = 0.0, shifty: float = 0.0, bp_sta: float = 0.0,
) -> CurveGeometry:
    if curve.curve_type == "straight":
        ep_xy = getattr(curve, "ep_xy", None) or curve.ip_xy
        return CurveGeometry(
            h1=curve.h1, h2=curve.h2,
            sp_pc_bearing=curve.h1,
            w13=0.0,
            sp_sta=curve.ip_sta, pc_sta=curve.ip_sta,
            cp_sta=curve.ip_sta, ps_sta=curve.ip_sta,
            bp_xy=bp_xy,
            sp_xy=curve.ip_xy,
            center_xy=(math.nan, math.nan),
            ps_xy=ep_xy,  # ✅ 여기에 EP 좌표를 넣어야 IP~EP 보간 가능
            bp_sta=bp_sta,
        )

    if curve.curve_type == "simplecurve":
        return CurveGeometry(
            h1=curve.h1, h2=curve.h2,
            sp_pc_bearing=curve.h1,
            w13=curve.params[4],
            sp_sta=curve.bc_sta,
            pc_sta=curve.bc_sta,
            cp_sta=curve.ec_sta,
            ps_sta=curve.ec_sta,
            bp_xy=bp_xy,
            sp_xy=curve.bc_xy,
            center_xy=curve.center_xy,
            ps_xy=curve.ec_xy,
            bp_sta=bp_sta,
        )

    return CurveGeometry(
        h1=curve.h1, h2=curve.h2,
        sp_pc_bearing=curve.sp_pc_bearing,
        w13=curve.params[2],
        sp_sta=curve.sp_sta,
        pc_sta=curve.pc_sta,
        cp_sta=curve.cp_sta,
        ps_sta=curve.ps_sta,
        bp_xy=bp_xy,
        sp_xy=curve.sp_xy,
        center_xy=curve.center_xy,
        ps_xy=curve.ps_xy,
        shiftx=shiftx, shifty=shifty,
        bp_sta=bp_sta,
    )


# ============================================================
# 좌표 ↔ 측점 조회 (기존 유지)
# ============================================================
def get_station_at_coordinates(p, polycurve, station_groups) -> Optional[float]:
    curve_math = [(y, x) for x, y in polycurve]
    apoint, index = perpendicular_point_on_curve(p, curve_math)
    if apoint is None:
        return None

    dest_x, dest_y = curve_math[index]
    dest_x_i, dest_y_i = int(dest_x), int(dest_y)

    for group in station_groups:
        for subgroup in group:
            for row in subgroup:
                cy, cx = row.coord
                if int(cx) == dest_x_i and int(cy) == dest_y_i:
                    return row.sta + calculate_distance(cx, cy, apoint[0], apoint[1])
    return None


def perpendicular_point_on_curve(p, curve):
    px, py = p
    for i in range(len(curve) - 1):
        x1, y1 = curve[i]
        x2, y2 = curve[i + 1]
        line_vec = np.array([x2 - x1, y2 - y1])
        point_vec = np.array([px - x1, py - y1])
        line_len_sq = float(np.dot(line_vec, line_vec))
        if line_len_sq == 0:
            continue
        t = float(np.dot(point_vec, line_vec)) / line_len_sq
        if 0 <= t <= 1:
            return (x1 + t * line_vec[0], y1 + t * line_vec[1]), i
    return None, None