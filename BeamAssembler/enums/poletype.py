from enum import Enum


class PoleType(Enum):
    """
    전주타입 클래스
    Attributes:
        PIPE: 강관주
        H_BEAM: H형강주
        STEEL: 조립철주
    """
    PIPE = '강관주'
    H_BEAM = 'H형강주'
    STEEL = '조립철주'