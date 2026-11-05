"""
선형 계산 서비스 레이어
=========================
기존 AlignmentApp.run_calculation에 뒤섞여 있던
비즈니스 흐름을 캡슐화.

흐름:
  입력 파싱 → 선형 계산 → 결과물(Excel/DXF/TXT) 저장

GUI는 이 서비스만 호출하며, 서비스는 tkinter에 의존하지 않음.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from shapely.geometry import LineString

from src.railway_alignment.core.cant import calculate_parameters
from src.railway_alignment.core.constants import Config
from src.railway_alignment.core.coordinate_calculator import (
    build_geometry_from_curve,
    create_coordinate_calculator, get_station_at_coordinates,
)
from src.railway_alignment.core.curve import cal_spiral_shiftx, cal_spiral_shifty, calculate_curve
from src.railway_alignment.core.linestring import create_linestring
from src.railway_alignment.core.math_util import calculate_angles, calculate_station_offset
from src.railway_alignment.core.validator import validate_curves, ValidationIssue
from src.railway_alignment.io.civil3d_wirter import create_civil3d_xlsx, create_incremental_station_report, \
    save_total_coordinates
from src.railway_alignment.io.dxf_config import DXFConfig
from src.railway_alignment.io.dxf_writer import create_dxf
from src.railway_alignment.io.parsers import parse_ip_lines
from src.railway_alignment.io.report_writer import write_report

logger = logging.getLogger(__name__)


# ============================================================
# 입력 데이터
# ============================================================
@dataclass(frozen=True)
class AlignmentInput:
    """사용자 입력 파라미터"""

    raw_lines: list[list[str]]         # 파일에서 읽은 원본 라인
    unit: int = Config.DEFAULT_UNIT
    start_sta: float = Config.DEFAULT_START_STA
    design_speed: int = Config.DEFAULT_DESIGN_SPEED
    ballast: str = "자갈도상"           # '자갈도상' | '콘크리트도상'

    # ✅ 복선 옵션
    double_track: bool = False
    track_gauge: float = 4.3  # 궤도 간격 (m) — 내부에서 D/2 계산
    track_swap_direction: bool = False  # 좌/우 스왑

    # ip_no(1-based) → {"m": mm아님 그대로, "v": int, "z": **mm**}
    # Z는 내부 계산 단위인 mm로 전달 (테이블에서 변환)
    parameter_overrides: dict[int, dict[str, float]] = field(default_factory=dict)

    # ip_no → "simplecurve"/"cubic" (수동 타입 토글만)
    type_overrides: dict[int, str] = field(default_factory=dict)

# ============================================================
# 계산 결과
# ============================================================
@dataclass
class AlignmentResult:
    """선형 계산 결과 (모든 산출물)"""

    linestring: Optional[LineString] = None
    curves: list = field(default_factory=list)             # list[CurveParams]
    station_groups: list = field(default_factory=list)     # list[list[list[StationRow]]]
    polycurve: list[tuple[float, float]] = field(default_factory=list)

    # ✅ 복선 궤도 (오프셋 계산 결과)
    track_gauge: float = 0.0
    upper_track_polycurve: list[tuple[float, float]] = field(default_factory=list)  # 상선 (우측)
    lower_track_polycurve: list[tuple[float, float]] = field(default_factory=list)  # 하선 (좌측)
    upper_track_stations: list = field(default_factory=list)
    lower_track_stations: list = field(default_factory=list)

    # 출력 파일 경로
    report_path: Optional[Path] = None
    civil3d_path: Optional[Path] = None
    total_coord_path: Optional[Path] = None
    incremental_report_path: Optional[Path] = None
    dxf_path: Optional[Path] = None

    # ✅ 검증 결과
    issues: list[ValidationIssue] = field(default_factory=list)

    unit: int = Config.DEFAULT_UNIT
    start_sta: float = Config.DEFAULT_START_STA
    design_speed: int = Config.DEFAULT_DESIGN_SPEED
    ballast: str = "자갈도상"

    @property
    def is_empty(self) -> bool:
        return not self.curves


# ============================================================
# 서비스 예외
# ============================================================
class AlignmentServiceError(Exception):
    """서비스 레이어 예외 (GUI에서 메시지 표시용)"""


# ============================================================
# 서비스 레이어
# ============================================================
class AlignmentService:
    """선형 계산 서비스

    tkinter에 의존하지 않으므로 CLI/테스트에서도 재사용 가능.
    """

    def __init__(self) -> None:
        self.result = AlignmentResult()
        self.dxf_config = DXFConfig.load_or_default()  # ✅ 자동 로드
    # --------------------------------------------------------
    # 공개 API
    # --------------------------------------------------------
    def calculate(self, input_data: AlignmentInput) -> AlignmentResult:
        """선형 계산 수행 + 결과물 파일 저장

        Args:
            input_data: 사용자 입력 (raw_lines, unit, start_sta, ...)

        Returns:
            AlignmentResult (curves, station_groups, polycurve, 저장 경로들)

        Raises:
            AlignmentServiceError: 입력 오류 또는 계산 실패
        """
        if not input_data.raw_lines:
            raise AlignmentServiceError("선형 데이터가 비어 있습니다.")

        # 1) IP 파싱
        alignment = self._parse_alignment(input_data.raw_lines)
        if len(alignment) < 3:
            raise AlignmentServiceError(
                f"IP가 3개 이상 필요합니다 (현재 {len(alignment)}개)."
            )

        # 2) 선형 계산
        result = self._run_calculation(alignment, input_data)
        result.issues = validate_curves(result.curves)  # ✅ 추가
        self.result = result

        # 3) 결과물 저장
        self._write_outputs(result, input_data)

        logger.info(
            "선형 계산 완료: IP %d개, 측점 %d개",
            len(result.curves),
            sum(len(sg[0]) for sg in result.station_groups),
        )
        return result

    def calculate_only(self, input_data: AlignmentInput) -> AlignmentResult:
        """계산만 수행 (파일 저장 없음) — 실시간 UI용"""
        if not input_data.raw_lines:
            raise AlignmentServiceError("선형 데이터가 비어 있습니다.")

        alignment = self._parse_alignment(input_data.raw_lines)
        if len(alignment) < 3:
            raise AlignmentServiceError(
                f"IP가 3개 이상 필요합니다 (현재 {len(alignment)}개)."
            )

        result = self._run_calculation(alignment, input_data)
        result.issues = validate_curves(result.curves)
        self.result = result
        return result

    def export_dxf(self, filename=None, config=None, unit=None, upper_track=None, lower_track=None) -> Path:
        """DXF 출력 (scale 인자 없음)."""
        if self.result.is_empty:
            raise AlignmentServiceError("먼저 선형 계산을 실행하세요.")

        filename = filename or Config.DXF_FILENAME
        cfg = config or self.dxf_config

        create_dxf(
            coordinates=self.result.polycurve,
            linestring=self.result.linestring,
            curves=self.result.curves,
            station_groups=self.result.station_groups,
            unit=unit or cfg.sub_tick,  # ✅ 서비스에서도 기본값 sub_tick
            filename=filename,
            config=cfg,
            upper_track=upper_track,
            lower_track=lower_track,
        )
        path = Config.ensure_output_dir() / filename
        self.result.dxf_path = path
        logger.info("DXF 저장 완료: %s", path)
        return path

    def get_coordinate(self, sta: float) -> Optional[tuple[float, float]]:
        """측점 → 좌표 조회"""
        if self.result.is_empty:
            raise AlignmentServiceError("먼저 선형 계산을 실행하세요.")

        for i, curve in enumerate(self.result.curves):
            group = self.result.station_groups[i] if i < len(self.result.station_groups) else []
            if not group or not group[0]:
                continue
            flat = group[0]
            if not (flat[0].sta <= sta <= flat[-1].sta):
                continue

            bp_xy = flat[0].coord
            bp_sta = flat[0].sta  # ✅ 신규
            if curve.curve_type == "straight":
                # ✅ 직선 IP: 단순 offset
                offset = sta - bp_sta
                shiftx = shifty = 0.0
            elif curve.curve_type == "simplecurve":
                offset = calculate_station_offset(
                    sta, curve.bc_sta, curve.bc_sta,
                    curve.ec_sta, curve.ec_sta, flat[0].sta,
                )
                shiftx = shifty = 0.0
            else:
                offset = calculate_station_offset(
                    sta, curve.sp_sta, curve.pc_sta,
                    curve.cp_sta, curve.ps_sta, flat[0].sta,
                )
                shiftx = cal_spiral_shiftx(
                    sta, curve.sp_sta, curve.pc_sta, curve.cp_sta, curve.ps_sta,
                    offset, curve.params[2], curve.params[3],
                )
                shifty = cal_spiral_shifty(
                    sta, curve.sp_sta, curve.pc_sta, curve.cp_sta, curve.ps_sta,
                    shiftx, curve.params[2], curve.params[0],
                )

            geometry = build_geometry_from_curve(
                curve, bp_xy=bp_xy, shiftx=shiftx, shifty=shifty,
                bp_sta=bp_sta,  # ✅
            )
            calc = create_coordinate_calculator(curve)
            return calc.compute(sta, offset, geometry).as_tuple()

        return None

    def get_station(self, x: float, y: float) -> Optional[float]:
        """좌표 → 측점 조회"""
        if self.result.is_empty:
            raise AlignmentServiceError("먼저 선형 계산을 실행하세요.")

        return get_station_at_coordinates(
            (x, y), self.result.polycurve, self.result.station_groups,
        )

    # --------------------------------------------------------
    # 내부: 선형 계산
    # --------------------------------------------------------
    def _parse_alignment(self, raw_lines: list[list[str]]) -> list[list[float]]:
        """raw_lines → alignment 파싱"""
        try:
            alignment = parse_ip_lines(raw_lines)
        except Exception as e:
            raise AlignmentServiceError(f"IP 파싱 실패: {e}") from e

        if not alignment:
            raise AlignmentServiceError("유효한 IP 데이터가 없습니다.")
        return alignment

    def _run_calculation(self, alignment, input_data):
        try:
            linestring = create_linestring(alignment)
            radius_list = [p[2] for p in alignment[1:-1]]
            angles = calculate_angles(linestring)

            auto_params = calculate_parameters(
                radius_list, input_data.design_speed, input_data.ballast,
            )

            parameters: list[list[float]] = []
            type_overrides = {
                ip: t for ip, t in input_data.type_overrides.items()
                if radius_list[ip - 1] != 0  # ✅ R=0 IP는 타입 오버라이드 무시
            }

            for i, auto in enumerate(auto_params):
                ip_no = i + 1
                # ✅ R=0 (직선 IP)은 파라미터 [0, 0, 0] 고정
                if radius_list[i] == 0:
                    parameters.append([0, 0, 0])
                    continue
                auto_m, auto_z, auto_v = auto[0], auto[1], auto[2]

                override = input_data.parameter_overrides.get(ip_no)
                if not override:
                    parameters.append([auto_m, auto_z, auto_v])
                    continue

                user_m = float(override.get("m", 0))
                user_v = float(override.get("v", 0))
                user_z_m = float(override.get("z", 0))  # m 단위

                # ── M 판정 (최우선)
                if user_m == 0:
                    curve_type = "simplecurve"
                    m_final = 0.0
                    v_final = auto_v
                    z_final = auto_z
                else:
                    curve_type = "cubic"
                    m_final = float(round(user_m / Config.M_ROUNDING) * Config.M_ROUNDING)

                    if user_v == 0:
                        v_final = int(round(auto_v / Config.V_ROUNDING) * Config.V_ROUNDING)
                    else:
                        v_final = int(round(user_v / Config.V_ROUNDING) * Config.V_ROUNDING)

                    if user_z_m == 0:
                        z_final = float(round(auto_z / Config.Z_ROUNDING) * Config.Z_ROUNDING)
                    else:
                        z_mm = user_z_m * 1000.0
                        z_final = float(round(z_mm / Config.Z_ROUNDING) * Config.Z_ROUNDING)

                # 명시 타입 토글이 있으면 최우선
                if ip_no in input_data.type_overrides:
                    curve_type = input_data.type_overrides[ip_no]

                type_overrides[ip_no] = curve_type
                parameters.append([m_final, z_final, v_final])

            station_groups, curves, polycurve = calculate_curve(
                linestring, radius_list, angles, parameters,
                input_data.unit, input_data.start_sta,
                type_overrides=type_overrides,
            )
        except Exception as e:
            raise AlignmentServiceError(f"선형 계산 실패: {e}") from e

        issues = validate_curves(curves)

        result = AlignmentResult(
            linestring=linestring,
            curves=curves,
            station_groups=station_groups,
            polycurve=polycurve,
            issues=issues,
            unit=input_data.unit,
            start_sta=input_data.start_sta,
            design_speed=input_data.design_speed,
            ballast=input_data.ballast,
        )
        # ✅ 복선 궤도 계산
        logger.warning(
            "[DEBUG _run_calculation] double_track=%s, track_gauge=%.2f",
            input_data.double_track, input_data.track_gauge,
        )
        # ✅ 여기로 이동! (result 생성 직후)
        if input_data.double_track and input_data.track_gauge > 0:
            self._compute_track_offsets(
                result,
                gauge=input_data.track_gauge,
                swap=input_data.track_swap_direction,
            )
            logger.warning(
                "[DEBUG] 궤도 계산 후: upper=%d, lower=%d",
                len(result.upper_track_polycurve),
                len(result.lower_track_polycurve),
            )
        else:
            logger.warning("[DEBUG] 복선 조건 미충족 → 궤도 계산 스킵")
        return result
    # --------------------------------------------------------
    # 내부: 결과물 저장
    # --------------------------------------------------------
    def _write_outputs(self, result: AlignmentResult, input_data: AlignmentInput) -> None:
        """보고서/Civil3D/좌표/증분 보고서 저장"""
        try:
            # 1) Excel 보고서
            write_report(result.curves, result.station_groups)
            result.report_path = Config.OUTPUT_DIR / Config.REPORT_FILENAME

            # 2) Civil3D 입력용
            create_civil3d_xlsx(result.curves)
            result.civil3d_path = Config.OUTPUT_DIR / Config.CIVIL3D_FILENAME

            # 3) 전체 좌표 TXT
            save_total_coordinates(result.station_groups)
            result.total_coord_path = Config.OUTPUT_DIR / Config.TOTAL_COORD_FILENAME

            # 4) 증분 측점 보고서
            create_incremental_station_report(
                result.station_groups,
                unit=input_data.unit,
                file_ext="xls",
            )
            result.incremental_report_path = (
                Config.OUTPUT_DIR / Config.INCREMENTAL_REPORT_FILENAME
            ).with_suffix(".xls")

        except Exception as e:
            logger.exception("결과물 저장 중 오류")
            raise AlignmentServiceError(f"결과물 저장 실패: {e}") from e


    def _compute_track_offsets(
        self, result: AlignmentResult, gauge: float, swap: bool = False,
    ) -> None:
        """CL 측점에서 상선/하선 궤도 좌표 계산 (단순 오프셋).

        - 하선: CL 진행 방향 기준 좌측 (ta + 90°)
        - 상선: CL 진행 방향 기준 우측 (ta - 90°)
        - 오프셋 = gauge / 2
        """
        import math
        from src.railway_alignment.core.models import StationRow

        offset = gauge / 2.0
        upper_poly: list[tuple[float, float]] = []
        lower_poly: list[tuple[float, float]] = []
        upper_stations: list[StationRow] = []
        lower_stations: list[StationRow] = []

        for group in result.station_groups:
            for subgroup in group:
                for row in subgroup:
                    x, y = row.coord
                    ta_deg = row.ta

                    # 하선(좌측): ta + 90°
                    # 상선(우측): ta - 90°
                    bearing_lower = math.radians(ta_deg + 90)
                    bearing_upper = math.radians(ta_deg - 90)

                    x_lower = x + offset * math.cos(bearing_lower)
                    y_lower = y + offset * math.sin(bearing_lower)
                    x_upper = x + offset * math.cos(bearing_upper)
                    y_upper = y + offset * math.sin(bearing_upper)

                    if swap:
                        x_lower, x_upper = x_upper, x_lower
                        y_lower, y_upper = y_upper, y_lower

                    lower_poly.append((x_lower, y_lower))
                    upper_poly.append((x_upper, y_upper))

                    lower_stations.append(StationRow(
                        label=row.label, sta=row.sta,
                        station_offset=row.station_offset,
                        coord=(x_lower, y_lower),
                        shiftx=row.shiftx, shifty=row.shifty,
                        ta=row.ta, chord_length=row.chord_length,
                        q=row.q, t=row.t, azimuth=row.azimuth,
                    ))
                    upper_stations.append(StationRow(
                        label=row.label, sta=row.sta,
                        station_offset=row.station_offset,
                        coord=(x_upper, y_upper),
                        shiftx=row.shiftx, shifty=row.shifty,
                        ta=row.ta, chord_length=row.chord_length,
                        q=row.q, t=row.t, azimuth=row.azimuth,
                    ))

        result.track_gauge = gauge
        result.upper_track_polycurve = upper_poly
        result.lower_track_polycurve = lower_poly
        result.upper_track_stations = upper_stations
        result.lower_track_stations = lower_stations

        logger.info(
            "복선 궤도 계산 완료: 궤도간격=%.3fm (오프셋 %.3fm), 상선 %d점, 하선 %d점",
            gauge, offset, len(upper_poly), len(lower_poly),
        )
# ============================================================
# 편의 함수 (CLI/테스트용)
# ============================================================
def run_alignment(
    raw_lines: list[list[str]],
    unit: int = Config.DEFAULT_UNIT,
    start_sta: float = Config.DEFAULT_START_STA,
    design_speed: int = Config.DEFAULT_DESIGN_SPEED,
    ballast: str = "자갈도상",
) -> AlignmentResult:
    """단일 호출로 전체 계산 수행"""
    service = AlignmentService()
    return service.calculate(AlignmentInput(
        raw_lines=raw_lines,
        unit=unit,
        start_sta=start_sta,
        design_speed=design_speed,
        ballast=ballast,
    ))
