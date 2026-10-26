from enum import Enum

class CurveType(Enum):
    """
    곡선 종류 클래스.

    Attributes:
        Simple (int): 원곡선
        Spiral (int): 완화곡선
        Compound (int): 복심곡선
        Reverse(int): 반향곡선
        NONE(int): 정의되지 않음
    """
    Simple = 0
    Spiral = 1
    Compound = 2
    Reverse = 3
    NONE = 99