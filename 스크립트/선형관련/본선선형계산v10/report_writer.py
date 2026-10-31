"""
선형계산서 Excel Writer 모듈
==============================
기존 write_report 함수를 시트 작성 전략 패턴으로 분리.

구조:
  ReportWorkbook         — 워크북 생성/저장 오케스트레이션
    ├ SimpleCurveSheetWriter — 단곡선 시트 (BP~EC)
    ├ CubicSheetWriter       — 3차포물선 시트 (BP~PS)
    └ StationTableWriter     — 측점 테이블 (공통)
"""

from __future__ import annotations
import math
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

logger = logging.getLogger(__name__)
import time

# ============================================================
# 공통 셀 유틸
# ============================================================
class SheetCellHelper:
    """시트 셀 쓰기 헬퍼 (반복 패턴 제거)"""

    def __init__(self, sheet: Worksheet):
        self.sheet = sheet

    def write(self, cell: str, value: str | float) -> None:
        """단일 셀 쓰기"""
        self.sheet[cell] = value

    def write_pairs(self, pairs: list[tuple[str, str | float]]) -> None:
        """(셀주소, 값) 리스트 일괄 쓰기"""
        for cell, value in pairs:
            self.sheet[cell] = value

    def write_coord(self, x_cell: str, y_cell: str, xy: tuple[float, float]) -> None:
        """좌표 (X, Y) 페어 쓰기"""
        self.sheet[x_cell] = f"X = {xy[0]:.4f}"
        self.sheet[y_cell] = f"Y = {xy[1]:.4f}"


# ============================================================
# 측점 테이블 Writer (공통)
# ============================================================
class StationTableWriter:
    """측점 테이블 (CHAINAGE / X / Y) 작성"""

    HEADER_ROW = 21
    START_ROW = 22

    def write(self, sheet: Worksheet, station_groups: list[list["StationRow"]]) -> None:
        sheet["B21"] = "CHAINAGE"
        sheet["D21"] = "X(North)"
        sheet["F21"] = "Y(East)"

        row_idx = self.START_ROW
        for subgroup in station_groups:
            for row in subgroup:
                sheet[f"A{row_idx}"] = row.label
                from 스크립트.선형관련.본선선형계산v10.본선선형계산v10 import format_distance
                from 스크립트.선형관련.본선선형계산v10.본선선형계산v10 import Config
                sheet[f"B{row_idx}"] = format_distance(row.sta, Config.KM_PRECISION)
                sheet[f"D{row_idx}"] = row.coord[0]
                sheet[f"F{row_idx}"] = row.coord[1]
                row_idx += 1


# ============================================================
# 시트 Writer 추상 베이스
# ============================================================
class BaseSheetWriter(ABC):
    """곡선 타입별 시트 작성기 인터페이스"""

    def __init__(self, curve: "CurveParams"):
        self.curve = curve
        self.helper: SheetCellHelper | None = None

    def write(self, sheet: Worksheet, station_groups: list[list["StationRow"]]) -> None:
        """템플릿 메서드: 헤더 → 본문 → 측점 테이블"""
        self.helper = SheetCellHelper(sheet)
        self._write_header()
        self._write_body()
        StationTableWriter().write(sheet, station_groups)

    # ---------- 공통 헤더 ----------
    def _write_header(self) -> None:
        """모든 곡선 타입이 공유하는 상단 헤더"""
        c = self.curve
        h = self.helper

        h.write("A3", f"'===================〈 IP  NO. {c.ip_no} >====================")
        h.write("A4", f"I P [ X ]  = {c.ip_xy[0]:.4f}")
        h.write("D4", f"I P [ Y ]  = {c.ip_xy[1]:.4f}")

        h.write("G6", "3차포물선" if c.curve_type == "cubic" else "단곡선")
        h.write("E6", f"({c.direction})")

        from 스크립트.선형관련.본선선형계산v10.본선선형계산v10 import degrees_to_dms
        h.write("A5", f"방위각 1  = {degrees_to_dms(c.h1)}")
        h.write("E5", f"방위각 2  = {degrees_to_dms(c.h2)}")
        h.write("A6", f"교각(IA)  = {degrees_to_dms(c.ia_degree)}")

        h.write("A7", "CURVE CENTER")
        h.write("C7", f"X  = {c.center_xy[0]:.4f}")
        h.write("F7", f"Y  = {c.center_xy[1]:.4f}")

        h.write("A8", f"R  = {c.radius:.3f}")
        h.write("C8", f"IP 연장1  = {c.ip_distance1:.3f}")

    # ---------- 서브클래스 구현 ----------
    @abstractmethod
    def _write_body(self) -> None:
        """곡선 타입별 본문 (M/Z/V, TL/CL, 측점/좌표 등)"""
        ...


