# ==============================================================================
# 1. 측점 방정식(Station Equation) 정의 데이터 구조체
# ==============================================================================
from dataclasses import dataclass


@dataclass
class StationEquation:
    """
    Civil 3D StationEquation 객체 대응 구조체
    - raw_station: 선형 시점(0.0) 기준 순수 물리적 누적 거리 (m)
    - station_back: 방정식 적용 지점의 후방 측점 (기존 체계 끝값)
    - station_ahead: 방정식 적용 지점의 전방 측점 (새 체계 시작값)
    """
    raw_station: float
    station_back: float
    station_ahead: float

    @property
    def shift(self) -> float:
        """측점 이동량 (양수: 결측/건너뜀, 음수: 중복/겹침)"""
        return self.station_ahead - self.station_back
