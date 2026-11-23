import csv
import pathlib
from typing import Dict, List
import openpyxl
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import range_boundaries

from landxml_loader import LandXMLSummary
from timetable_engine import SegmentRunResult, format_sec_to_hhmmss
from mixed_timetable import MixedTrainRun


PRIMARY_COLOR = "1E3A5F"
ACCENT_COLOR = "2563EB"
ALT_ROW_COLOR = "F4F7FB"
BORDER_COLOR = "CBD5E1"
WARN_FILL_COLOR = "FEF3C7"


def _style_merged_range(ws, cell_range, font=None, fill=None, alignment=None):
    min_col, min_row, max_col, max_row = range_boundaries(cell_range)
    for row in ws.iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col):
        for cell in row:
            if font:
                cell.font = font
            if fill:
                cell.fill = fill
            if alignment:
                cell.alignment = alignment


def _auto_fit_columns(ws, skip_rows=()):
    merged_multi = {
        cell.coordinate
        for rng in ws.merged_cells.ranges
        if rng.min_col != rng.max_col
        for row in ws[rng.coord]
        for cell in row
    }
    for col in ws.columns:
        max_len = 0
        for cell in col:
            if cell.row in skip_rows or cell.coordinate in merged_multi:
                continue
            val = str(cell.value) if cell.value is not None else ""
            if val.startswith("="):
                continue
            # 한글 폭 보정 (한글 1자 ≈ 영문 1.8자)
            disp_len = sum(1.8 if ord(ch) > 127 else 1.0 for ch in val)
            max_len = max(max_len, disp_len)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = min(max(int(max_len) + 5, 12), 42)


def export_validation_csvs(
    output_dir: str,
    profiles_by_mode: Dict[str, List[SegmentRunResult]],
    mixed_runs: List[MixedTrainRun],
) -> List[str]:
    """역간 운전시분 및 혼합 다이어 결과를 UTF-8(BOM) CSV 파일로 저장"""
    out_path = pathlib.Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    created: List[str] = []

    seg_csv = out_path / "segment_run_summary.csv"
    with open(seg_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "운행모드", "출발역", "도착역", "통과역", "거리(m)",
            "최단시분(s)", "계획시분(s)", "정차시간(s)",
            "타행개시(m)", "소비전력(kWh)", "에너지절감률(%)"
        ])
        for mode_name, segs in profiles_by_mode.items():
            for seg in segs:
                writer.writerow([
                    mode_name,
                    seg.from_station,
                    seg.to_station,
                    ", ".join(seg.passed_stations) if seg.passed_stations else "-",
                    seg.distance_m,
                    round(seg.min_time_sec, 1),
                    round(seg.scheduled_time_sec, 1),
                    seg.dwell_time_sec,
                    round(seg.coast_start_x, 1),
                    round(seg.energy_kwh, 3),
                    round(seg.energy_saved_pct, 1),
                ])
    created.append(str(seg_csv))

    tt_csv = out_path / "mixed_timetable_summary.csv"
    with open(tt_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "열차번호", "종별", "출발시각", "도착시각",
            "총소요시간(s)", "대피정차역", "대피시간(s)"
        ])
        for r in mixed_runs:
            dep_s = r.stops[0]["dep_sec"]
            arr_s = r.stops[-1]["arr_sec"]
            waits = [s for s in r.stops if s["overtake_wait_sec"] > 0]
            wait_st = ", ".join(s["station"] for s in waits) if waits else "-"
            wait_sec = sum(s["overtake_wait_sec"] for s in waits)
            writer.writerow([
                r.train_number,
                r.train_type,
                format_sec_to_hhmmss(dep_s),
                format_sec_to_hhmmss(arr_s),
                arr_s - dep_s,
                wait_st,
                wait_sec,
            ])
    created.append(str(tt_csv))
    return created


