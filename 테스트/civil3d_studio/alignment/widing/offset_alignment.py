# ==============================================================================
# 2. Civil 3D 스타일 Offset Alignment (간격띄우기 선형) 엔진
# ==============================================================================
from typing import Optional, Tuple, List

from alignment.widing.wideing_region import WideningRegion
from alignment.alignment import Alignment

class OffsetAlignment:
    """
    상위 모선형(Parent HorizontalAlignment)에 동적 연동되는 Civil 3D Offset Alignment 엔진
    - 기본 이격 거리(nominal_offset) 유지 + 다중 확폭 구간(WideningRegion) 자동 합성
    - 임의 측점에서의 오프셋 좌표(E, N), 실시간 폭원(W), 테이퍼 접선 방위각 산출
    - 외부 좌표(E, N)로부터 모선형 기준 측점 및 오프셋 선형으로부터의 이격 거리 역산
    """
    def __init__(
        self,
        name: str,
        parent_alignment: Alignment,
        nominal_offset: float,
        start_station: Optional[float] = None,
        end_station: Optional[float] = None
    ):
        """
        :param name: 간격띄우기 선형 이름 (예: "우측_차선외측_ETW")
        :param parent_alignment: 기준이 되는 상위 Alignment 객체
        :param nominal_offset: 기본 이격 거리 (우측: 양수 +, 좌측: 음수 -)
        :param start_station: 오프셋 선형 시작 측점 (생략 시 모선형 시점과 동일)
        :param end_station: 오프셋 선형 종료 측점 (생략 시 모선형 종점과 동일)
        """
        self.name = name

        self.parent = parent_alignment
        self.nominal_offset = float(nominal_offset)
        self.side_sign = 1.0 if self.nominal_offset >= 0 else -1.0

        self.start_station = float(start_station) if start_station is not None else self.parent.starting_station
        self.end_station = float(end_station) if end_station is not None else self.parent.ending_station
        self.widenings: List[WideningRegion] = []

    def add_widening(self, region: WideningRegion):
        """확폭 구간(버스베이, 가감속차선, 교차로 좌회전 차선 등) 추가 및 유효성 검증"""
        if region.end_station - region.start_station < (region.entry_transition_len + region.exit_transition_len) - 1e-6:
            raise ValueError(
                f"[{region.name}] 전체 확폭 구간 길이({region.end_station - region.start_station:.2f}m)보다 "
                f"진입·진출 테이퍼 길이 합({region.entry_transition_len + region.exit_transition_len:.2f}m)이 큽니다."
            )
        self.widenings.append(region)
        self.widenings.sort(key=lambda w: w.start_station)
        return self

    @staticmethod
    def _transition_factor(t: float, mode: str) -> Tuple[float, float]:
        """
        전환 비율 t (0~1)에 대한 (폭원 보간 계수 f(t), 도함수 f'(t)) 반환
        """
        t = max(0.0, min(1.0, t))
        if mode == "Linear":
            return t, 1.0
        # "Smooth": Civil 3D Curve-Curve / Reverse Curve 스타일의 3차 에르미트 S자 보간
        return (3.0 * t * t - 2.0 * t * t * t), (6.0 * t * (1.0 - t))

    def get_offset_at(self, station: float) -> Tuple[float, float]:
        """
        지정 측점(station)에서의 (실제 이격 거리 W(s), 폭원 변화율 dW/ds) 반환
        """
        if station < self.start_station - 1e-9 or station > self.end_station + 1e-9:
            raise ValueError(f"측점({station})이 Offset Alignment 범위({self.start_station} ~ {self.end_station})를 벗어났습니다.")

        total_w = self.nominal_offset
        dw_ds = 0.0

        for w in self.widenings:
            if w.start_station <= station <= w.end_station:
                s_full_start = w.start_station + w.entry_transition_len
                s_full_end = w.end_station - w.exit_transition_len

                if station < s_full_start and w.entry_transition_len > 1e-9:
                    # 1. 진입 테이퍼 구간 (확폭 증가)
                    t = (station - w.start_station) / w.entry_transition_len
                    f_val, df_dt = self._transition_factor(t, w.transition_type)
                    total_w += self.side_sign * w.widening_width * f_val
                    dw_ds += self.side_sign * w.widening_width * (df_dt / w.entry_transition_len)
                elif station > s_full_end and w.exit_transition_len > 1e-9:
                    # 2. 복귀 테이퍼 구간 (확폭 감소)
                    t = (w.end_station - station) / w.exit_transition_len
                    f_val, df_dt = self._transition_factor(t, w.transition_type)
                    total_w += self.side_sign * w.widening_width * f_val
                    dw_ds -= self.side_sign * w.widening_width * (df_dt / w.exit_transition_len)
                else:
                    # 3. 최대 확폭 유지 구간
                    total_w += self.side_sign * w.widening_width
                    dw_ds += 0.0

        return total_w, dw_ds

    def point_location(self, parent_station: float, additional_offset: float = 0.0) -> Tuple[float, float]:
        """
        모선형 측점(parent_station)과 이 오프셋 선형 기준 추가 이격거리(additional_offset)로
        글로벌 좌표 (Easting, Northing) 반환
        """
        curr_offset, _ = self.get_offset_at(parent_station)
        return self.parent.point_location(parent_station, curr_offset + additional_offset)

    def sample_polyline(self, interval: float = 5.0) -> List[Tuple[float, float, float, float]]:
        """
        도면 작도 및 3D 코리더 연동을 위한 오프셋 선형 정점 테이블 추출
        - 테이퍼 시·종점(임계 측점)을 자동으로 포함하여 꺾임이나 곡선 왜곡 방지
        :return: [(Parent_Station, Offset_Width, Easting, Northing), ...]
        """
        # 기본 간격 측점 + 확폭 테이퍼 주요 변화점 측점 병합
        sta_set = {self.start_station, self.end_station}
        curr = self.start_station
        while curr < self.end_station - 1e-6:
            sta_set.add(round(curr, 6))
            curr += interval

        for w in self.widenings:
            for key_sta in [
                w.start_station,
                w.start_station + w.entry_transition_len,
                w.end_station - w.exit_transition_len,
                w.end_station
            ]:
                if self.start_station <= key_sta <= self.end_station:
                    sta_set.add(round(key_sta, 6))

        sorted_stations = sorted(sta_set)
        result = []
        for sta in sorted_stations:
            w_val, _ = self.get_offset_at(sta)
            e, n = self.parent.point_location(sta, w_val)
            result.append((sta, w_val, e, n))

        return result