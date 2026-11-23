import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.lines import Line2D

from tps_engine import AdvancedUrbanTPS
from timetable_engine import (
    Station,
    SegmentRunResult,
    LineTimetableGenerator,
    format_sec_to_hhmmss,
)


@dataclass
class MixedTrainRun:
    train_number: str
    train_type: str  # "LOCAL" or "EXPRESS"
    dep_sec: int
    # [{"station": str, "pos_m": int, "arr_sec": Optional[int], "dep_sec": Optional[int], "is_pass": bool, "overtake_wait_sec": int}]
    stops: List[Dict] = field(default_factory=list)
    # [(time_sec, pos_m), ...] TPS 물리 궤적 (그래프 및 통과시각 정밀 계산용)
    trajectory: List[Tuple[float, float]] = field(default_factory=list)


def _interpolate_pass_time(history: List, target_pos_m: float) -> Optional[float]:
    """TPS history[(t, x, v, state)]에서 특정 거리(target_pos_m) 통과 시각(상대 초) 보간"""
    if not history:
        return None
    for i in range(len(history) - 1):
        t0, x0, _, _ = history[i]
        t1, x1, _, _ = history[i + 1]
        if x0 <= target_pos_m <= x1:
            if abs(x1 - x0) < 1e-6:
                return t0
            ratio = (target_pos_m - x0) / (x1 - x0)
            return t0 + ratio * (t1 - t0)
    return history[-1][0]


