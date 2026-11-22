from tps_engine import TrainSpec
from landxml_loader import load_landxml_to_tps
from timetable_engine import Station, LineTimetableGenerator, reverse_stations
from demo import plot_run_curve


def print_profile_summary(title: str, std_profile):
    print("\n" + "=" * 86)
    print(f" {title}")
    print("=" * 86)
    total_dist = 0
    total_run = 0.0
    total_dwell = 0
    total_kwh = 0.0

    for seg in std_profile:
        print(
            f"{seg.from_station} -> {seg.to_station} ({seg.distance_m}m) | "
            f"최단 {seg.min_time_sec:.1f}s | 계획 {seg.scheduled_time_sec:.1f}s | "
            f"타행 {seg.coast_start_x:.1f}m | 전력 {seg.energy_kwh:.2f}kWh (-{seg.energy_saved_pct:.1f}%)"
        )
        total_dist += seg.distance_m
        total_run += seg.scheduled_time_sec
        total_dwell += seg.dwell_time_sec
        total_kwh += seg.energy_kwh

    total_trip = total_run + total_dwell
    comm_spd = (total_dist / total_trip) * 3.6 if total_trip > 0 else 0.0
    print("-" * 86)
    print(
        f"▶ 합계: {total_dist}m | 순수주행 {int(total_run)}초 + 정차 {total_dwell}초 "
        f"= 총 {int(total_trip)}초 ({int(total_trip // 60)}분 {int(total_trip % 60)}초) "
        f"| 표정속도 {comm_spd:.1f} km/h | 총 전력 {total_kwh:.2f} kWh"
    )


def main():
    xml_path = "실시설계-1구간.xml"

    # 1. 차량 제원 설정 (편성 길이 120m 반영)
    train = TrainSpec(
        name="Express_EMU_100 (120m)",
        length_m=120.0,
        max_speed_kmh=100.0,
        base_power_kw=2200.0,
    )

    # 2. LandXML 파싱 -> 하행(정방향: 구래 -> 김포공항) TPS 구성
    tps_down, summary = load_landxml_to_tps(
        xml_path=xml_path,
        train=train,
        curve_speed_factor=4.5,
        apply_design_speed=True,
    )
    tps_down.prepare_track()

    print(
        f"LandXML 선형명: {summary.alignment_name} (총 연장 {summary.length_m:.2f} m | "
        f"최소 반경 {summary.min_radius_m:.1f} m | 구배 {summary.min_gradient_permille:.2f}‰ ~ {summary.max_gradient_permille:.2f}‰)"
    )

    # 3. 정거장 위치 정의 (구래 -> 김포공항)
    stations_down = [
        Station("구래", 0, dwell_time_sec=0),
        Station("대포리", 2805, dwell_time_sec=30),
        Station("검단사거리", 6185, dwell_time_sec=30),
        Station("검단3동", 9512, dwell_time_sec=30),
        Station("서부면허시험장", 11260, dwell_time_sec=30),
        Station("계양", 14185, dwell_time_sec=30),
        Station("동양", 16427, dwell_time_sec=30),
        Station("김포공항", 19600, dwell_time_sec=0),
    ]

    # 4. 하행(구래 -> 김포공항) 시뮬레이션
    gen_down = LineTimetableGenerator(tps_down, stations_down)
    prof_down = gen_down.build_standard_run_profile(
        margin_ratio=0.05, round_to_5sec=True, record_history=True
    )
    print_profile_summary("[하행] 구래 -> 김포공항 표준 운전 시분표 (열차 길이 120m 반영)", prof_down)
    plot_run_curve(tps_down, stations_down, prof_down, save_path="gurae_to_gimpo.png")

    # 5. 상행(김포공항 -> 구래) 선형 및 정거장 반전 시뮬레이션
    tps_up = tps_down.create_reversed()
    stations_up = reverse_stations(stations_down, tps_down.length)
    gen_up = LineTimetableGenerator(tps_up, stations_up)
    prof_up = gen_up.build_standard_run_profile(
        margin_ratio=0.05, round_to_5sec=True, record_history=True
    )
    print_profile_summary("[상행] 김포공항 -> 구래 표준 운전 시분표 (선형 반전)", prof_up)
    plot_run_curve(tps_up, stations_up, prof_up, save_path="gimpo_to_gurae.png")


if __name__ == "__main__":
    main()