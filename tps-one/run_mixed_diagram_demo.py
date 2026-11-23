from config import LANDXML_PATH
from tps_engine import TrainSpec
from landxml_loader import load_landxml_to_tps
from timetable_engine import Station, format_sec_to_hhmmss
from mixed_timetable import MixedTimetablePlanner, plot_train_diagram


def main():
    xml_path = LANDXML_PATH

    # 1. 차량 제원 및 LandXML 선형 로드
    train = TrainSpec(
        name="Express_EMU_100 (120m)",
        length_m=120.0,
        max_speed_kmh=100.0,
        base_power_kw=2200.0,
    )
    tps, _ = load_landxml_to_tps(
        xml_path=xml_path,
        train=train,
        curve_speed_factor=4.5,
        round_step_kmh=5.0,
    )

    # 2. 완행 / 급행 정거장 정의
    local_stations = [
        Station("구래", 0, dwell_time_sec=0),
        Station("대포리", 2805, dwell_time_sec=30),
        Station("검단사거리", 6185, dwell_time_sec=30),
        Station("검단3동", 9512, dwell_time_sec=30),
        Station("서부면허시험장", 11260, dwell_time_sec=30),
        Station("계양", 14185, dwell_time_sec=30),
        Station("동양", 16427, dwell_time_sec=30),
        Station("김포공항", 19600, dwell_time_sec=0),
    ]

    express_stations = [
        Station("구래", 0, dwell_time_sec=0),
        Station("대포리", 2805, dwell_time_sec=30, is_pass=True),
        Station("검단사거리", 6185, dwell_time_sec=30),
        Station("검단3동", 9512, dwell_time_sec=30),
        Station("서부면허시험장", 11260, dwell_time_sec=30, is_pass=True),
        Station("계양", 14185, dwell_time_sec=30),
        Station("동양", 16427, dwell_time_sec=30, is_pass=True),
        Station("김포공항", 19600, dwell_time_sec=0),
    ]

    # 3. 혼합 다이어 플래너 (대피 가능역: 검단사거리, 계양 / 최소 시격 90초)
    overtake_stations = ["검단사거리", "계양"]
    planner = MixedTimetablePlanner(
        tps=tps,
        local_stations=local_stations,
        express_stations=express_stations,
        overtake_stations=overtake_stations,
        min_headway_sec=90,
    )
    planner.build_profiles(margin_ratio=0.05, round_to_5sec=True)

    # 4. 07:00 ~ 08:00, 6분 간격 [완행 -> 완행 -> 급행] 패턴 생성
    runs = planner.generate_mixed_timetable(
        first_departure_hhmm="07:00",
        last_departure_hhmm="08:00",
        base_headway_min=6,
        pattern=["LOCAL", "LOCAL", "EXPRESS"],
        auto_overtake=True,
    )

    # 5. 열차별 요약 및 대피 현황 출력
    print("=" * 92)
    print(" [완행·급행 혼합 다이어 요약] (구래 -> 김포공항, 07:00~08:00, 대피역: 검단사거리·계양)")
    print("=" * 92)
    for r in runs:
        dep = format_sec_to_hhmmss(r.stops[0]["dep_sec"])
        arr = format_sec_to_hhmmss(r.stops[-1]["arr_sec"])
        waits = [f"{s['station']}(+{s['overtake_wait_sec']}s)" for s in r.stops if s["overtake_wait_sec"] > 0]
        wait_str = f" | 대피정차: {', '.join(waits)}" if waits else ""
        print(f"{r.train_number:<6} [{r.train_type:<7}] | 출발 {dep} -> 도착 {arr}{wait_str}")

    # 6. 최소 운전시격(90초) 충돌 검사
    conflicts = planner.check_headway_conflicts(runs)
    print("\n=== 최소 운전시격(90초) 충돌 검사 ===")
    if not conflicts:
        print("▶ 충돌 없음 (전 역 최소 시격 90초 이상 확보)")
    else:
        for c in conflicts:
            print(
                f"[충돌] {c['station']} | {c['train_a']}({c['time_a']}) vs "
                f"{c['train_b']}({c['time_b']}) -> 시격 {c['gap_sec']}초"
            )

    # 7. 열차운행도(Time-Distance 다이아그램) 생성
    plot_train_diagram(
        runs=runs,
        stations=local_stations,
        overtake_stations=overtake_stations,
        save_path="mixed_train_diagram.png",
        title="구래 → 김포공항 완행·급행 혼합 열차운행도 (07:00~08:00)",
    )


if __name__ == "__main__":
    main()