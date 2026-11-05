"""
측점 그룹 빌더 (Station Group Builder) 모듈
=============================================
_build_station_group의 책임을 분리:
  1. StationListBuilder  : 측점 리스트 생성 + 정렬 + 중복 제거
  2. ShiftCalculator     : 이정량(shiftx, shifty) 계산
  3. StationRowFactory   : 측점 1개 → StationRow 변환

각 클래스는 단일 책임 원칙(SRP)을 따르며,
곡선 타입(simplecurve/cubic) 차이는 팩토리에서 흡수.
"""

from __future__ import annotations

import logging
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.railway_alignment.core.coordinate_calculator import (
    CoordinateCalculator,
    build_geometry_from_curve,
    create_coordinate_calculator,
)
from src.railway_alignment.core.math_util import get_station_label, calculate_station_offset
from src.railway_alignment.core.models import StationRow, CurveParams

from src.railway_alignment.core.tangent_calculator import (
    TangentCalculator,
    create_tangent_calculator,
)

logger = logging.getLogger(__name__)


# ============================================================
# 1) 측점 리스트 빌더
# ============================================================
# ============================================================
# 1) 측점 리스트 빌더 (개선)
# ============================================================
class StationListBuilder(ABC):
    """측점 리스트 생성 전략"""

    def __init__(self, curve: "CurveParams", bp_sta: float, end_sta: float, unit: int):
        self.curve = curve
        self.bp_sta = bp_sta
        self.end_sta = end_sta
        self.unit = unit

    @abstractmethod
    def build(self) -> list[float]:
        """측점 리스트 (정렬 + 중복 제거)"""
        ...

    def _base_stations(self) -> list[float]:
        """측점 리스트 생성.

        ✅ bp_sta와 end_sta를 반드시 포함 (연속성 보장).
        - bp_sta가 unit 배수가 아니면 bp_sta 직접 포함
        - unit 배수로 채움
        - end_sta가 마지막 unit 배수 이후면 end_sta 직접 포함
        """
        stations: list[float] = []

        # 1) bp_sta가 unit 배수가 아니면 직접 포함
        if self.bp_sta % self.unit != 0:
            stations.append(self.bp_sta)

        # 2) bp_sta 이후 첫 unit 배수부터 end_sta 이전 마지막 unit 배수까지
        start_unit = math.ceil(self.bp_sta / self.unit) * self.unit
        end_unit = math.floor(self.end_sta / self.unit) * self.unit
        if start_unit <= end_unit:
            stations.extend(
                float(v) for v in range(int(start_unit), int(end_unit) + 1, self.unit)
            )

        # 3) end_sta가 마지막 unit 배수 이후면 직접 포함
        if end_unit < self.end_sta - 1e-6:
            stations.append(self.end_sta)

        return stations

    def _finalize(self, stations: list[float]) -> list[float]:
        """0.01m 정밀도로 중복 제거 + 정렬 (부동소수점 안전)."""
        unique: dict[int, float] = {}
        for sta in stations:
            key = int(round(sta * 100))  # ✅ 0.01m 단위
            if key not in unique:
                unique[key] = sta
        return [unique[k] for k in sorted(unique)]


class SimpleCurveStationListBuilder(StationListBuilder):
    def build(self) -> list[float]:
        stations = self._base_stations()
        stations.extend([self.bp_sta, self.curve.bc_sta, self.curve.ec_sta])
        if self.end_sta - self.curve.ec_sta > 1e-6:
            stations.append(self.end_sta)
        return self._finalize(stations)


class CubicStationListBuilder(StationListBuilder):
    def build(self) -> list[float]:
        stations = self._base_stations()

        markers = [
            self.curve.sp_sta, self.curve.pc_sta,
            self.curve.cp_sta, self.curve.ps_sta,
        ]
        if any(m is None for m in markers):
            raise ValueError(
                f"IP{self.curve.ip_no}: cubic 곡선인데 SP/PC/CP/PS가 None"
            )
        stations.extend(markers)

        if self.bp_sta % self.unit != 0:
            stations.append(self.bp_sta)
        if self.end_sta - self.curve.ps_sta > 1e-6:
            stations.append(self.end_sta)

        return self._finalize(stations)


class StraightStationListBuilder(StationListBuilder):
    """직선 IP: 곡선 주요 지점 없음. BP + unit 배수 + IP sta."""

    def build(self) -> list[float]:
        stations = self._base_stations()

        # ✅ [핵심 수정] 마지막 IP의 EP 지점(end_sta)이 부동소수점 오차나
        # unit 배수 조건 때문에 누락되는 것을 방지하기 위해 무조건 강제 추가
        if not stations or abs(stations[-1] - self.end_sta) > 1e-6:
            stations.append(self.end_sta)

        return self._finalize(stations)

def create_station_list_builder(curve, bp_sta, end_sta, unit):
    if curve.curve_type == "simplecurve":
        return SimpleCurveStationListBuilder(curve, bp_sta, end_sta, unit)
    if curve.curve_type == "straight":
        return StraightStationListBuilder(curve, bp_sta, end_sta, unit)  # ✅
    return CubicStationListBuilder(curve, bp_sta, end_sta, unit)


# ============================================================
# 2) 이정량 계산기
# ============================================================
@dataclass(frozen=True)
class ShiftResult:
    """이정량 (shiftx, shifty)"""

    x: float = 0.0
    y: float = 0.0

    @classmethod
    def zero(cls) -> "ShiftResult":
        return cls(0.0, 0.0)


class ShiftCalculator(ABC):
    """이정량 계산 전략"""

    def __init__(self, curve: "CurveParams"):
        self.curve = curve

    @abstractmethod
    def compute(self, sta: float, offset: float) -> ShiftResult:
        ...


