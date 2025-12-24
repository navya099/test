from enum import Enum


class PoleType(Enum):
    """
    전주타입 클래스
    Attributes:
        PIPE: 강관주
        H_BEAM: H형강주
        STEEL: 조립철주
    """
    PIPE = 0
    H_BEAM = 1
    STEEL = 2

    @property
    def label(self) -> str:
        return {
            PoleType.PIPE: "강관주",
            PoleType.H_BEAM: "H형강주",
            PoleType.STEEL: "조립철주",
        }[self]