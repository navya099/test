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
from src.railway_alignment.core.constant_config import Config
from src.railway_alignment.core.coordinate_calculator import (
    build_geometry_from_curve,
    create_coordinate_calculator, get_station_at_coordinates,
)
from src.railway_alignment.core.curve import cal_spiral_shiftx, cal_spiral_shifty, calculate_curve
from src.railway_alignment.core.linestring import create_linestring
from src.railway_alignment.core.math_util import calculate_angles, calculate_station_offset
from src.railway_alignment.io.civil3d_wirter import create_civil3d_xlsx, create_incremental_station_report, \
    save_total_coordinates
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

    # 출력 파일 경로
    report_path: Optional[Path] = None
    civil3d_path: Optional[Path] = None
    total_coord_path: Optional[Path] = None
    incremental_report_path: Optional[Path] = None
    dxf_path: Optional[Path] = None

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
        self.result = result

        # 3) 결과물 저장
        self._write_outputs(result, input_data)

        logger.info(
            "선형 계산 완료: IP %d개, 측점 %d개",
            len(result.curves),
            sum(len(sg[0]) for sg in result.station_groups),
        )
        return result

    def export_dxf(self, scale: int = Config.DEFAULT_SCALE, filename: str = None) -> Path:
        """DXF 출력 (calculate 호출 후 사용)"""
        if self.result.is_empty:
            raise AlignmentServiceError("먼저 선형 계산을 실행하세요.")

        filename = filename or Config.DXF_FILENAME
        create_dxf(
            coordinates=self.result.polycurve,
            linestring=self.result.linestring,
            curves=self.result.curves,
            station_groups=self.result.station_groups,
            unit=Config.DEFAULT_UNIT,   # TODO: input에서 전달
            filename=filename,
            scale=scale,
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

            if curve.curve_type == "simplecurve":
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

    def _run_calculation(
        self, alignment: list[list[float]], input_data: AlignmentInput,
    ) -> AlignmentResult:
        """핵심 계산 로직"""
        try:
            linestring = create_linestring(alignment)
            radius_list = [p[2] for p in alignment[1:-1]]
            angles = calculate_angles(linestring)
            parameters = calculate_parameters(
                radius_list, input_data.design_speed, input_data.ballast,
            )

            station_groups, curves, polycurve = calculate_curve(
                linestring, radius_list, angles, parameters,
                input_data.unit, input_data.start_sta,
            )
        except Exception as e:
            raise AlignmentServiceError(f"선형 계산 실패: {e}") from e

        return AlignmentResult(
            linestring=linestring,
            curves=curves,
            station_groups=station_groups,
            polycurve=polycurve,
        )

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