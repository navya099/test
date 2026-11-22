import os
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.lines import Line2D
from tps_engine import TrainSpec, AdvancedUrbanTPS
from timetable_engine import (
    Station, LineTimetableGenerator, format_sec_to_hhmmss
)

def configure_korean_font():
    """운영체제별 한글 폰트 자동 설정"""
    noto_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    ]
    for path in noto_paths:
        if os.path.exists(path):
            fm.fontManager.addfont(path)
            plt.rcParams["font.family"] = fm.FontProperties(fname=path).get_name()
            plt.rcParams["axes.unicode_minus"] = False
            return

    candidates = [
        "Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR"
    ]
    available = {f.name for f in fm.fontManager.ttflist}
    for font_name in candidates:
        if font_name in available:
            plt.rcParams["font.family"] = font_name
            break
    plt.rcParams["axes.unicode_minus"] = False

def plot_run_curve(tps: AdvancedUrbanTPS, stations, std_profile, save_path: str = "run_curve.png"):
    """속도-거리 운전선도(Run Curve) 및 선로 구배 프로파일 시각화"""
    configure_korean_font()

    fig, (ax_spd, ax_grad) = plt.subplots(
        2, 1, figsize=(13, 7.5), sharex=True,
        gridspec_kw={"height_ratios": [3.2, 1.0], "hspace": 0.14}
    )

    max_spd = max(tps.speed_limit) if tps.speed_limit else 80.0

    # 1) 제한속도 프로파일
    x_grid = list(range(tps.length + 1))
    ax_spd.step(
        x_grid, tps.speed_limit, where="post",
        color="#475569", linestyle="--", linewidth=1.3, alpha=0.85, label="제한속도 (km/h)"
    )

    # 2) 운전 모드별 속도-거리 곡선
    state_colors = {
        "POWER": ("#DC2626", "역행 (POWER)"),
        "CRUISE": ("#16A34A", "정속 (CRUISE)"),
        "COAST": ("#2563EB", "타행 (COAST)"),
        "BRAKE": ("#9333EA", "제동 (BRAKE)"),
    }

    for seg in std_profile:
        hist = seg.history
        if not hist:
            continue
        chunk_x = [hist[0][1]]
        chunk_v = [hist[0][2]]
        curr_state = hist[0][3]

        for _, pos_m, v_kmh, state in hist[1:]:
            chunk_x.append(pos_m)
            chunk_v.append(v_kmh)
            if state != curr_state:
                color = state_colors.get(curr_state, ("#111827", curr_state))[0]
                ax_spd.plot(chunk_x, chunk_v, color=color, linewidth=2.3)
                chunk_x = [pos_m]
                chunk_v = [v_kmh]
                curr_state = state

        color = state_colors.get(curr_state, ("#111827", curr_state))[0]
        ax_spd.plot(chunk_x, chunk_v, color=color, linewidth=2.3)

        # 타행 개시 지점 마커
        ax_spd.axvline(seg.coast_start_x, color="#2563EB", linestyle=":", linewidth=1.0, alpha=0.55)

    # 3) 정거장 위치 및 역명 표기
    label_y = max_spd * 1.07
    for st in stations:
        ax_spd.axvline(st.position_m, color="#94A3B8", linestyle="-", linewidth=0.9, alpha=0.6)
        ax_grad.axvline(st.position_m, color="#94A3B8", linestyle="-", linewidth=0.9, alpha=0.6)
        ax_spd.text(
            st.position_m, label_y, st.name,
            ha="center", va="bottom", fontsize=9.5, fontweight="bold",
            color="#0F172A", bbox=dict(boxstyle="round,pad=0.2", fc="#F8FAFC", ec="#CBD5E1", lw=0.8)
        )

    legend_handles = [
        Line2D([0], [0], color=col, lw=2.4, label=lbl)
        for col, lbl in state_colors.values()
    ] + [
        Line2D([0], [0], color="#475569", lw=1.3, ls="--", label="선로 제한속도"),
        Line2D([0], [0], color="#2563EB", lw=1.0, ls=":", label="타행 개시 지점"),
    ]
    ax_spd.legend(handles=legend_handles, loc="lower right", ncol=3, fontsize=8.8, frameon=True, facecolor="white")

    ax_spd.set_ylim(0, max_spd * 1.2)
    ax_spd.set_xlim(0, tps.length)
    ax_spd.set_ylabel("속도 (km/h)", fontsize=10.5, fontweight="bold")
    ax_spd.set_title(
        f"전 역간 운전선도(Run Curve) 및 선로 구배 프로파일 — {tps.train.name}",
        fontsize=13, fontweight="bold", pad=16
    )
    ax_spd.grid(True, linestyle="--", alpha=0.35)

    # 4) 하단 선로 구배(‰) 프로파일
    grads = tps.gradient
    min_g = min(grads) if grads else -10.0
    max_g = max(grads) if grads else 10.0
    pad_g = max(5.0, (max_g - min_g) * 0.15)
    ax_grad.fill_between(x_grid, grads, 0, where=[g >= 0 for g in grads], step="post", color="#FCA5A5", alpha=0.6, label="상구배 (+)")
    ax_grad.fill_between(x_grid, grads, 0, where=[g < 0 for g in grads], step="post", color="#93C5FD", alpha=0.6, label="하구배 (-)")
    ax_grad.step(x_grid, grads, where="post", color="#334155", linewidth=1.0)
    ax_grad.axhline(0, color="#64748B", linewidth=0.8)
    ax_grad.set_ylabel("구배 (‰)", fontsize=10, fontweight="bold")
    ax_grad.set_xlabel("노선 거리 (m)", fontsize=10.5, fontweight="bold")
    ax_grad.set_ylim(min_g - pad_g, max_g + pad_g * 1.4)
    ax_grad.legend(loc="upper right", ncol=2, fontsize=8.5, frameon=True)
    ax_grad.grid(True, linestyle="--", alpha=0.35)

    plt.savefig(save_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"\n[그래프 저장 완료] {save_path}")