class MixedTimetablePlanner:
    def __init__(
        self,
        tps: AdvancedUrbanTPS,
        local_stations: List[Station],
        express_stations: List[Station],
        overtake_stations: Optional[List[str]] = None,
        min_headway_sec: int = 90,
    ):
        self.tps = tps
        self.local_stations = sorted(local_stations, key=lambda s: s.position_m)
        self.express_stations = sorted(express_stations, key=lambda s: s.position_m)
        self.overtake_stations = set(overtake_stations or [])
        self.min_headway_sec = min_headway_sec

        self.local_gen = LineTimetableGenerator(tps, self.local_stations)
        self.express_gen = LineTimetableGenerator(tps, self.express_stations)
        self.local_profile: List[SegmentRunResult] = []
        self.express_profile: List[SegmentRunResult] = []

    def build_profiles(self, margin_ratio: float = 0.05, round_to_5sec: bool = True):
        """완행·급행 표준 운전 시분 및 TPS 궤적 생성"""
        self.local_profile = self.local_gen.build_standard_run_profile(
            margin_ratio=margin_ratio, round_to_5sec=round_to_5sec, record_history=True
        )
        self.express_profile = self.express_gen.build_standard_run_profile(
            margin_ratio=margin_ratio, round_to_5sec=round_to_5sec, record_history=True
        )

    def _build_single_run(
        self,
        train_number: str,
        train_type: str,
        dep_sec: int,
        extra_dwell: Optional[Dict[str, int]] = None,
    ) -> MixedTrainRun:
        extra_dwell = extra_dwell or {}
        if train_type == "EXPRESS":
            all_stations = self.express_stations
            profile = self.express_profile
        else:
            all_stations = self.local_stations
            profile = self.local_profile

        stops_by_name: Dict[str, Dict] = {}
        trajectory: List[Tuple[float, float]] = []

        t_cursor = float(dep_sec)
        origin = profile[0].from_station
        origin_pos = all_stations[0].position_m
        stops_by_name[origin] = {
            "station": origin,
            "pos_m": origin_pos,
            "arr_sec": None,
            "dep_sec": int(round(t_cursor)),
            "is_pass": False,
            "overtake_wait_sec": 0,
        }

        for idx, seg in enumerate(profile):
            seg_start_t = t_cursor
            scale = seg.scheduled_time_sec / seg.history[-1][0] if seg.history and seg.history[-1][0] > 0 else 1.0

            # TPS 궤적 샘플링 (1초 간격 정도로 경량화)
            last_t = -999.0
            for t_rel, x_pos, _, _ in seg.history:
                abs_t = seg_start_t + t_rel * scale
                if abs_t - last_t >= 1.0:
                    trajectory.append((abs_t, x_pos))
                    last_t = abs_t
            if seg.history:
                trajectory.append((seg_start_t + seg.scheduled_time_sec, float(seg.to_pos_m)))

            # 중간 통과역 시각 보간
            for st in all_stations:
                if st.is_pass and st.name in seg.passed_stations:
                    pass_rel = _interpolate_pass_time(seg.history, float(st.position_m))
                    pass_abs = int(round(seg_start_t + (pass_rel * scale if pass_rel is not None else 0.0)))
                    stops_by_name[st.name] = {
                        "station": st.name,
                        "pos_m": st.position_m,
                        "arr_sec": pass_abs,
                        "dep_sec": pass_abs,
                        "is_pass": True,
                        "overtake_wait_sec": 0,
                    }

            arr_t = seg_start_t + seg.scheduled_time_sec
            is_terminal = (idx == len(profile) - 1)
            wait_sec = 0 if is_terminal else extra_dwell.get(seg.to_station, 0)
            dwell_t = 0 if is_terminal else (seg.dwell_time_sec + wait_sec)
            dep_t = None if is_terminal else (arr_t + dwell_t)

            stops_by_name[seg.to_station] = {
                "station": seg.to_station,
                "pos_m": seg.to_pos_m,
                "arr_sec": int(round(arr_t)),
                "dep_sec": int(round(dep_t)) if dep_t is not None else None,
                "is_pass": False,
                "overtake_wait_sec": wait_sec,
            }

            if dep_t is not None:
                trajectory.append((arr_t, float(seg.to_pos_m)))
                trajectory.append((dep_t, float(seg.to_pos_m)))
                t_cursor = dep_t

        ordered_stops = [stops_by_name[st.name] for st in all_stations if st.name in stops_by_name]
        return MixedTrainRun(
            train_number=train_number,
            train_type=train_type,
            dep_sec=dep_sec,
            stops=ordered_stops,
            trajectory=trajectory,
        )

    def _resolve_overtakes_with_next_express(
        self, local_dep_sec: int, express_dep_sec: int
    ) -> Dict[str, int]:
        """
        선행 완행(local_dep_sec)이 후속 급행(express_dep_sec)에게 추월당해야 하는지 판단하고,
        가능한 대피역에서 완행의 대피 정차 시간(extra_dwell)을 자동 계산.
        """
        extra_dwell: Dict[str, int] = {}
        exp_run = self._build_single_run("EXP_TMP", "EXPRESS", express_dep_sec)
        exp_map = {s["station"]: s for s in exp_run.stops}

        # 완행이 대피 없이 갔을 때 각 역의 시각 확인
        loc_base = self._build_single_run("LOC_TMP", "LOCAL", local_dep_sec)
        loc_map = {s["station"]: s for s in loc_base.stops}

        # 종착역 도착 기준 추월 필요 여부 확인
        term_name = self.local_stations[-1].name
        if loc_map[term_name]["arr_sec"] <= exp_map[term_name]["arr_sec"] - self.min_headway_sec:
            return extra_dwell  # 추월 없이 완행이 먼저 종착역 도착

        # 대피 가능한 역 중 급행이 통과하거나 정차하기 전에 완행이 먼저 도착하고,
        # 급행 통과/출발 후 min_headway_sec 뒤에 완행이 출발하도록 대피 시간 부여
        cumulative_shift = 0
        for st in self.local_stations[1:-1]:
            if st.name not in self.overtake_stations:
                continue
            loc_arr = loc_map[st.name]["arr_sec"] + cumulative_shift
            loc_dep = loc_map[st.name]["dep_sec"] + cumulative_shift
            exp_dep = exp_map[st.name]["dep_sec"]
            exp_arr = exp_map[st.name]["arr_sec"]

            # 완행이 급행 도착 최소 시격 전에 대피역에 들어오고, 그대로 출발하면 급행과 충돌/추월당하는 경우
            if loc_arr <= exp_arr - self.min_headway_sec and loc_dep < exp_dep + self.min_headway_sec:
                needed_dep = exp_dep + self.min_headway_sec
                wait_sec = int(needed_dep - loc_dep)
                if wait_sec > 0:
                    # 5초 단위 올림
                    wait_sec = ((wait_sec + 4) // 5) * 5
                    extra_dwell[st.name] = wait_sec
                    cumulative_shift += wait_sec
                    break  # 1회 대피로 해결되는지 우선 적용

        return extra_dwell

    def generate_mixed_timetable(
        self,
        first_departure_hhmm: str,
        last_departure_hhmm: str,
        base_headway_min: int = 5,
        pattern: Optional[List[str]] = None,
        auto_overtake: bool = True,
        local_prefix: str = "L",
        express_prefix: str = "E",
        start_number: int = 1001,
    ) -> List[MixedTrainRun]:
        """
        완행·급행 혼합 패턴 다이어 생성.
        예: pattern=["LOCAL", "LOCAL", "EXPRESS"], base_headway_min=5
        """
        if base_headway_min <= 0:
            raise ValueError("base_headway_min은 1분 이상이어야 합니다.")
        if not self.local_profile or not self.express_profile:
            self.build_profiles()

        pattern = pattern or ["LOCAL", "LOCAL", "EXPRESS"]
        fh, fm = map(int, first_departure_hhmm.split(":"))
        lh, lm = map(int, last_departure_hhmm.split(":"))
        curr_sec = fh * 3600 + fm * 60
        end_sec = lh * 3600 + lm * 60
        if end_sec < curr_sec:
            end_sec += 86400

        departures: List[Tuple[int, str]] = []
        idx = 0
        while curr_sec <= end_sec:
            t_type = pattern[idx % len(pattern)].upper()
            departures.append((curr_sec, t_type))
            curr_sec += base_headway_min * 60
            idx += 1

        runs: List[MixedTrainRun] = []
        loc_cnt = 0
        exp_cnt = 0

        for i, (dep_t, t_type) in enumerate(departures):
            if t_type == "EXPRESS":
                t_num = f"{express_prefix}{start_number + exp_cnt * 2}"
                exp_cnt += 1
                runs.append(self._build_single_run(t_num, "EXPRESS", dep_t))
            else:
                t_num = f"{local_prefix}{start_number + loc_cnt * 2}"
                loc_cnt += 1
                extra_dwell: Dict[str, int] = {}
                if auto_overtake and self.overtake_stations:
                    # 뒤따르는 가장 가까운 급행 열차 탐색
                    next_exp = next((d for d, tp in departures[i + 1:] if tp == "EXPRESS"), None)
                    if next_exp is not None:
                        extra_dwell = self._resolve_overtakes_with_next_express(dep_t, next_exp)
                runs.append(self._build_single_run(t_num, "LOCAL", dep_t, extra_dwell=extra_dwell))

        return runs

    def check_headway_conflicts(self, runs: List[MixedTrainRun]) -> List[Dict]:
        """전 역에서 연속 열차 간 최소 운전시격(min_headway_sec) 위반 여부 검사"""
        conflicts: List[Dict] = []
        station_names = [st.name for st in self.local_stations]

        for st_name in station_names:
            events = []
            for r in runs:
                match = next((s for s in r.stops if s["station"] == st_name), None)
                if match is None:
                    continue
                t_ref = match["dep_sec"] if match["dep_sec"] is not None else match["arr_sec"]
                events.append((t_ref, r.train_number, r.train_type, match))

            events.sort(key=lambda e: e[0])
            for j in range(len(events) - 1):
                t1, n1, tp1, _ = events[j]
                t2, n2, tp2, _ = events[j + 1]
                gap = t2 - t1
                if gap < self.min_headway_sec:
                    conflicts.append({
                        "station": st_name,
                        "train_a": f"{n1}({tp1})",
                        "train_b": f"{n2}({tp2})",
                        "time_a": format_sec_to_hhmmss(t1),
                        "time_b": format_sec_to_hhmmss(t2),
                        "gap_sec": gap,
                        "required_sec": self.min_headway_sec,
                    })
        return conflicts


def _configure_korean_font():
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
    for name in ["Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR"]:
        if name in {f.name for f in fm.fontManager.ttflist}:
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False


def plot_train_diagram(
    runs: List[MixedTrainRun],
    stations: List[Station],
    overtake_stations: Optional[List[str]] = None,
    save_path: str = "mixed_train_diagram.png",
    title: str = "완행·급행 혼합 열차운행도 (Time-Distance Diagram)",
):
    """시각(X축) - 거리/정거장(Y축) 열차 다이아그램 생성"""
    _configure_korean_font()
    overtake_set = set(overtake_stations or [])

    fig, ax = plt.subplots(figsize=(14, 8))

    # Y축 정거장 가로선 및 라벨
    y_positions = [st.position_m for st in stations]
    y_labels = [
        f"{st.name} (대피)" if st.name in overtake_set else st.name
        for st in stations
    ]
    for st in stations:
        is_ot = st.name in overtake_set
        ax.axhline(
            st.position_m,
            color="#94A3B8" if not is_ot else "#64748B",
            linestyle="-" if is_ot else "--",
            linewidth=0.9 if is_ot else 0.7,
            alpha=0.7,
        )

    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=9.5, fontweight="bold")
    ax.set_ylim(-400, max(y_positions) + 400)

    # 열차 궤적 그리기
    min_t = float("inf")
    max_t = float("-inf")

    for r in runs:
        if not r.trajectory:
            continue
        ts = [pt[0] / 60.0 for pt in r.trajectory]  # 분 단위 변환
        xs = [pt[1] for pt in r.trajectory]
        min_t = min(min_t, ts[0])
        max_t = max(max_t, ts[-1])

        is_exp = (r.train_type == "EXPRESS")
        color = "#DC2626" if is_exp else "#2563EB"
        lw = 2.2 if is_exp else 1.5
        ls = "-"

        ax.plot(ts, xs, color=color, linewidth=lw, linestyle=ls, alpha=0.9)

        # 열차번호 라벨 (출발 직후 지점)
        label_idx = min(len(ts) - 1, max(1, len(ts) // 22))
        ax.text(
            ts[label_idx],
            xs[label_idx],
            r.train_number,
            color=color,
            fontsize=7.8,
            fontweight="bold" if is_exp else "normal",
            rotation=28,
            ha="left",
            va="bottom",
        )

        # 대피 정차 구간 강조 마커
        for s in r.stops:
            if s.get("overtake_wait_sec", 0) > 0:
                t_a = s["arr_sec"] / 60.0
                t_d = s["dep_sec"] / 60.0
                ax.plot([t_a, t_d], [s["pos_m"], s["pos_m"]], color="#F59E0B", linewidth=4.2, solid_capstyle="round")

    # X축 시각 눈금 (10분 단위)
    start_tick = int(min_t // 10) * 10
    end_tick = int(max_t // 10 + 1) * 10
    ticks = list(range(start_tick, end_tick + 1, 10))
    tick_labels = [f"{(t // 60) % 24:02d}:{t % 60:02d}" for t in ticks]
    ax.set_xticks(ticks)
    ax.set_xticklabels(tick_labels, fontsize=9)
    ax.set_xlim(start_tick - 2, end_tick + 2)
    ax.grid(True, axis="x", linestyle=":", alpha=0.45)

    legend_handles = [
        Line2D([0], [0], color="#2563EB", lw=1.8, label="완행 (LOCAL)"),
        Line2D([0], [0], color="#DC2626", lw=2.4, label="급행 (EXPRESS)"),
        Line2D([0], [0], color="#F59E0B", lw=4.0, label="대피 정차 (Overtake Wait)"),
    ]
    ax.legend(handles=legend_handles, loc="upper left", fontsize=9.5, frameon=True, facecolor="white")
    ax.set_xlabel("운행 시각 (HH:MM)", fontsize=10.5, fontweight="bold")
    ax.set_ylabel("정거장 / 노선 거리 (m)", fontsize=10.5, fontweight="bold")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=14)

    plt.savefig(save_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"[열차운행도 저장 완료] {save_path}")