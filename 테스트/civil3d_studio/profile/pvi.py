# ==============================================================================
# 1. Civil 3D 스타일 종단 교점(PVI) 데이터 구조체
# ==============================================================================
from dataclasses import dataclass
from typing import Optional


@dataclass
class PVIPoint:
    """
    Civil 3D Layout Profile용 종단 교점(PVI) 제원
    - 시점(BVP)과 종점(EVP)은 L1=0, L2=0으로 입력
    - 중간 PVI는 대칭 종단곡선 길이 L을 입력하거나, 비대칭 시 L1, L2를 각각 입력
    """
    name: str
    station: float
    elevation: float
    L: Optional[float] = None       # 대칭 종단곡선 총 길이 (m)
    L1: Optional[float] = None      # 비대칭 진입 종단곡선 길이 (m)
    L2: Optional[float] = None      # 비대칭 진출 종단곡선 길이 (m)