def export_validation_excel(
    output_xlsx_path: str,
    summary: LandXMLSummary,
    curve_zones: List[Dict],
    profiles_by_mode: Dict[str, List[SegmentRunResult]],
    mixed_runs: List[MixedTrainRun],
    conflicts: List[Dict],
) -> str:
    """실선형 검증 결과를 다중 시트 엑셀(.xlsx) 리포트로 생성"""
    wb = openpyxl.Workbook()

    header_fill = PatternFill(start_color=PRIMARY_COLOR, end_color=PRIMARY_COLOR, fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=15, bold=True, color=PRIMARY_COLOR)
    sub_font = Font(name="Calibri", size=10, color="475569")
    alt_fill = PatternFill(start_color=ALT_ROW_COLOR, end_color=ALT_ROW_COLOR, fill_type="solid")
    warn_fill = PatternFill(start_color=WARN_FILL_COLOR, end_color=WARN_FILL_COLOR, fill_type="solid")
    thin_border = Border(
        left=Side(style="thin", color=BORDER_COLOR),
        right=Side(style="thin", color=BORDER_COLOR),
        top=Side(style="thin", color=BORDER_COLOR),
        bottom=Side(style="thin", color=BORDER_COLOR),
    )

    # =========================================================================
    # Sheet 1: 요약_대시보드
    # =========================================================================
    ws1 = wb.active
    ws1.title = "요약_대시보드"
    ws1.views.sheetView[0].showGridLines = True
    ws1.page_setup.orientation = "landscape"
    ws1.sheet_properties.pageSetUpPr.fitToPage = True

    ws1.merge_cells("A1:H1")
    ws1["A1"].value = f"실선형 TPS 및 운전시분 검증 리포트 — {summary.alignment_name}"
    ws1["A1"].font = title_font
    ws1["A1"].alignment = Alignment(vertical="center")
    ws1.row_dimensions[1].height = 28

    ws1.merge_cells("A2:H2")
    ws1["A2"].value = (
        f"LandXML 연장 {summary.length_m:,.2f} m | 최소 반경 {summary.min_radius_m:.1f} m | "
        f"구배 {summary.min_gradient_permille:.2f}‰ ~ {summary.max_gradient_permille:.2f}‰ | "
        f"설계속도 {summary.design_speeds[0][1] if summary.design_speeds else 100:.0f} km/h"
    )
    ws1["A2"].font = sub_font
    ws1.row_dimensions[2].height = 20

    # KPI 카드 (A4:H6)
    kpis = [
        ("A4:B4", "노선 총 연장", "A5:B5", f"{summary.length_m:,.1f} m", "A6:B6", f"평면 {summary.coord_geom_count} / PVI {summary.pvi_count}"),
        ("C4:D4", "최소 곡선반경", "C5:D5", f"{summary.min_radius_m:.1f} m", "C6:D6", f"곡선 구간 {len(curve_zones)}개소"),
        ("E4:F4", "고밀도 배차 열차수", "E5:F5", f"{len(mixed_runs)} 편성", "E6:F6", "3분 간격 (L-L-E)"),
        ("G4:H4", "운전시격 충돌", "G5:H5", f"{len(conflicts)} 건", "G6:H6", "최소 시격 90초 기준"),
    ]
    kpi_h_font = Font(size=9, bold=True, color="FFFFFF")
    kpi_v_font = Font(size=14, bold=True, color=PRIMARY_COLOR)
    kpi_s_font = Font(size=9, color="64748B")
    center = Alignment(horizontal="center", vertical="center")
    for hr, ht, vr, vt, sr, st in kpis:
        ws1.merge_cells(hr)
        ws1[hr.split(":")[0]].value = ht
        _style_merged_range(ws1, hr, font=kpi_h_font, fill=header_fill, alignment=center)
        ws1.merge_cells(vr)
        ws1[vr.split(":")[0]].value = vt
        _style_merged_range(ws1, vr, font=kpi_v_font, alignment=center)
        ws1.merge_cells(sr)
        ws1[sr.split(":")[0]].value = st
        _style_merged_range(ws1, sr, font=kpi_s_font, alignment=center)

    # 모드별 비교 요약 테이블 (Row 8~13, Cols A~G, 역간_운전시분 시트 참조 수식 사용)
    sum_headers = [
        "운행 모드", "총 거리(m)", "순수주행(s)", "정차시간(s)",
        "총 소요시간(s)", "표정속도(km/h)", "총 소비전력(kWh)"
    ]
    for col_idx, h_text in enumerate(sum_headers, start=1):
        c = ws1.cell(row=8, column=col_idx, value=h_text)
        c.fill = header_fill
        c.font = header_font
        c.alignment = Alignment(horizontal="left" if col_idx == 1 else "right", vertical="center")
    ws1.row_dimensions[8].height = 22

    # 역간_운전시분 시트의 각 모드 행 범위 계산
    mode_names = list(profiles_by_mode.keys())
    cur_row = 2
    mode_ranges = {}
    for m_name in mode_names:
        cnt = len(profiles_by_mode[m_name])
        mode_ranges[m_name] = (cur_row, cur_row + cnt - 1)
        cur_row += cnt

    for idx, m_name in enumerate(mode_names):
        r_idx = 9 + idx
        r0, r1 = mode_ranges[m_name]
        ws1.cell(row=r_idx, column=1, value=m_name)
        ws1.cell(row=r_idx, column=2, value=f"=SUM('역간_운전시분'!E{r0}:E{r1})")
        ws1.cell(row=r_idx, column=3, value=f"=SUM('역간_운전시분'!G{r0}:G{r1})")
        ws1.cell(row=r_idx, column=4, value=f"=SUM('역간_운전시분'!H{r0}:H{r1})")
        ws1.cell(row=r_idx, column=5, value=f"=C{r_idx}+D{r_idx}")
        ws1.cell(row=r_idx, column=6, value=f"=(B{r_idx}/E{r_idx})*3.6")
        ws1.cell(row=r_idx, column=7, value=f"=SUM('역간_운전시분'!J{r0}:J{r1})")

        for col_idx in range(1, 8):
            c = ws1.cell(row=r_idx, column=col_idx)
            c.border = thin_border
            if idx % 2 == 1:
                c.fill = alt_fill
            c.alignment = Alignment(horizontal="left" if col_idx == 1 else "right", vertical="center")
            if col_idx in (2, 3, 4, 5):
                c.number_format = "#,##0"
            elif col_idx in (6, 7):
                c.number_format = "#,##0.00"

    # 임베디드 차트 (Stacked: Row 15부터 A15에 배치)
    chart = BarChart()
    chart.type = "col"
    chart.style = 10
    chart.title = "운행 모드별 총 소요시간(초) 및 소비전력(kWh)"
    chart.y_axis.title = "수치"
    chart.width = 18
    chart.height = 10

    data_ref = Reference(ws1, min_col=5, max_col=5, min_row=8, max_row=8 + len(mode_names))
    energy_ref = Reference(ws1, min_col=7, max_col=7, min_row=8, max_row=8 + len(mode_names))
    cats_ref = Reference(ws1, min_col=1, min_row=9, max_row=8 + len(mode_names))
    chart.add_data(data_ref, titles_from_data=True)
    chart.add_data(energy_ref, titles_from_data=True)
    chart.set_categories(cats_ref)
    ws1.add_chart(chart, "A15")

    _auto_fit_columns(ws1, skip_rows=(1, 2, 4, 5, 6))

    # =========================================================================
    # Sheet 2: 역간_운전시분
    # =========================================================================
    ws2 = wb.create_sheet("역간_운전시분")
    ws2.views.sheetView[0].showGridLines = True
    ws2.freeze_panes = "A2"
    ws2.page_setup.orientation = "landscape"
    ws2.sheet_properties.pageSetUpPr.fitToPage = True

    seg_headers = [
        "운행모드", "출발역", "도착역", "통과역", "거리(m)",
        "최단시분(s)", "계획시분(s)", "정차시간(s)",
        "타행개시(m)", "소비전력(kWh)", "에너지절감률(%)"
    ]
    for col_idx, h_text in enumerate(seg_headers, start=1):
        c = ws2.cell(row=1, column=col_idx, value=h_text)
        c.fill = header_fill
        c.font = header_font
        c.alignment = Alignment(horizontal="left" if col_idx <= 4 else "right", vertical="center")
    ws2.row_dimensions[1].height = 22

    row_cursor = 2
    for mode_name, segs in profiles_by_mode.items():
        for seg in segs:
            ws2.append([
                mode_name,
                seg.from_station,
                seg.to_station,
                ", ".join(seg.passed_stations) if seg.passed_stations else "-",
                seg.distance_m,
                round(seg.min_time_sec, 1),
                round(seg.scheduled_time_sec, 1),
                seg.dwell_time_sec,
                round(seg.coast_start_x, 1),
                round(seg.energy_kwh, 3),
                round(seg.energy_saved_pct / 100.0, 4),
            ])
            for col_idx in range(1, 12):
                c = ws2.cell(row=row_cursor, column=col_idx)
                c.border = thin_border
                if row_cursor % 2 == 1:
                    c.fill = alt_fill
                c.alignment = Alignment(horizontal="left" if col_idx <= 4 else "right", vertical="center")
                if col_idx in (5, 8):
                    c.number_format = "#,##0"
                elif col_idx in (6, 7, 9):
                    c.number_format = "#,##0.0"
                elif col_idx == 10:
                    c.number_format = "#,##0.00"
                elif col_idx == 11:
                    c.number_format = "0.0%"
            row_cursor += 1

    _auto_fit_columns(ws2)

    # =========================================================================
    # Sheet 3: 혼합_다이어_3분
    # =========================================================================
    ws3 = wb.create_sheet("혼합_다이어_3분")
    ws3.views.sheetView[0].showGridLines = True
    ws3.freeze_panes = "A2"
    ws3.page_setup.orientation = "landscape"
    ws3.sheet_properties.pageSetUpPr.fitToPage = True

    tt_headers = [
        "열차번호", "종별", "출발시각", "도착시각",
        "총소요(초)", "대피정차역", "대피추가시간(초)"
    ]
    for col_idx, h_text in enumerate(tt_headers, start=1):
        c = ws3.cell(row=1, column=col_idx, value=h_text)
        c.fill = header_fill
        c.font = header_font
        c.alignment = Alignment(horizontal="center" if col_idx <= 4 else "right", vertical="center")
    ws3.row_dimensions[1].height = 22

    for idx, r in enumerate(mixed_runs, start=2):
        dep_s = r.stops[0]["dep_sec"]
        arr_s = r.stops[-1]["arr_sec"]
        waits = [s for s in r.stops if s["overtake_wait_sec"] > 0]
        wait_st = ", ".join(s["station"] for s in waits) if waits else "-"
        wait_sec = sum(s["overtake_wait_sec"] for s in waits)

        ws3.append([
            r.train_number,
            r.train_type,
            format_sec_to_hhmmss(dep_s),
            format_sec_to_hhmmss(arr_s),
            arr_s - dep_s,
            wait_st,
            wait_sec,
        ])
        for col_idx in range(1, 8):
            c = ws3.cell(row=idx, column=col_idx)
            c.border = thin_border
            if wait_sec > 0:
                c.fill = warn_fill
            elif idx % 2 == 1:
                c.fill = alt_fill
            c.alignment = Alignment(horizontal="center" if col_idx <= 4 or col_idx == 6 else "right", vertical="center")
            if col_idx in (5, 7):
                c.number_format = "#,##0"

    _auto_fit_columns(ws3)

    # =========================================================================
    # Sheet 4: 선형_곡선_요약
    # =========================================================================
    ws4 = wb.create_sheet("선형_곡선_요약")
    ws4.views.sheetView[0].showGridLines = True
    ws4.freeze_panes = "A2"
    ws4.page_setup.orientation = "landscape"
    ws4.sheet_properties.pageSetUpPr.fitToPage = True

    c_headers = ["곡선구간 번호", "시작(m)", "종료(m)", "연장(m)", "최소 반경(m)", "적용 제한속도(km/h)"]
    for col_idx, h_text in enumerate(c_headers, start=1):
        c = ws4.cell(row=1, column=col_idx, value=h_text)
        c.fill = header_fill
        c.font = header_font
        c.alignment = Alignment(horizontal="center" if col_idx == 1 else "right", vertical="center")
    ws4.row_dimensions[1].height = 22

    for idx, cz in enumerate(curve_zones, start=2):
        ws4.append([
            idx - 1,
            cz["start_m"],
            cz["end_m"],
            f"=C{idx}-B{idx}+1",
            cz["min_radius_m"],
            cz["speed_limit_kmh"],
        ])
        for col_idx in range(1, 7):
            c = ws4.cell(row=idx, column=col_idx)
            c.border = thin_border
            if idx % 2 == 1:
                c.fill = alt_fill
            c.alignment = Alignment(horizontal="center" if col_idx == 1 else "right", vertical="center")
            if col_idx in (1, 2, 3, 4):
                c.number_format = "#,##0"
            else:
                c.number_format = "#,##0.0"

    _auto_fit_columns(ws4)

    out_path = pathlib.Path(output_xlsx_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out_path))
    return str(out_path)