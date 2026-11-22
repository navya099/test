from tps_engine import TrainSpec
from landxml_loader import load_landxml_to_tps
from timetable_engine import Station, LineTimetableGenerator, reverse_stations
from demo import plot_run_curve


def print_profile_summary(title: str, std_profile):
    print("\n" + "=" * 92)
    print(f" {title}")
    print("=" * 92)
    total_dist = 0
    total_run = 0.0
    total_dwell = 0
    total_kwh = 0.0

    for seg in std_profile:
        pass_note = f" [통과: {', '.join(seg.passed_stations)}]" if seg.passed_stations else ""
        print(
            f"{seg.from_station} -> {seg.to_station} ({seg.distance_m}m){pass_note} | "
            f"최단 {seg.min_time_sec:.1f}s | 계획 {seg.scheduled_time_sec:.1f}s | "
            f"타행 {seg.coast_start_x:.1f}m | 전력 {seg.energy_kwh:.2f}kWh (-{seg.energy_saved_pct:.1f}%)"
        )
        total_dist += seg.distance_m
        total_run += seg.scheduled_time_sec
        total_dwell += seg.dwell_time_sec
        total_kwh += seg.energy_kwh

    total_trip = total_run + total_dwell
    comm_spd = (total_dist / total_trip) * 3.6 if total_trip > 0 else 0.0
    print("-" * 92)
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

    # 3. 정거장 정의 (급행 예시: 대포리, 서부면허시험장, 동양 통과)
    express_stations_down = [
        Station("구래", 0, dwell_time_sec=0),
        Station("대포리", 2805, dwell_time_sec=30, is_pass=True),
        Station("검단사거리", 6185, dwell_time_sec=30),
        Station("검단3동", 9512, dwell_time_sec=30),
        Station("서부면허시험장", 11260, dwell_time_sec=30, is_pass=True),
        Station("계양", 14185, dwell_time_sec=30),
        Station("동양", 16427, dwell_time_sec=30, is_pass=True),
        Station("김포공항", 19600, dwell_time_sec=0),
    ]

    # 4. 급행 하행 (구래 -> 김포공항)
    gen_exp_down = LineTimetableGenerator(tps_down, express_stations_down)
    prof_exp_down = gen_exp_down.build_standard_run_profile(
        margin_ratio=0.05, round_to_5sec=True, record_history=True
    )
    print_profile_summary("[급행 하행] 구래 -> 김포공항 (대포리·서부면허시험장·동양 통과)", prof_exp_down)
    plot_run_curve(
        tps_down, express_stations_down, prof_exp_down,
        save_path="gurae_to_gimpo_express.png", title_suffix="급행 하행"
    )

    # 5. 급행 상행 (김포공항 -> 구래)
    tps_up = tps_down.create_reversed()
    express_stations_up = reverse_stations(express_stations_down, tps_down.length)
    gen_exp_up = LineTimetableGenerator(tps_up, express_stations_up)
    prof_exp_up = gen_exp_up.build_standard_run_profile(
        margin_ratio=0.05, round_to_5sec=True, record_history=True
    )
    print_profile_summary("[급행 상행] 김포공항 -> 구래 (동양·서부면허시험장·대포리 통과)", prof_exp_up)
    plot_run_curve(
        tps_up, express_stations_up, prof_exp_up,
        save_path="gimpo_to_gurae_express.png", title_suffix="급행 상행"
    )


if __name__ == "__main__":
    main()