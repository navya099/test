# ==============================================================================
# 2. Civil 3D 스타일 측점 방정식 관리자 (StationEquationManager)
# ==============================================================================
from typing import List, Tuple, Optional

from alignment.station.station_equation import StationEquation


class StationEquationManager:
    """
    선형의 물리적 거리(Raw Station)와 파정이 반영된 표기 측점(Display Station) 간의
    양방향 정밀 변환 및 구간(Region) 관리를 수행하는 Civil 3D 호환 엔진
    """
    def __init__(self, start_station: float = 0.0, total_physical_length: float = 1000.0):
        self.start_station = float(start_station)
        self.total_length = float(total_physical_length)
        self.equations: List[StationEquation] = []
        self.regions = []
        self._rebuild_regions()

    def add_equation_by_raw(self, raw_station: float, station_ahead: float):
        """
        물리적 거리(raw_station) 위치에 새 전방 측점(station_ahead)을 지정하여 파정 추가
        (후방 측점 station_back은 이전 구간의 누적 체계에서 자동 계산됨)
        """
        if raw_station <= 0.0 or raw_station >= self.total_length:
            raise ValueError(f"방정식 위치({raw_station})는 선형 내부(0 ~ {self.total_length})에 있어야 합니다.")

        # 해당 물리적 거리에서의 기존 후방 측점(station_back) 자동 산출
        station_back, _ = self.raw_to_display(raw_station)
        self.equations.append(StationEquation(float(raw_station), station_back, float(station_ahead)))
        self.equations.sort(key=lambda eq: eq.raw_station)
        self._rebuild_regions()
        return self

    def add_equation_by_back(self, station_back: float, station_ahead: float, region_index: Optional[int] = None):
        """
        Civil 3D UI 방식: 후방 측점(Station Back)과 전방 측점(Station Ahead)을 직접 입력해 파정 추가
        """
        matches = self.display_to_raw_all(station_back)
        if not matches:
            raise ValueError(f"후방 측점({station_back})이 현재 선형 측점 범위 내에 존재하지 않습니다.")

        if region_index is not None:
            raw_sta = next((r for r, idx in matches if idx == region_index), None)
            if raw_sta is None:
                raise ValueError(f"지정한 구간({region_index})에 측점({station_back})이 없습니다.")
        else:
            # 기본적으로 가장 마지막(최신) 구간을 기준으로 물리적 거리 역산
            raw_sta = matches[-1][0]

        self.equations.append(StationEquation(raw_sta, float(station_back), float(station_ahead)))
        self.equations.sort(key=lambda eq: eq.raw_station)
        self._rebuild_regions()
        return self

    def _rebuild_regions(self):
        """방정식 기준으로 선형을 연속된 측점 구간(Region 0, 1, 2...)으로 분할 캐싱"""
        self.regions = []
        curr_raw = 0.0
        curr_disp_start = self.start_station

        for idx, eq in enumerate(self.equations):
            span = eq.raw_station - curr_raw
            if span <= 1e-9:
                raise ValueError(f"중복되거나 역전된 물리적 위치({eq.raw_station})에 방정식을 추가할 수 없습니다.")
            self.regions.append({
                "region_idx": idx,
                "raw_start": curr_raw,
                "raw_end": eq.raw_station,
                "disp_start": curr_disp_start,
                "disp_end": curr_disp_start + span,
                "offset": curr_disp_start - curr_raw  # Display = Raw + offset
            })
            curr_raw = eq.raw_station
            curr_disp_start = eq.station_ahead

        # 마지막 방정식 이후부터 종점까지의 최종 구간
        final_span = self.total_length - curr_raw
        self.regions.append({
            "region_idx": len(self.equations),
            "raw_start": curr_raw,
            "raw_end": self.total_length,
            "disp_start": curr_disp_start,
            "disp_end": curr_disp_start + final_span,
            "offset": curr_disp_start - curr_raw
        })

    def raw_to_display(self, raw_station: float) -> Tuple[float, int]:
        """
        순수 물리적 거리(Raw Station) -> (표기 측점 Display Station, 구간 인덱스 Region Index)
        """
        if raw_station < -1e-9 or raw_station > self.total_length + 1e-9:
            raise ValueError(f"물리적 거리({raw_station})가 선형 범위(0 ~ {self.total_length})를 벗어났습니다.")

        for reg in self.regions:
            if reg["raw_start"] - 1e-9 <= raw_station <= reg["raw_end"] + 1e-9:
                # 경계점일 경우 마지막 구간이 아니면 이전 구간의 후방 측점 반환
                if abs(raw_station - reg["raw_end"]) < 1e-9 and reg["region_idx"] < len(self.regions) - 1:
                    return reg["disp_end"], reg["region_idx"]
                return raw_station + reg["offset"], reg["region_idx"]

        last = self.regions[-1]
        return raw_station + last["offset"], last["region_idx"]

    def display_to_raw_all(self, display_station: float) -> List[Tuple[float, int]]:
        """
        표기 측점(Display Station) -> 일치하는 모든 (물리적 거리 Raw Station, 구간 인덱스) 리스트 반환
        - 중복 파정(Overlap) 구간에서는 2개 이상의 해가 반환됨
        - 결측 파정(Gap) 구간에서는 빈 리스트([])가 반환됨
        """
        results = []
        for reg in self.regions:
            if reg["disp_start"] - 1e-9 <= display_station <= reg["disp_end"] + 1e-9:
                raw_val = display_station - reg["offset"]
                raw_val = max(reg["raw_start"], min(reg["raw_end"], raw_val))
                results.append((raw_val, reg["region_idx"]))
        return results

    def display_to_raw(self, display_station: float, region_index: Optional[int] = None) -> float:
        """
        표기 측점(Display Station) -> 단일 물리적 거리(Raw Station) 반환
        (중복 구간에서 region_index를 생략하면 첫 번째 매칭 구간을 반환, 결측 구간이면 예외 발생)
        """
        matches = self.display_to_raw_all(display_station)
        if not matches:
            raise ValueError(f"측점({self.format_station(display_station)})은 파정으로 인해 건너뛴 결측 구간(Gap)이거나 범위 밖입니다.")

        if region_index is not None:
            for raw_val, r_idx in matches:
                if r_idx == region_index:
                    return raw_val
            raise ValueError(f"지정한 구간(Region {region_index})에 측점({display_station})이 존재하지 않습니다.")

        return matches[0][0]

    @staticmethod
    def format_station(sta: float, chainage_unit: float = 1000.0) -> str:
        """토목 표준 측점 문자열 변환 (예: 1250.5 -> '1+250.500')"""
        sign = "-" if sta < 0 else ""
        abs_sta = abs(sta)
        major = int(abs_sta // chainage_unit)
        minor = abs_sta % chainage_unit
        return f"{sign}{major}+{minor:07.3f}"

    def print_summary(self):
        """Civil 3D Station Equations 테이블 및 구간별 유효 측점 범위 요약 출력"""
        print("\n==================== [Civil 3D Station Equations 요약] ====================")
        if not self.equations:
            print("등록된 측점 방정식(파정)이 없습니다.")
        else:
            print(f"{'No.':<4} | {'물리위치(Raw)':<14} | {'후방측점(Back)':<15} | {'전방측점(Ahead)':<15} | {'보정량(Shift)':<13} | {'유형'}")
            print("-" * 82)
            for i, eq in enumerate(self.equations, 1):
                kind = "결측(Gap/단축)" if eq.shift > 0 else ("중복(Overlap/연장)" if eq.shift < 0 else "변화없음")
                print(
                    f"{i:<4} | {eq.raw_station:<14.3f} | {self.format_station(eq.station_back):<15} | "
                    f"{self.format_station(eq.station_ahead):<15} | {eq.shift:+13.3f} | {kind}"
                )

        print("\n[구간별 유효 측점 매핑 테이블]")
        print(f"{'Region':<8} | {'물리적 거리 (Raw)':<22} | {'표기 측점 범위 (Display Station)'}")
        print("-" * 68)
        for r in self.regions:
            raw_rng = f"{r['raw_start']:.2f} ~ {r['raw_end']:.2f} m"
            disp_rng = f"{self.format_station(r['disp_start'])} ~ {self.format_station(r['disp_end'])}"
            print(f"Zone {r['region_idx']:<3} | {raw_rng:<22} | {disp_rng}")
        print("=" * 82)