# ============================================================
# 단곡선 Sheet Writer
# ============================================================
class SimpleCurveSheetWriter(BaseSheetWriter):
    """단곡선 시트 작성기"""

    def _write_body(self) -> None:
        c = self.curve
        h = self.helper

        # M/Z/V
        h.write("A9", "M = 0")
        h.write("C9", f"V = {c.v:.3f}")
        h.write("F9", f"Z = {c.z * 0.001:.3f}")

        # TL/CL/SL
        h.write("A10", f"TL = {c.tl:.3f}")
        h.write("C10", f"CL = {c.cl:.3f}")
        h.write("F10", f"SL = {c.params[2]:.3f}")

        # IP 측점
        from 스크립트.선형관련.본선선형계산v10.본선선형계산v10 import format_distance
        from 스크립트.선형관련.본선선형계산v10.본선선형계산v10 import Config
        h.write("A11", f"IP 정측점 = {format_distance(c.ip_sta, Config.KM_PRECISION)}")

        # BC/EC 측점
        h.write("B12", f"BC = {format_distance(c.bc_sta, Config.KM_PRECISION)}")
        h.write("B13", f"EC = {format_distance(c.ec_sta, Config.KM_PRECISION)}")

        # BC/EC 좌표
        h.write_coord("D12", "F12", c.bc_xy)
        h.write_coord("D13", "F13", c.ec_xy)


# ============================================================
# 3차포물선 Sheet Writer
# ============================================================
class CubicSheetWriter(BaseSheetWriter):
    """3차포물선 시트 작성기"""

    def _write_body(self) -> None:
        c = self.curve
        p = c.params
        h = self.helper

        # M/Z/V
        h.write("A9", f"M  = {c.m:.3f}")
        h.write("C9", f"V  = {c.v:.3f}")
        h.write("F9", f"Z  = {c.z * 0.001:.3f}")

        # TL/CL/LC/L/X1/Y1/SL
        h.write("A10", f"TL  = {p[10]:.3f}")
        h.write("C10", f"CL  = {p[12]:.3f}")
        h.write("A11", f"LC  = {p[11]:.3f}")
        h.write("A12", f"X1  = {p[0]:.3f}")
        h.write("C11", f"L  = {p[3]:.3f}")
        h.write("C12", f"Y1  = {p[4]:.3f}")
        h.write("F10", f"SL  = {p[13]:.3f}")

        # 각도

        from 스크립트.선형관련.본선선형계산v10.본선선형계산v10 import degrees_to_dms
        h.write("D13", f"THITA = {degrees_to_dms(math.degrees(c.theta_pc))}")
        h.write("A13", f"B  = {degrees_to_dms(math.degrees(p[16]))}")
        h.write("A14", f"C  = {degrees_to_dms(math.degrees(p[15]))}")
        h.write("D14", f"원곡선교각  = {degrees_to_dms(math.degrees(p[14]))}")

        # IP 측점
        from 스크립트.선형관련.본선선형계산v10.본선선형계산v10 import format_distance
        from 스크립트.선형관련.본선선형계산v10.본선선형계산v10 import Config
        h.write("A15", f"IP 정측점  = {format_distance(c.ip_sta, Config.KM_PRECISION)}")
        h.write("D15", f"IP 역측점  = {format_distance(c.ip_sta, Config.KM_PRECISION)}")

        # SP/PC/CP/PS 측점
        h.write("B16", f"SP  = {format_distance(c.sp_sta, Config.KM_PRECISION)}")
        h.write("B17", f"PC  = {format_distance(c.pc_sta, Config.KM_PRECISION)}")
        h.write("B18", f"CP  = {format_distance(c.cp_sta, Config.KM_PRECISION)}")
        h.write("B19", f"PS  = {format_distance(c.ps_sta, Config.KM_PRECISION)}")

        # SP/PC/CP/PS 좌표
        h.write_coord("D16", "F16", c.sp_xy)
        h.write_coord("D17", "F17", c.pc_xy)
        h.write_coord("D18", "F18", c.cp_xy)
        h.write_coord("D19", "F19", c.ps_xy)


