import os
import csv
from typing import Dict, Tuple, List

from alignment.station.equation_manager import StationEquationManager
from alignment.widing.offset_alignment import OffsetAlignment
from alignment.widing.wideing_region import WideningRegion
from importer.dxf_exporter import DXFExporter
from profile.profile import Profile

from alignment.alignment import Alignment
from importer.csv_importer import CSVDesignSpecLoader


#==============================================================================


#6. 전체 워크플로우 데모 실행 (CSV 입력 -> 3D CSV & 3D DXF 일괄 출력)


#==============================================================================

def create_sample_input_csvs(work_dir: str):
    os.makedirs(work_dir, exist_ok=True)
    pi_path = os.path.join(work_dir, "input_pi.csv")
    pvi_path = os.path.join(work_dir, "input_pvi.csv")
    sup_path = os.path.join(work_dir, "input_superelevation.csv")
    with open(pi_path, "w", newline="", encoding="utf-8-sig") as f:

        w = csv.writer(f)
        w.writerow(["Name", "Easting", "Northing", "R", "L1", "L2", "A1", "A2"])
        w.writerow(["BP",   "200000.000", "500000.000", "0",   "",    "",   "", ""])
        w.writerow(["IP-1", "200450.000", "500250.000", "500", "100", "80", "", ""])
        w.writerow(["EP",   "200950.000", "500050.000", "0",   "",    "",   "", ""])
    with open(pvi_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Name", "RawStation", "Elevation", "L", "L1", "L2"])
        w.writerow(["BVP",   "0.0",   "40.00", "",    "", ""])
        w.writerow(["PVI-1", "450.0", "49.00", "200", "", ""])
        w.writerow(["EVP",   "1021.0313773989678", "44.00", "",    "", ""])
    with open(sup_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["RawStation", "LeftSlope", "RightSlope"])
        w.writerow(["0.0",   "-0.02", "-0.02"])
        w.writerow(["280.0", "-0.02", "-0.02"])
        w.writerow(["380.0", "0.05",  "-0.05"])
        w.writerow(["620.0", "0.05",  "-0.05"])
        w.writerow(["700.0", "-0.02", "-0.02"])
    return pi_path, pvi_path, sup_path

if __name__ == "__main__":
    out_dir = "./c3d_workflow_output"
    pi_csv, pvi_csv, sup_csv = create_sample_input_csvs(out_dir)
    # 1. CSV 제원 파일 로드 및 평면/종단/편경사 엔진 초기화
    h_align = Alignment.create(name="본선_중심선", pi_list=CSVDesignSpecLoader.load_pis_from_csv(pi_csv))
    v_prof = Profile.create(name='본선 종단(1)', pvi_list=CSVDesignSpecLoader.load_pvis_from_csv(pvi_csv))
    sup_tbl = CSVDesignSpecLoader.load_super_from_csv(sup_csv)
    # 2. 파정(Station Equation) 적용 (예: 물리적 300m 지점에서 1+300.000 = 1+350.000 점프)
    sta_mgr = StationEquationManager(start_station=1000.0, total_physical_length=h_align.total_length)
    sta_mgr.add_equation_by_back(station_back=1300.0, station_ahead=1350.0)
    # 3. 우측 차선 Offset Alignment + 버스베이 확폭 구간 정의
    right_lane = OffsetAlignment("우측차선_ETW", h_align, nominal_offset=+3.5).add_widening(
    WideningRegion("버스베이", start_station=150.0, end_station=260.0, widening_width=3.0, entry_transition_len=25.0, exit_transition_len=25.0)
    )
    left_lane = OffsetAlignment("좌측차선_ETW", h_align, nominal_offset=-3.5)
    # 4. 5m 간격으로 전 구간 3D 좌표 테이블(CSV) 및 DXF 형상선 데이터 생성
    feature_lines: Dict[str, List[Tuple[float, float, float]]] = {
    "CL": [], "L_ETW": [], "R_ETW": [], "L_Daylight": [], "R_Daylight": []
    }
    text_labels: List[Tuple[float, float, str]] = []
    out_csv_path = os.path.join(out_dir, "output_3d_coordinates.csv")
    print("Alignment Length :", h_align.total_length)

    with open(out_csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Raw_STA", "Display_STA", "Zone", "Code", "Offset(m)", "Easting(X)", "Northing(Y)", "Elevation(Z)"])

        interval = 5.0
        raw_sta = 0.0
        end_raw = h_align.total_length
        while raw_sta <= end_raw + 1e-6:
            s = min(raw_sta, end_raw)
            disp_sta, zone = sta_mgr.raw_to_display(s)
            disp_str = sta_mgr.format_station(disp_sta)
            cl_e, cl_n = h_align.point_location(s, 0.0)
            cl_el = v_prof.elevation_at(s)
            l_slope, r_slope = sup_tbl.get_slopes_at(s)
            # 동적 차선 폭원 계산 (확폭 반영)
            r_etw_off, r_etw_slope = right_lane.get_offset_at(s)
            l_etw_off, l_etw_slope = left_lane.get_offset_at(s)

            # 횡단 포인트 3D 좌표 산출 (중심선 -> 차선끝 -> 1:2 비탈면 1.5m)
            r_etw_el = cl_el + abs(r_etw_off) * r_slope
            l_etw_el = cl_el + abs(l_etw_off) * l_slope
            r_day_off = r_etw_off + 1.5
            l_day_off = l_etw_off - 1.5
            r_day_el = r_etw_el - 1.5 * 0.5
            l_day_el = l_etw_el - 1.5 * 0.5
            pts_map = {
            "CL": (0.0, cl_e, cl_n, cl_el),
            "L_ETW": (l_etw_off, *h_align.point_location(s, l_etw_off), l_etw_el),
            "R_ETW": (r_etw_off, *h_align.point_location(s, r_etw_off), r_etw_el),
            "L_Daylight": (l_day_off, *h_align.point_location(s, l_day_off), l_day_el),
            "R_Daylight": (r_day_off, *h_align.point_location(s, r_day_off), r_day_el),
            }
            for code, (off, e, n, z) in pts_map.items():
                feature_lines[code].append((e, n, z))
                writer.writerow([f"{s:.3f}", disp_str, zone, code, f"{off:.3f}", f"{e:.6f}", f"{n:.6f}", f"{z:.6f}"])
                # 20m 간격마다 DXF 도면용 측점 주석 추가
                if abs(round(s / 20.0) * 20.0 - s) < 1e-4:
                    text_labels.append((cl_e, cl_n, f"STA {disp_str}"))
                if s >= end_raw:
                    break
            raw_sta += interval
    # 5. AutoCAD / Civil 3D 호환 3D DXF 도면 저장
    out_dxf_path = os.path.join(out_dir, "output_corridor_model.dxf")
    DXFExporter.export_dxf_3d(out_dxf_path, feature_lines, text_labels)
    print(f"[완료] 3D 좌표 테이블 생성: {os.path.abspath(out_csv_path)}")
    print(f"[완료] 3D 코리더 DXF 생성 : {os.path.abspath(out_dxf_path)}")