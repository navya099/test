
"""
규정 검증 모듈
================
IP별 계산 결과를 규정 기준으로 검증하여 UI에 피드백.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from src.railway_alignment.core.constants import Config

if TYPE_CHECKING:
    from src.railway_alignment.core.models import CurveParams


class Severity(Enum):
    OK = "ok"
    WARN = "warn"
    ERROR = "error"


@dataclass(frozen=True)
class ValidationIssue:
    """단일 검증 결과"""

    ip_no: int
    severity: Severity
    code: str            # 'L_SHORT', 'OVERLAP', 'R_SMALL' 등
    message: str


# ============================================================
# 검증 규칙
# ============================================================
def _check_min_radius(curve: "CurveParams") -> ValidationIssue | None:
    """최소 곡선 반경 검증"""
    v = curve.v
    cm_cd = 160 + 100 if v <= 250 else 160 + 80
    min_r = Config.CANT_COEFFICIENT * 0 + (v ** 2) / (cm_cd / Config.CANT_COEFFICIENT)
    if curve.radius < min_r * 0.5:  # 여유 있게 50% 기준
        return ValidationIssue(
            ip_no=curve.ip_no,
            severity=Severity.WARN,
            code="R_SMALL",
            message=f"곡선반경 R={curve.radius:.0f}m가 권장 최소값({min_r:.0f}m) 미달",
        )
    return None


def _check_spiral_length(curve: "CurveParams") -> ValidationIssue | None:
    """완화곡선 길이 검증 (3차포물선만)"""
    if curve.curve_type != "cubic":
        return None
    L = curve.spiral_length
    min_L = curve.v / 3.6 * 1.0  # 1초 주행 거리
    if L < min_L * 0.8:
        return ValidationIssue(
            ip_no=curve.ip_no,
            severity=Severity.WARN,
            code="L_SHORT",
            message=f"완화곡선 L={L:.1f}m가 최소({min_L:.1f}m) 미달",
        )
    return None


def _check_curve_overlap(
    prev_curve: "CurveParams | None", curve: "CurveParams"
) -> ValidationIssue | None:
    """이전 IP와의 곡선 중첩 검증"""
    if prev_curve is None:
        return None
    prev_end = prev_curve.ec_sta if prev_curve.curve_type == "simplecurve" else prev_curve.ps_sta
    curr_start = curve.bc_sta if curve.curve_type == "simplecurve" else curve.sp_sta
    if prev_end is None or curr_start is None:
        return None
    if prev_end > curr_start + 1e-6:
        return ValidationIssue(
            ip_no=curve.ip_no,
            severity=Severity.ERROR,
            code="OVERLAP",
            message=(
                f"곡선 중첩: IP{prev_curve.ip_no} 종점({prev_end:.2f}) > "
                f"IP{curve.ip_no} 기점({curr_start:.2f})"
            ),
        )
    return None


def _check_ia_positive(curve: "CurveParams") -> ValidationIssue | None:
    """교각 검증"""
    if curve.ia_degree <= 0 or curve.ia_degree >= 180:
        return ValidationIssue(
            ip_no=curve.ip_no,
            severity=Severity.ERROR,
            code="IA_INVALID",
            message=f"교각 IA={curve.ia_degree:.2f}°가 유효 범위(0~180)를 벗어남",
        )
    return None


# ============================================================
# 공개 API
# ============================================================
def validate_curves(curves: list["CurveParams"]) -> list[ValidationIssue]:
    """전체 IP 검증"""
    issues: list[ValidationIssue] = []
    for i, curve in enumerate(curves):
        prev = curves[i - 1] if i > 0 else None
        for check in (
            _check_ia_positive(curve),
            _check_min_radius(curve),
            _check_spiral_length(curve),
            _check_curve_overlap(prev, curve),
        ):
            if check is not None:
                issues.append(check)
    return issues


def issues_by_ip(issues: list[ValidationIssue]) -> dict[int, list[ValidationIssue]]:
    """IP별로 그룹화"""
    grouped: dict[int, list[ValidationIssue]] = {}
    for issue in issues:
        grouped.setdefault(issue.ip_no, []).append(issue)
    return grouped


def overall_severity(issues: list[ValidationIssue]) -> Severity:
    """전체 심각도"""
    if any(i.severity == Severity.ERROR for i in issues):
        return Severity.ERROR
    if any(i.severity == Severity.WARN for i in issues):
        return Severity.WARN
    return Severity.OK