# ============================================================
# 팩토리
# ============================================================
def create_sheet_writer(curve: "CurveParams") -> BaseSheetWriter:
    if curve.curve_type == "simplecurve":
        return SimpleCurveSheetWriter(curve)
    return CubicSheetWriter(curve)


# ============================================================
# 워크북 오케스트레이터
# ============================================================
class ReportWorkbook:
    """선형계산서 워크북 생성/저장"""

    def __init__(self, filename: Path | None = None):
        from 스크립트.선형관련.본선선형계산v10.본선선형계산v10 import Config
        self.filename = filename or (Config.ensure_output_dir() / Config.REPORT_FILENAME)
        self.workbook = Workbook()
        if "Sheet" in self.workbook.sheetnames:
            del self.workbook["Sheet"]

    def add_curve(self, curve: "CurveParams", station_groups: list[list["StationRow"]]) -> None:
        """IP별 시트 추가"""
        sheet = self.workbook.create_sheet(title=f"IP{curve.ip_no}")
        writer = create_sheet_writer(curve)
        writer.write(sheet, station_groups)

    def save(self) -> bool:
        """워크북 저장 (재시도 포함)"""
        return save_with_retry(self.workbook, self.filename)


# ============================================================
# 편의 함수 (기존 write_report 대체)
# ============================================================
def write_report(
    curves: list["CurveParams"],
    station_groups: list[list[list["StationRow"]]],
    filename: Path | None = None,
) -> None:
    """IP별 선형계산서 Excel 출력

    Args:
        curves: IP별 곡선 파라미터
        station_groups: IP별 측점 그룹 (curves와 같은 순서)
        filename: 출력 파일 경로 (None이면 기본 경로)
    """
    wb = ReportWorkbook(filename)

    for i, curve in enumerate(curves):
        groups = station_groups[i] if i < len(station_groups) else []
        wb.add_curve(curve, groups)

    if not wb.save():
        logger.error("선형계산서 저장 실패: %s", wb.filename)
        raise IOError(f"Excel 저장 실패: {wb.filename}")

    logger.info("선형계산서 저장 완료: %s", wb.filename)

# ============================================================
# 파일 I/O
# ============================================================
def save_with_retry(workbook, filename: Path, max_retries: int = None, delay: int = None) -> bool:
    """Excel 저장 재시도 (GUI 블로킹 최소화)"""
    from 스크립트.선형관련.본선선형계산v10.본선선형계산v10 import Config
    max_retries = max_retries or Config.SAVE_MAX_RETRIES
    delay = delay or Config.SAVE_RETRY_DELAY
    for attempt in range(max_retries):
        try:
            workbook.save(str(filename))
            logger.info("File saved: %s", filename)
            return True
        except PermissionError:
            logger.warning(
                "Attempt %d/%d: permission denied (%s). Retrying in %ds...",
                attempt + 1, max_retries, filename.name, delay,
            )
            import time
            time.sleep(delay)
    logger.error("Failed to save after %d attempts: %s", max_retries, filename)
    return False


def dxf_save_with_retry(doc, filename: str, max_retries: int = None, delay: int = None) -> bool:
    """DXF 저장 재시도"""
    max_retries = max_retries or Config.SAVE_MAX_RETRIES
    from 스크립트.선형관련.본선선형계산v10.본선선형계산v10 import Config
    delay = delay or Config.SAVE_RETRY_DELAY
    out_path = Config.ensure_output_dir() / filename
    for attempt in range(max_retries):
        try:
            doc.saveas(str(out_path))
            logger.info("DXF saved: %s", out_path)
            return True
        except PermissionError:
            logger.warning(
                "Attempt %d/%d: permission denied (%s). Retrying in %ds...",
                attempt + 1, max_retries, out_path.name, delay,
            )
            time.sleep(delay)
    logger.error("Failed to save DXF after %d attempts: %s", max_retries, out_path)
    return False