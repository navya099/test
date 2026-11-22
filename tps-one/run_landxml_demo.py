from tps_engine import TrainSpec
from landxml_loader import load_landxml_to_tps
from timetable_engine import Station, LineTimetableGenerator, format_sec_to_hhmmss
from demo import plot_run_curve


def main():
    xml_path = "c:/temp/landxml/실시설계-1구간.xml"

    # 1. 차량 제원 설정 (설계속도 100 km/h)
    train = TrainSpec(
        name="Express_EMU_100",
        max_speed_kmh=100.0,
        base_power_kw=2200.0,
    )

    # 2. LandXML 파싱 -> AdvancedUrbanTPS 자동 구성
    tps, summary = load_landxml_to_tps(
        xml_path=xml_path,
        train=train,
        curve_speed_factor=4.5,  # 곡선 제한속도 V = 4.5 * sqrt(R)
        apply_design_speed=True,
    )

    print("=" * 80)
    print(f"LandXML 선형명: {summary.alignment_name} (총 연장 {summary.length_m:.2f} m)")
    print(
        f"평면요소 {summary.coord_geom_count}개 | 종단 PVI {summary.pvi_count}개 | "
        f"최소 반경 {summary.min_radius_m:.1f} m | "
        f"구배 {summary.min_gradient_permille:.2f}‰ ~ {summary.max_gradient_permille:.2f}‰"
    )
    print("=" * 80)

    # 3. 정거장 위치 정의 (실제 역 위치에 맞게 수정하여 사용)
    stations = [
        Station("구래", 0, dwell_time_sec=0),
        Station("대포리", 2805, dwell_time_sec=30),
        Station("검단사거리", 6185, dwell_time_sec=30),
        Station("검단3동", 9512, dwell_time_sec=30),
        Station("서부면허시험장", 11260, dwell_time_sec=30),
        Station("계양", 14185, dwell_time_sec=30),
        Station("동양", 16427, dwell_time_sec=30),
        Station("김포공항", 19600, dwell_time_sec=0),
    ]

    # 4. 표준 운전 시분 산출
    generator = LineTimetableGenerator(tps, stations)
    std_profile = generator.build_standard_run_profile(
        margin_ratio=0.05, round_to_5sec=True, record_history=True
    )

    for seg in std_profile:
        print(
            f"{seg.from_station} -> {seg.to_station} ({seg.distance_m}m) | "
            f"최단 {seg.min_time_sec:.1f}s | 계획 {seg.scheduled_time_sec:.1f}s | "
            f"타행 {seg.coast_start_x:.1f}m | 전력 {seg.energy_kwh:.2f}kWh (-{seg.energy_saved_pct:.1f}%)"
        )

    # 5. BVE .Sta 구문 예시 출력 (첫 열차)
    timetable = generator.generate_pattern_timetable(
        first_departure_hhmm="07:00",
        last_departure_hhmm="07:30",
        headway_min=10,
        train_prefix="E",
        start_number=1001,
    )
    print("\n" + generator.export_bve_sta_commands(timetable[0]))

    # 6. 운전선도 및 구배 그래프 저장
    plot_run_curve(tps, stations, std_profile, save_path="real_alignment_curve.png")


if __name__ == "__main__":
    main()