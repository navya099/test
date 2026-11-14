from typing import List, Tuple

from superelevation.superelevation import SuperelevationStation


class SuperelevationTable:
    """측점별 좌/우 편경사를 선형 보간하여 반환하는 편경사 관리자"""

    def __init__(self, critical_stations: List[SuperelevationStation], default_crown: float = -0.02):
        self.stations = sorted(critical_stations, key=lambda s: s.station)
        self.default_crown = float(default_crown)

    def get_slopes_at(self, station: float) -> Tuple[float, float]:
        """지정 측점에서의 (좌측 경사, 우측 경사) 소수값 반환"""
        if not self.stations:
            return self.default_crown, self.default_crown

        # 수정: self.stations.station -> self.stations[0].station
        if station <= self.stations[0].station:
            return self.stations[0].left_slope, self.stations[0].right_slope

        if station >= self.stations[-1].station:
            return self.stations[-1].left_slope, self.stations[-1].right_slope

        for i in range(len(self.stations) - 1):
            s1, s2 = self.stations[i], self.stations[i + 1]
            if s1.station <= station <= s2.station:
                span = s2.station - s1.station
                if span <= 1e-9:
                    return s2.left_slope, s2.right_slope
                t = (station - s1.station) / span
                l_slope = s1.left_slope + t * (s2.left_slope - s1.left_slope)
                r_slope = s1.right_slope + t * (s2.right_slope - s1.right_slope)
                return l_slope, r_slope

        return self.default_crown, self.default_crown