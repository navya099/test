from dataclasses import dataclass


@dataclass
class SuperelevationStation:
    """편경사 임계 측점 (Critical Station) 정의"""
    station: float
    left_slope: float   # 좌측 차선 횡단경사 (예: -0.02 = -2.0%, 바깥쪽 내리막)
    right_slope: float  # 우측 차선 횡단경사 (예: -0.02 = -2.0%, 바깥쪽 내리막)