def run_demo():
    # 1. 차량 제원 및 노선(총 연장 6,200m) 초기화
    train = TrainSpec(name="Metro_VVVF_6Car", max_speed_kmh=80.0)
    tps = AdvancedUrbanTPS(train, total_length_m=6200)

    # 2. 선형/구배/제한속도 설정
    tps.set_track_segment(300, 900, grad=18.0, radius=350.0, limit=65.0)
    tps.set_track_segment(1800, 2600, grad=-12.0, radius=600.0, limit=75.0)
    tps.set_track_segment(3500, 4100, grad=22.0, radius=300.0, limit=60.0)
    tps.set_track_segment(5000, 5800, grad=-8.0)

    # 3. 정거장 리스트 정의
    stations = [
        Station("중앙역", 0, dwell_time_sec=0),
        Station("시청앞역", 1350, dwell_time_sec=30),
        Station("대학가역", 3100, dwell_time_sec=35),
        Station("테크노파크역", 4650, dwell_time_sec=25),
        Station("종점신도시역", 6200, dwell_time_sec=0),
    ]

    # 4. 전 역간 연속 시뮬레이션 (그래프 생성을 위해 record_history=True 설정)
    generator = LineTimetableGenerator(tps, stations)
    std_profile = generator.build_standard_run_profile(
        margin_ratio=0.05, round_to_5sec=True, record_history=True
    )

    print("=" * 88)
    print(f" [1] 전 역간 표준 운전 시분 및 에너지 최적화 결과 (차량: {train.name})")
    print("=" * 88)
    print(f"{'구간':<22} | {'거리':>6} | {'최단시분':>7} | {'계획시분':>7} | {'타행개시':>8} | {'소비전력':>8} | {'절감률':>6}")
    print("-" * 88)

    total_dist = 0
    total_run_sec = 0
    total_dwell_sec = 0
    total_kwh = 0.0

    for seg in std_profile:
        route_label = f"{seg.from_station}->{seg.to_station}"
        print(
            f"{route_label:<20} | {seg.distance_m:>5}m | "
            f"{seg.min_time_sec:>6.1f}s | {seg.scheduled_time_sec:>6.1f}s | "
            f"{seg.coast_start_x:>7.1f}m | {seg.energy_kwh:>6.2f}kWh | {seg.energy_saved_pct:>5.1f}%"
        )
        total_dist += seg.distance_m
        total_run_sec += seg.scheduled_time_sec
        total_dwell_sec += seg.dwell_time_sec
        total_kwh += seg.energy_kwh

    total_trip_sec = total_run_sec + total_dwell_sec
    commercial_speed = (total_dist / total_trip_sec) * 3.6
    print("-" * 88)
    print(
        f"▶ 전 구간 합계: 거리 {total_dist}m | 순수주행 {int(total_run_sec)}초 + 정차 {total_dwell_sec}초 "
        f"= 총 {int(total_trip_sec)}초 ({int(total_trip_sec//60)}분 {int(total_trip_sec%60)}초) "
        f"| 표정속도: {commercial_speed:.1f} km/h | 총 전력: {total_kwh:.2f} kWh\n"
    )

    # 5. 패턴 다이어 생성
    timetable = generator.generate_pattern_timetable(
        first_departure_hhmm="07:00",
        last_departure_hhmm="07:30",
        headway_min=6,
        train_prefix="K",
        start_number=2001
    )

    print("=" * 88)
    print(" [2] 자동 생성 열차 시각표 (출근시간대 6분 간격 패턴 다이어)")
    print("=" * 88)
    header = f"{'정거장명':<12} | " + " | ".join([f"{tr.train_number:^17}" for tr in timetable])
    print(header)
    print("-" * 88)

    for st_idx, st in enumerate(stations):
        row_cells = []
        for tr in timetable:
            stop_info = tr.stops[st_idx]
            arr = format_sec_to_hhmmss(stop_info["arr_sec"]) if stop_info["arr_sec"] is not None else "   --   "
            dep = format_sec_to_hhmmss(stop_info["dep_sec"]) if stop_info["dep_sec"] is not None else "   --   "
            row_cells.append(f"{arr}/{dep}")
        print(f"{st.name:<11} | " + " | ".join(row_cells))

    # 6. BVE .Sta 구문 출력
    print("\n" + "=" * 88)
    print(" [3] BVE 루트 파일(.csv) 삽입용 .Sta 구문 자동 출력 (K2001 열차 기준)")
    print("=" * 88)
    print(generator.export_bve_sta_commands(timetable[0]))

    # 7. 운전선도 및 구배 그래프 생성
    plot_run_curve(tps, stations, std_profile, save_path="run_curve.png")

if __name__ == "__main__":
    run_demo()