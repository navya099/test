"""
선형 좌표 계산 (Coordinate Calculator) 모듈
=============================================
기존 calculate_coordinates 함수를 곡선 타입별 계산기로 분리.

구간별 좌표 계산:
  - BP ~ SP/BC : 접선 직선
  - SP ~ PC    : 진입 완화곡선 (3차포물선)
  - PC ~ CP    : 원곡선
  - CP ~ PS    : 진출 완화곡선
  - PS ~ EP    : 접선 직선
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
# 좌표 컨텍스트 (계산에 필요한 모든 기하 정보)
# ============================================================
@dataclass(frozen=True)
class CurveGeometry:
    """좌표 계산에 필요한 기하 정보 묶음

    기존 calculate_coordinates의 18개 인자를 의미 단위로 그룹화.
    """

    # 방위각
    h1: float                    # 방위각 1 (도)
    h2: float                    # 방위각 2 (도)
    sp_pc_bearing: float         # SP→PC 방위각 (도)

    # 반지름 (부호 포함)
    w13: float                   # -R (RIGHT) 또는 +R (LEFT)

    # 측점
    sp_sta: float                # SP 또는 BC
    pc_sta: float
    cp_sta: float
    ps_sta: float                # PS 또는 EC

    # 주요 좌표
    bp_xy: tuple[float, float]   # BP (또는 이전 IP 끝점)
    sp_xy: tuple[float, float]   # SP 또는 BC
    center_xy: tuple[float, float]  # 원곡선 중심
    ps_xy: tuple[float, float]   # PS 또는 EC

    # 이정량 (완화곡선 계산용)
    shiftx: float = 0.0
    shifty: float = 0.0


@dataclass(frozen=True)
class CoordinateResult:
    """좌표 계산 결과"""

    x: float
    y: float

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


# ============================================================
# 추상 베이스
# ============================================================
class CoordinateCalculator(ABC):
    """곡선 타입별 좌표계산기 인터페이스"""

    @abstractmethod
    def compute(self, sta: float, offset: float, geometry: CurveGeometry) -> CoordinateResult:
        """측점 sta, 측거 offset에 대한 (X, Y) 좌표 계산"""
        ...

    # ---------- 공통 유틸 ----------
    @staticmethod
    def _straight_from_bp(h1: float, offset: float, bp: tuple[float, float]) -> CoordinateResult:
        """BP~SP/BC 직선구간 (h1 방향)"""
        rad = math.radians(h1)
        return CoordinateResult(
            x=math.cos(rad) * offset + bp[0],
            y=math.sin(rad) * offset + bp[1],
        )

    @staticmethod
    def _straight_from_ps(h2: float, offset: float, ps: tuple[float, float]) -> CoordinateResult:
        """PS/EC~EP 직선구간 (h2 방향)"""
        rad = math.radians(h2)
        return CoordinateResult(
            x=math.cos(rad) * offset + ps[0],
            y=math.sin(rad) * offset + ps[1],
        )

    @staticmethod
    def _spiral_offset(
        h: float,
        shiftx: float,
        shifty: float,
        anchor: tuple[float, float],
        flip: bool = False,
    ) -> CoordinateResult:
        """완화곡선 구간 좌표 (이정량 + 접선방향 회전)

        Args:
            h: 접선 방위각 (도)
            shiftx: 이정량 X
            shifty: 이정량 Y
            anchor: 기준점 좌표 (SP 또는 PS)
            flip: True면 진출부 (h+90 → h-90, h+180 → h+180)
        """
        if not flip:
            # 진입부: (h+90)·y + h·x
            x = math.cos(math.radians(h + 90)) * shifty + math.cos(math.radians(h)) * shiftx + anchor[0]
            y = math.sin(math.radians(h + 90)) * shifty + math.sin(math.radians(h)) * shiftx + anchor[1]
        else:
            # 진출부: (h+90)·y + (h+180)·x
            x = math.cos(math.radians(h + 90)) * shifty + math.cos(math.radians(h + 180)) * shiftx + anchor[0]
            y = math.sin(math.radians(h + 90)) * shifty + math.sin(math.radians(h + 180)) * shiftx + anchor[1]
        return CoordinateResult(x=x, y=y)

    @staticmethod
    def _circular(
        sp_pc_bearing: float,
        offset: float,
        w13: float,
        center: tuple[float, float],
    ) -> CoordinateResult:
        """원곡선 구간 (중심 + 반지름 회전)"""
        angle = sp_pc_bearing - 90 + (180 * offset) / math.pi / w13
        return CoordinateResult(
            x=math.cos(math.radians(angle)) * w13 + center[0],
            y=math.sin(math.radians(angle)) * w13 + center[1],
        )


# ============================================================
# 단곡선 좌표계산기
# ============================================================
class SimpleCurveCoordinateCalculator(CoordinateCalculator):
    """단곡선: BP ─ BC ═══ EC ─ EP

    구간: 2개 (BP~BC 직선, BC~EC 원곡선, EC~EP 직선)
    """

    def compute(self, sta: float, offset: float, geometry: CurveGeometry) -> CoordinateResult:
        # 단곡선: sp_sta=bc_sta, pc_sta=bc_sta, cp_sta=ec_sta, ps_sta=ec_sta
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
# 3차포물선 좌표계산기
# ============================================================
class CubicCoordinateCalculator(CoordinateCalculator):
    """3차포물선: BP ─ SP ═══ PC ─── CP ═══ PS ─ EP

    구간: 5개 (BP~SP, SP~PC, PC~CP, CP~PS, PS~EP)
    """

    def compute(self, sta: float, offset: float, geometry: CurveGeometry) -> CoordinateResult:
        zone = _classify_zone(
            sta, geometry.sp_sta, geometry.pc_sta, geometry.cp_sta, geometry.ps_sta
        )
        dispatch = {
            Zone.BEFORE_CURVE: self._bp_to_sp,
            Zone.ENTRY_SPIRAL: self._sp_to_pc,
            Zone.CIRCULAR: self._pc_to_cp,
            Zone.EXIT_SPIRAL: self._cp_to_ps,
            Zone.AFTER_CURVE: self._ps_to_ep,
        }
        return dispatch[zone](sta, offset, geometry)

    # ---------- 구간별 메서드 ----------
    def _bp_to_sp(self, sta: float, offset: float, g: CurveGeometry) -> CoordinateResult:
        """BP ~ SP 직선"""
        return self._straight_from_bp(g.h1, offset, g.bp_xy)

    def _sp_to_pc(self, sta: float, offset: float, g: CurveGeometry) -> CoordinateResult:
        """SP ~ PC 진입 완화곡선"""
        return self._spiral_offset(
            h=g.h1,
            shiftx=g.shiftx,
            shifty=g.shifty,
            anchor=g.sp_xy,
            flip=False,
        )

    def _pc_to_cp(self, sta: float, offset: float, g: CurveGeometry) -> CoordinateResult:
        """PC ~ CP 원곡선"""
        return self._circular(g.sp_pc_bearing, offset, g.w13, g.center_xy)

    def _cp_to_ps(self, sta: float, offset: float, g: CurveGeometry) -> CoordinateResult:
        """CP ~ PS 진출 완화곡선"""
        return self._spiral_offset(
            h=g.h2,
            shiftx=g.shiftx,
            shifty=g.shifty,
            anchor=g.ps_xy,
            flip=True,
        )

    def _ps_to_ep(self, sta: float, offset: float, g: CurveGeometry) -> CoordinateResult:
        """PS ~ EP 직선"""
        return self._straight_from_ps(g.h2, offset, g.ps_xy)


# ============================================================
# 팩토리 + 편의 함수
# ============================================================
def create_coordinate_calculator(curve: "CurveParams") -> CoordinateCalculator:
    """곡선 타입에 맞는 계산기 생성"""
    if curve.curve_type == "simplecurve":
        return SimpleCurveCoordinateCalculator()
    return CubicCoordinateCalculator()


def build_geometry_from_curve(
    curve: "CurveParams",
    bp_xy: tuple[float, float],
    shiftx: float = 0.0,
    shifty: float = 0.0,
) -> CurveGeometry:
    """CurveParams + BP 좌표로부터 CurveGeometry 생성

    단곡선/3차포물선의 필드 차이를 흡수.
    """
    if curve.curve_type == "simplecurve":
        # 단곡선: BC→SP, EC→PS로 매핑
        return CurveGeometry(
            h1=curve.h1,
            h2=curve.h2,
            sp_pc_bearing=curve.h1,       # 단곡선은 h1 사용
            w13=curve.params[4],          # W13 (-R)
            sp_sta=curve.bc_sta,
            pc_sta=curve.bc_sta,          # BC = PC
            cp_sta=curve.ec_sta,          # EC = CP
            ps_sta=curve.ec_sta,
            bp_xy=bp_xy,
            sp_xy=curve.bc_xy,
            center_xy=curve.center_xy,
            ps_xy=curve.ec_xy,
        )
    # 3차포물선
    return CurveGeometry(
        h1=curve.h1,
        h2=curve.h2,
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
        shiftx=shiftx,
        shifty=shifty,
    )

def get_station_at_coordinates(
    p: tuple[float, float], polycurve: list[tuple[float, float]],
    station_groups,
) -> Optional[float]:
    """좌표 → 측점"""
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
