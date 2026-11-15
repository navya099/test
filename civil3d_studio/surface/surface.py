# ==============================================================================
# 4. 현지지반(EG) 지형 엔진 및 절토·성토(Daylight) 자동 탐색 모듈
# ==============================================================================
import math
from typing import Tuple


class ExistingGroundTerrain:
    """
    현지지반(Existing Ground) 표고 모델 및 측점별 횡단 지형 프로파일 제공기
    - 실제 측량 TIN/DEM 격자 데이터를 바인딩하거나, 설계 검증용 3D 기복 지형을 생성
    """
    def __init__(self, base_profile_func=None):
        self.base_profile_func = base_profile_func

    def elevation_at(self, easting: float, northing: float, station: float = 0.0, offset: float = 0.0) -> float:
        """글로벌 좌표 (E, N) 또는 (Station, Offset)에서의 현지지반고(EG EL) 반환"""
        base_el = self.base_profile_func(station) if self.base_profile_func else 42.0
        # 자연 지형 기복(종방향 능선/계곡 + 횡방향 산지 경사) 시뮬레이션
        long_wave = -2.8 * math.sin(station * 0.0085) + 1.6 * math.cos(station * 0.019)
        trans_slope = 0.08 * offset + 0.6 * math.sin(offset * 0.15 + station * 0.01)
        return base_el + long_wave + trans_slope

    def find_daylight_intersection(
        self,
        station: float,
        hinge_offset: float,
        hinge_el: float,
        side_sign: float,
        cut_slope_ratio: float = 1.0,    # 절토 비탈면 경사 (1 : 1.0 = 100%)
        fill_slope_ratio: float = 1.5,   # 성토 비탈면 경사 (1 : 1.5 = 66.7%)
        max_search_width: float = 40.0,
        step: float = 0.25
    ) -> Tuple[str, float, float]:
        """
        노견 끝(Hinge)에서 출발하여 현지지반(EG)과 만나는 절토/성토 경계점(Daylight) 자동 탐색
        :return: (상태 "CUT"|"FILL", 최종 Daylight Offset, 최종 Daylight EL)
        """
        eg_at_hinge = self.elevation_at(0.0, 0.0, station, hinge_offset)
        is_cut = hinge_el < eg_at_hinge  # 계획고가 지반고보다 낮으면 절토(Cut), 높으면 성토(Fill)
        mode = "CUT" if is_cut else "FILL"
        slope = (1.0 / cut_slope_ratio) if is_cut else (-1.0 / fill_slope_ratio)

        prev_w = 0.0
        prev_diff = hinge_el - eg_at_hinge

        # ★ 개선: 시작점에서 이미 지반과 교차(hinge가 지반보다 위)하면 즉시 반환
        if abs(prev_diff) < 1e-9:
            return mode, hinge_offset, hinge_el

        w = step
        while w <= max_search_width:
            curr_off = hinge_offset + side_sign * w
            curr_design_el = hinge_el + w * slope
            curr_eg_el = self.elevation_at(0.0, 0.0, station, curr_off)
            curr_diff = curr_design_el - curr_eg_el

            # 부호가 바뀌는 순간(지반선 관통) 선형 보간으로 정밀 교점(Daylight) 산출
            if prev_diff * curr_diff <= 0.0:
                denom = abs(prev_diff) + abs(curr_diff)
                t = abs(prev_diff) / denom if denom > 1e-9 else 0.0
                exact_w = prev_w + t * step
                exact_off = hinge_offset + side_sign * exact_w
                exact_el = hinge_el + exact_w * slope
                return mode, exact_off, exact_el

            prev_w = w
            prev_diff = curr_diff
            w += step

        # ★ 개선: 탐색 실패 시 mode를 "CUT"|"FILL"로 유지하되 max_off 반환 (기존과 동일)
        max_off = hinge_offset + side_sign * max_search_width
        return mode, max_off, hinge_el + max_search_width * slope