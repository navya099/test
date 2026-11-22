import math
from dataclasses import dataclass, field
from typing import List, Dict
from tps_engine import AdvancedUrbanTPS

@dataclass
class Station:
    name: str
    position_m: int          # 역 중심(정차 목표) 거리 (m)
    dwell_time_sec: int = 30 # 기본 정차 시간 (초)
    is_pass: bool = False    # 급행 열차 통과 여부 (확장 대비)

@dataclass
class SegmentRunResult:
    from_station: str
    to_station: str
    distance_m: int
    min_time_sec: float
    scheduled_time_sec: float
    dwell_time_sec: int
    coast_start_x: float
    energy_kwh: float
    energy_saved_pct: float
    to_pos_m: int = 0
    history: List = field(default_factory=list)

@dataclass
class TrainSchedule:
    train_number: str
    stops: List[Dict] # [{"station": str, "pos_m": int, "arr_sec": int, "dep_sec": int}, ...]

def reverse_stations(stations: List[Station], total_length_m: int) -> List[Station]:
    """상·하행 반전용 정거장 리스트 변환 (position_m -> total_length_m - position_m)"""
    sorted_desc = sorted(stations, key=lambda st: st.position_m, reverse=True)
    reversed_list: List[Station] = []
    for idx, st in enumerate(sorted_desc):
        is_endpoint = (idx == 0 or idx == len(sorted_desc) - 1)
        reversed_list.append(
            Station(
                name=st.name,
                position_m=total_length_m - st.position_m,
                dwell_time_sec=0 if is_endpoint else st.dwell_time_sec,
                is_pass=st.is_pass,
            )
        )
    return reversed_list

def format_sec_to_hhmmss(total_sec: int) -> str:
    """초 단위 시간을 HH:MM:SS 문자열로 변환 (24시 이후 심야 운행 지원)"""
    total_sec = int(round(total_sec))
    h = (total_sec // 3600) % 24
    m = (total_sec % 3600) // 60
    s = total_sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def format_sec_to_bve_time(total_sec: int) -> str:
    """BVE .Sta 구문용 HH.MMSS 형식 변환 (예: 08:05:30 -> 08.0530)"""
    total_sec = int(round(total_sec))
    h = (total_sec // 3600) % 24
    m = (total_sec % 3600) // 60
    s = total_sec % 60
    return f"{h:02d}.{m:02d}{s:02d}"

class LineTimetableGenerator:
    def __init__(self, tps: AdvancedUrbanTPS, stations: List[Station]):
        if len(stations) < 2:
            raise ValueError("최소 2개 이상의 정거장이 필요합니다.")
        self.tps = tps
        self.stations = sorted(stations, key=lambda st: st.position_m)
        if self.stations[-1].position_m > self.tps.length:
            raise ValueError("종착역 위치가 노선 총 연장을 초과합니다.")
        self.standard_segments: List[SegmentRunResult] = []

    def build_standard_run_profile(
        self,
        margin_ratio: float = 0.05,
        round_to_5sec: bool = True,
        record_history: bool = False
    ) -> List[SegmentRunResult]:
        """
        전 역간 연속 시뮬레이션을 수행하여 표준 운전 시분표(기준 운전선도) 생성.
        round_to_5sec=True 일 경우 실제 철도 다이어처럼 5초 단위로 시분 올림 후 타행 재최적화.
        """
        self.standard_segments.clear()

        for i in range(len(self.stations) - 1):
            st_from = self.stations[i]
            st_to = self.stations[i + 1]
            start_x = st_from.position_m
            stop_x = st_to.position_m

            opt_res = self.tps.optimize_coasting_for_target_time(
                start_x,
                stop_x,
                margin_ratio=margin_ratio,
                record_history=(record_history and not round_to_5sec),
            )
            scheduled_sec = opt_res["target_time_sec"]

            if round_to_5sec:
                scheduled_sec = float(math.ceil(scheduled_sec / 5.0) * 5)
                opt_res = self.tps.optimize_coasting_for_target_time(
                    start_x, stop_x, target_time_sec=scheduled_sec, record_history=record_history
                )

            dwell = 0 if i == len(self.stations) - 2 else st_to.dwell_time_sec

            seg_result = SegmentRunResult(
                from_station=st_from.name,
                to_station=st_to.name,
                distance_m=stop_x - start_x,
                min_time_sec=opt_res["min_possible_time_sec"],
                scheduled_time_sec=scheduled_sec,
                dwell_time_sec=dwell,
                coast_start_x=opt_res["coast_start_x"],
                energy_kwh=opt_res["energy_kwh"],
                energy_saved_pct=opt_res["energy_saved_pct"],
                to_pos_m=stop_x,
                history=opt_res["history"]
            )
            self.standard_segments.append(seg_result)

        return self.standard_segments

    def generate_pattern_timetable(
        self,
        first_departure_hhmm: str,
        last_departure_hhmm: str,
        headway_min: int,
        train_prefix: str = "S",
        start_number: int = 1001
    ) -> List[TrainSchedule]:
        """
        산출된 표준 운전 시분을 바탕으로 시발역~종착역 패턴 다이어(전체 열차 시각표) 자동 생성
        """
        if headway_min <= 0:
            raise ValueError("배차 간격(headway_min)은 1분 이상이어야 합니다.")

        if not self.standard_segments:
            self.build_standard_run_profile()

        fh, fm = map(int, first_departure_hhmm.split(":"))
        lh, lm = map(int, last_departure_hhmm.split(":"))
        curr_dep_sec = fh * 3600 + fm * 60
        end_dep_sec = lh * 3600 + lm * 60
        if end_dep_sec < curr_dep_sec:
            end_dep_sec += 86400
        headway_sec = headway_min * 60

        schedules: List[TrainSchedule] = []
        train_idx = 0

        while curr_dep_sec <= end_dep_sec:
            t_num = f"{train_prefix}{start_number + train_idx * 2}"
            stops_data = []

            t_cursor = curr_dep_sec
            first_st = self.stations[0]
            stops_data.append({
                "station": first_st.name,
                "pos_m": first_st.position_m,
                "arr_sec": None,
                "dep_sec": t_cursor
            })

            for idx, seg in enumerate(self.standard_segments):
                arr_t = t_cursor + int(seg.scheduled_time_sec)
                is_terminal = (idx == len(self.standard_segments) - 1)
                dep_t = None if is_terminal else (arr_t + seg.dwell_time_sec)

                stops_data.append({
                    "station": seg.to_station,
                    "pos_m": seg.to_pos_m,
                    "arr_sec": arr_t,
                    "dep_sec": dep_t
                })
                if dep_t is not None:
                    t_cursor = dep_t

            schedules.append(TrainSchedule(train_number=t_num, stops=stops_data))
            curr_dep_sec += headway_sec
            train_idx += 1

        return schedules

    def export_bve_sta_commands(self, schedule: TrainSchedule) -> str:
        """특정 열차 스케줄을 BVE 루트 파일에 바로 쓸 수 있는 .Sta 구문으로 변환"""
        lines = [f"; --- BVE Timetable for Train {schedule.train_number} ---"]
        for stop in schedule.stops:
            pos = stop["pos_m"]
            name = stop["station"]
            arr_str = format_sec_to_bve_time(stop["arr_sec"]) if stop["arr_sec"] is not None else ""
            dep_str = format_sec_to_bve_time(stop["dep_sec"]) if stop["dep_sec"] is not None else ""
            lines.append(f"{pos}, .Sta {name}; {arr_str}; {dep_str}; 0; 1; 0;")
        return "\n".join(lines)