"""
선형 접선계산 (Tangent Fields) 모듈
====================================
기존 _compute_tangent_fields 함수를 곡선 타입별 계산기로 분리.

반환 필드:
  - ta: 접선방위각 (Tangent Azimuth)
  - azimuth: 방위각 (Azimuth)
  - q: 편기각 (Deflection Angle)
  - t: 접선각 (Tangent Angle)
  - chord: 사거리 (Chord Length)
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from 본선선형계산v10 import CurveParams


# ============================================================
# 반환 데이터 클래스
# ============================================================
@dataclass(frozen=True)
class TangentFields:
    """측점 1개에 대한 접선 관련 계산 결과"""

    ta: float           # 접선방위각 (Tangent Azimuth)
    azimuth: float      # 방위각 (Azimuth)
    q: float            # 편기각 (Deflection Angle, 도)
    t: float            # 접선각 (Tangent Angle, 도)
    chord: float        # 사거리 (Chord Length)

    @classmethod
    def zero(cls, ta: float) -> "TangentFields":
        """직선구간용 (편기각/접선각/사거리 모두 0)"""
        return cls(ta=ta, azimuth=0.0, q=0.0, t=0.0, chord=0.0)


class Zone(Enum):
    """측점이 속한 곡선 구간"""

    BEFORE_CURVE = "before"     # BP ~ SP (또는 BC)
    ENTRY_SPIRAL = "entry"      # SP ~ PC (완화곡선 진입)
    CIRCULAR = "circular"       # PC ~ CP (원곡선)
    EXIT_SPIRAL = "exit"        # CP ~ PS (완화곡선 진출)
    AFTER_CURVE = "after"       # PS ~ EP (또는 EC)


# ============================================================
# 구간 판정 유틸
# ============================================================
def _classify_zone(
    sta: float,
    sp: float,
    pc: float,
    cp: float,
    ps: float,
) -> Zone:
    """측점이 어느 구간에 속하는지 판정

    주의: 원본 로직의 경계 조건을 그대로 유지
      - SP < sta < PC  → ENTRY_SPIRAL
      - PC ≤ sta ≤ CP  → CIRCULAR
      - CP < sta < PS  → EXIT_SPIRAL
    """
    if pc <= sta <= cp:
        return Zone.CIRCULAR
    if sp < sta < pc:
        return Zone.ENTRY_SPIRAL
    if cp < sta < ps:
        return Zone.EXIT_SPIRAL
    if sta <= sp:
        return Zone.BEFORE_CURVE
    return Zone.AFTER_CURVE


def _signed_direction(direction: str) -> int:
    """'RIGHT CURVE' → +1, 'LEFT CURVE' → -1"""
    return 1 if direction == "RIGHT CURVE" else -1


# ============================================================
# 추상 베이스
# ============================================================
class TangentCalculator(ABC):
    """곡선 타입별 접선계산기 인터페이스"""

    @abstractmethod
    def compute(self, sta: float, offset: float) -> TangentFields:
        """측점 sta, 측거 offset에 대한 접선 필드 계산"""
        ...


# ============================================================
# 단곡선 계산기
# ============================================================
class SimpleCurveTangentCalculator(TangentCalculator):
    """단곡선 (Simple Curve) 접선계산기

    구간: BP ─ BC ═══ EC ─ EP
    - BC ~ EC: 원곡선 구간만 존재
    """

    def __init__(self, curve: "CurveParams"):
        self.curve = curve
        self.h1 = curve.h1
        self.h2 = curve.h2
        self.radius = curve.radius
        self.ia_degree = curve.ia_degree
        self.cl = curve.cl
        self.bc_sta = curve.bc_sta
        self.ec_sta = curve.ec_sta
        self.direction = _signed_direction(curve.direction)
        # 단곡선은 theta_pc = 0
        self.theta_deg = 0.0

    def compute(self, sta: float, offset: float) -> TangentFields:
        zone = self._zone(sta)
        if zone != Zone.CIRCULAR:
            return TangentFields.zero(self._straight_ta(zone))
        return self._circular(offset)

    def _zone(self, sta: float) -> Zone:
        if self.bc_sta < sta <= self.ec_sta:
            return Zone.CIRCULAR
        if sta <= self.bc_sta:
            return Zone.BEFORE_CURVE
        return Zone.AFTER_CURVE

    def _straight_ta(self, zone: Zone) -> float:
        return self.h1 if zone == Zone.BEFORE_CURVE else self.h2

    def _circular(self, offset: float) -> TangentFields:
        """원곡선 구간 계산 (원본 수식 유지)"""
        q = (180 / (2 * math.pi)) * (offset / self.radius)
        t = self.theta_deg
        d = self.direction

        azimuth = self.h1 + t + q if d == 1 else self.h1 - t - q
        ta = self.h1 + t + 2 * q if d == 1 else self.h1 - t - 2 * q
        chord = 2 * self.radius * math.sin(
            ((offset / self.cl) * math.radians(self.ia_degree)) / 2 * math.pi / 180
        )
        return TangentFields(ta=ta, azimuth=azimuth, q=q, t=t, chord=chord)


# ============================================================
# 3차포물선(완화곡선) 계산기
# ============================================================
class CubicTangentCalculator(TangentCalculator):
    """3차포물선 (완화곡선 포함) 접선계산기

    구간: BP ─ SP ═══ PC ─── CP ═══ PS ─ EP
    - SP ~ PC: 진입 완화곡선
    - PC ~ CP: 원곡선
    - CP ~ PS: 진출 완화곡선
    """

    def __init__(self, curve: "CurveParams"):
        self.curve = curve
        self.h1 = curve.h1
        self.h2 = curve.h2
        self.radius = curve.radius
        self.direction = _signed_direction(curve.direction)
        self.theta_deg = math.degrees(curve.theta_pc)

        # 파라미터 언팩
        p = curve.params
        self.x1 = p[0]          # X1
        self.w13 = p[2]         # -R
        self.L = p[3]           # 완화곡선 길이
        self.Lc = p[11]         # 원곡선 길이
        self.RIA = p[14]        # 원곡선교각 (rad)

        # 측점
        self.sp_sta = curve.sp_sta
        self.pc_sta = curve.pc_sta
        self.cp_sta = curve.cp_sta
        self.ps_sta = curve.ps_sta

    def compute(self, sta: float, offset: float) -> TangentFields:
        zone = _classify_zone(sta, self.sp_sta, self.pc_sta, self.cp_sta, self.ps_sta)
        dispatch = {
            Zone.CIRCULAR: self._circular,
            Zone.ENTRY_SPIRAL: self._entry_spiral,
            Zone.EXIT_SPIRAL: self._exit_spiral,
        }
        if zone in dispatch:
            return dispatch[zone](sta, offset)
        return TangentFields.zero(self._straight_ta(zone))

    def _straight_ta(self, zone: Zone) -> float:
        return self.h1 if zone == Zone.BEFORE_CURVE else self.h2

    # ---------- 원곡선 구간 ----------
    def _circular(self, sta: float, offset: float) -> TangentFields:
        """PC ~ CP (원본과 동일)"""
        q = (180 / (2 * math.pi)) * (offset / self.radius)
        t = self.theta_deg
        d = self.direction

        azimuth = self.h1 + t + q if d == 1 else self.h1 - t - q
        ta = self.h1 + t + 2 * q if d == 1 else self.h1 - t - 2 * q
        chord = 2 * self.radius * math.sin(
            ((offset / self.Lc) * math.degrees(self.RIA)) / 2 * math.pi / 180
        )
        return TangentFields(ta=ta, azimuth=azimuth, q=q, t=t, chord=chord)

    # ---------- 진입 완화곡선 ----------
    def _entry_spiral(self, sta: float, offset: float) -> TangentFields:
        """SP ~ PC (원본과 동일)"""
        shiftx = self._shiftx(sta, offset)
        q = math.atan(shiftx ** 2 / (6 * self.radius * self.x1))
        t = (180 * shiftx ** 2) / (6 * math.pi * self.radius * self.L) * 3
        d = self.direction

        azimuth = self.h1 + math.degrees(q) if d == 1 else self.h1 - math.degrees(q)
        ta = self.h1 + t if d == 1 else self.h1 - t
        chord = abs(shiftx)  # 원본: sqrt(shiftx² + 0)
        return TangentFields(ta=ta, azimuth=azimuth, q=q, t=t, chord=chord)

    # ---------- 진출 완화곡선 ----------
    def _exit_spiral(self, sta: float, offset: float) -> TangentFields:
        """CP ~ PS (원본과 동일)"""
        shiftx = self._shiftx(sta, offset)
        q = math.atan(shiftx ** 2 / (6 * self.radius * self.x1))
        t = (180 * shiftx ** 2) / (6 * math.pi * self.radius * self.L) * 3
        d = self.direction

        azimuth = self.h2 - math.degrees(q) if d == 1 else self.h2 + math.degrees(q)
        ta = self.h2 - t if d == 1 else self.h2 + t
        chord = abs(shiftx)
        return TangentFields(ta=ta, azimuth=azimuth, q=q, t=t, chord=chord)

    # ---------- 이정량 헬퍼 ----------
    def _shiftx(self, sta: float, offset: float) -> float:
        """진입/진출 완화곡선 이정량 X (원본 cal_spiral_shiftx 로직 인라인)"""
        s, sp_i, pc_i, ps_i = (int(x) for x in (sta, self.sp_sta, self.pc_sta, self.ps_sta))
        if sp_i >= s:
            return 0.0
        if pc_i > s or ps_i >= s:
            return offset - offset ** 5 / (40 * self.w13 ** 2 * self.L ** 2)
        return 0.0


# ============================================================
# 팩토리
# ============================================================
def create_tangent_calculator(curve: "CurveParams") -> TangentCalculator:
    """곡선 타입에 맞는 계산기 생성"""
    if curve.curve_type == "simplecurve":
        return SimpleCurveTangentCalculator(curve)
    return CubicTangentCalculator(curve)