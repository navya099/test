from enum import Enum

class StructureType(Enum):
    """
    구조물 타입 정의 구조체
    Attributes:
        Earth: 토공
        Bridge: 교량
        Tunnel: 터널
        NONE: 미정의
    """
    Earth = 0
    Bridge = 1
    Tunnel = 2
    NONE = 3