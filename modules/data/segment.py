from dataclasses import dataclass, field

from AutoCAD.point2d import Point2d
from curvetype import CurveType

@dataclass
class Segment:
    """
    공통 세그멘트 객체
    Attributes:
        prev_index(int): 이전 세그먼트 인덱스
        current_index(int): 현재 세그먼트 인덱스
        next_index(int): 다음 세그먼트 인덱스
        start_sta (float): 시작 측점
        end_sta (float): 끝 측점
        type(CurveType): 세그먼트 타입(직선 ,곡선 ,완화곡선)
    """
    prev_index: int = 0
    current_index: int = 0
    next_index: int = 0
    start_sta: float = 0.0
    end_sta: float = 0.0
    type: CurveType = CurveType.NONE




