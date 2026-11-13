# ==============================================================================
# 1. 실무 입력용 PI(교점) 데이터 구조체
# ==============================================================================
from dataclasses import dataclass
from typing import Optional


@dataclass
class PIPoint:
    """
    실무 선형 설계용 교점(PI) 및 곡선 제원 정의
    - BP(시점) 및 EP(종점)는 R=0, L=0, A=0으로 입력
    - 중간 PI점은 R과 함께 (L 또는 A 중 하나)를 입력하면 나머지는 자동 계산됨
    """
    name: str
    easting: float
    northing: float
    R: float = 0.0                  # 원곡선 반경 (m)
    L: Optional[float] = None       # 진입/진출 완화곡선 길이 (m) - L1, L2 동일 기준
    A: Optional[float] = None       # 완화곡선 계수 A (m) -> 입력 시 L = A^2 / R 자동 계산
    spiral_type: str = "JapaneseCubic"  # "JapaneseCubic" 또는 "Clothoid"