class ZeroShiftCalculator(ShiftCalculator):
    """단곡선: 이정량 항상 0"""

    def compute(self, sta: float, offset: float) -> ShiftResult:
        return ShiftResult.zero()


class SpiralShiftCalculator(ShiftCalculator):
    """3차포물선: 완화곡선 구간 이정량"""

    def __init__(self, curve: "CurveParams"):
        super().__init__(curve)
        p = curve.params
        self.x1 = p[0]          # X1
        self.w13 = p[2]         # -R
        self.L = p[3]           # 완화곡선 길이
        self.sp_sta = curve.sp_sta
        self.pc_sta = curve.pc_sta
        self.cp_sta = curve.cp_sta
        self.ps_sta = curve.ps_sta

    def compute(self, sta: float, offset: float) -> ShiftResult:
        # 진입부: SP < sta < PC
        if self.sp_sta < sta < self.pc_sta:
            return self._entry(offset)
        # 진출부: CP < sta < PS
        if self.cp_sta < sta < self.ps_sta:
            return self._exit(offset)
        return ShiftResult.zero()

    def _entry(self, offset: float) -> ShiftResult:
        """진입 완화곡선 이정량 (원본 수식)"""
        x = offset - offset ** 5 / (40 * self.w13 ** 2 * self.L ** 2)
        y = x ** 3 / (6 * self.w13 * self.x1)
        return ShiftResult(x=x, y=y)

    def _exit(self, offset: float) -> ShiftResult:
        """진출 완화곡선 이정량 (원본과 동일 수식)"""
        x = offset - offset ** 5 / (40 * self.w13 ** 2 * self.L ** 2)
        y = x ** 3 / (6 * self.w13 * self.x1)
        return ShiftResult(x=x, y=y)


def create_shift_calculator(curve: "CurveParams") -> ShiftCalculator:
    if curve.curve_type in ("simplecurve", "straight"):
        return ZeroShiftCalculator(curve)  # ✅ 직선은 이정량 0
    return SpiralShiftCalculator(curve)


# ============================================================
# 3) StationRow 팩토리
# ============================================================
class StationRowFactory:
    """측점 1개를 StationRow로 조립

    좌표/접선 계산기와 기하 컨텍스트를 받아 완전한 row 생성.
    """

    def __init__(
        self,
        curve: "CurveParams",
        coord_calc: CoordinateCalculator,
        tangent_calc: TangentCalculator,
        bp_xy: tuple[float, float],
        bp_sta: float,  # ✅ 신규
    ):
        self.curve = curve
        self.coord_calc = coord_calc
        self.tangent_calc = tangent_calc
        self.bp_xy = bp_xy
        self.bp_sta = bp_sta  # ✅

    def create(
        self,
        sta: float,
        offset: float,
        label: str,
        shift: ShiftResult,
    ) -> "StationRow":

        geometry = build_geometry_from_curve(
            self.curve,
            bp_xy=self.bp_xy,
            shiftx=shift.x,
            shifty=shift.y,
            bp_sta=self.bp_sta,  # ✅
        )
        coord = self.coord_calc.compute(sta, offset, geometry).as_tuple()
        fields = self.tangent_calc.compute(sta, offset)

        return StationRow(
            label=label,
            sta=sta,
            station_offset=offset,
            coord=coord,
            shiftx=shift.x,
            shifty=shift.y,
            ta=fields.ta,
            chord_length=fields.chord,
            q=fields.q,
            t=fields.t,
            azimuth=fields.azimuth,
        )


# ============================================================
# 4) 오케스트레이터 (기존 _build_station_group 대체)
# ============================================================
def build_station_group(
    curve: "CurveParams",
    bp_sta: float,
    bp_xy: tuple[float, float],
    end_sta: float,
    unit: int,
) -> list["StationRow"]:
    """한 IP에 대한 측점 리스트 생성 (오케스트레이션만 담당)

    Args:
        curve: 곡선 파라미터
        bp_sta: BP 측점
        bp_xy: BP 좌표 (또는 이전 IP 끝점)
        end_sta: EP 측점 (마지막 IP면 EP, 아니면 EC/PS)
        unit: 측점 간격

    Returns:
        StationRow 리스트
    """

    # 1) 계산기 준비
    station_builder = create_station_list_builder(curve, bp_sta, end_sta, unit)
    shift_calc = create_shift_calculator(curve)
    coord_calc = create_coordinate_calculator(curve)
    tangent_calc = create_tangent_calculator(curve)
    row_factory = StationRowFactory(curve, coord_calc, tangent_calc, bp_xy, bp_sta)

    # 2) 측점 리스트
    stations = station_builder.build()

    # 3) 라벨 경계값 (구간별)
    boundaries = _curve_boundaries(curve, end_sta)

    # 4) 측점별 row 생성
    rows: list[StationRow] = []
    for j, sta in enumerate(stations):
        # 라벨/측거
        if abs(sta - bp_sta) < 1e-6:
            label = "BP"
            offset = 0.0
        else:
            label = get_station_label(curve.curve_type, sta, *boundaries)
            offset = calculate_station_offset(sta, *boundaries[:4], bp_sta)

        # 이정량
        shift = shift_calc.compute(sta, offset)

        # row 생성
        row = row_factory.create(sta, offset, label, shift)
        rows.append(row)
    return rows


def _curve_boundaries(curve, end_sta):
    if curve.curve_type == "simplecurve":
        return (curve.bc_sta, curve.bc_sta, curve.ec_sta, curve.ec_sta, end_sta)
    if curve.curve_type == "straight":
        return (end_sta, end_sta, end_sta, end_sta, end_sta)   # ✅
    return (curve.sp_sta, curve.pc_sta, curve.cp_sta, curve.ps_sta, end_sta)