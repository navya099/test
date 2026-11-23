from config import LANDXML_PATH
from tps_engine import TrainSpec, build_vvvf_tractive_table
from landxml_loader import load_landxml_to_tps
from timetable_engine import Station, LineTimetableGenerator, reverse_stations
from mixed_timetable import MixedTimetablePlanner, plot_train_diagram
from report_exporter import export_validation_csvs, export_validation_excel


def main():
    xml_path = LANDXML_PATH

    # 1. 차량 제원 및 F-v 견인력 곡선 설정
    fv_table = build_vvvf_tractive_table(
        mass_ton=180.0,
        rotational_factor=1.08,
        max_accel_ms2=0.83,
        base_power_kw=2200.0,
        weak_field_start_kmh=70.0,
        max_speed_kmh=100.0,
        step_kmh=5.0,
    )
    train = TrainSpec(
        name="Express_EMU_100 (120m)",
        length_m=120.0,
        max_speed_kmh=100.0,
        base_power_kw=2200.0,
        tractive_effort_table=fv_table,
    )

    # 2. LandXML 선형 불러오기 (하행 + 상행 반전)
    tps_down, summary = load_landxml_to_tps(
        xml_path=xml_path,
        train=train,
        curve_speed_factor=4.5,
        round_step_kmh=5.0,
    )
    tps_up = tps_down.create_reversed()

    # 3. 정거장 정의 (완행 / 급행)
    local_down = [
        Station("구래", 0, dwell_time_sec=0),
        Station("대포리", 2805, dwell_time_sec=30),
        Station("검단사거리", 6185, dwell_time_sec=30),
        Station("검단3동", 9512, dwell_time_sec=30),
        Station("서부면허시험장", 11260, dwell_time_sec=30),
        Station("계양", 14185, dwell_time_sec=30),
        Station("동양", 16427, dwell_time_sec=30),
        Station("김포공항", 19600, dwell_time_sec=0),
    ]
    express_down = [
        Station("구래", 0, dwell_time_sec=0),
        Station("대포리", 2805, dwell_time_sec=30, is_pass=True),
        Station("검단사거리", 6185, dwell_time_sec=30),
        Station("검단3동", 9512, dwell_time_sec=30),
        Station("서부면허시험장", 11260, dwell_time_sec=30, is_pass=True),
        Station("계양", 14185, dwell_time_sec=30),
        Station("동양", 16427, dwell_time_sec=30, is_pass=True),
        Station("김포공항", 19600, dwell_time_sec=0),
    ]
    local_up = reverse_stations(local_down, tps_down.length)
    express_up = reverse_stations(express_down, tps_down.length)

    # 4. 4가지 모드(완행/급행 × 하행/상행) 운전시분 계산
    profiles_by_mode = {
        "완행_하행(구래->김포)": LineTimetableGenerator(tps_down, local_down).build_standard_run_profile(margin_ratio=0.05, round_to_5sec=True),
        "완행_상행(김포->구래)": LineTimetableGenerator(tps_up, local_up).build_standard_run_profile(margin_ratio=0.05, round_to_5sec=True),
        "급행_하행(구래->김포)": LineTimetableGenerator(tps_down, express_down).build_standard_run_profile(margin_ratio=0.05, round_to_5sec=True),
        "급행_상행(김포->구래)": LineTimetableGenerator(tps_up, express_up).build_standard_run_profile(margin_ratio=0.05, round_to_5sec=True),
    }

    # 5. 완행·급행 혼합 다이어 생성 (3분 간격, 대피역: 검단사거리·계양)
    planner = MixedTimetablePlanner(
        tps=tps_down,
        local_stations=local_down,
        express_stations=express_down,
        overtake_stations=["검단사거리", "계양"],
        min_headway_sec=90,
    )
    planner.build_profiles(margin_ratio=0.05, round_to_5sec=True)
    mixed_runs = planner.generate_mixed_timetable(
        first_departure_hhmm="07:00",
        last_departure_hhmm="07:45",
        base_headway_min=3,
        pattern=["LOCAL", "LOCAL", "EXPRESS"],
        auto_overtake=True,
    )
    conflicts = planner.check_headway_conflicts(mixed_runs)

    # 6. CSV, 엑셀(.xlsx), 열차운행도 그래프 일괄 저장
    csv_files = export_validation_csvs(".", profiles_by_mode, mixed_runs)
    xlsx_file = export_validation_excel(
        output_xlsx_path="tps_validation_report.xlsx",
        summary=summary,
        curve_zones=tps_down.get_curve_summary(),
        profiles_by_mode=profiles_by_mode,
        mixed_runs=mixed_runs,
        conflicts=conflicts,
    )
    plot_train_diagram(
        runs=mixed_runs,
        stations=local_down,
        overtake_stations=["검단사거리", "계양"],
        save_path="mixed_train_diagram.png",
        title="구래 → 김포공항 완행·급행 혼합 열차운행도 (07:00~07:45, 3분 배차)",
    )

    print("생성 완료:")
    for f in csv_files + [xlsx_file, "mixed_train_diagram.png"]:
        print(" -", f)


if __name__ == "__main__":
    main()