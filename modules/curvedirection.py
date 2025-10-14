from enum import Enum

class CurveDirection(Enum):
    """
    곡선 방향 클래스.

    Attributes:
        LEFT (int): 좌향
        RIGHT (int): 우향
        NULL(int): 잘못된 값
    """
    LEFT = 0
    RIGHT = 1
    NULL = 2