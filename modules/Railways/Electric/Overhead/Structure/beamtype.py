from enum import Enum


class BeamType(Enum):
    """
    빔 타입 클래스
    Attributes:
        PIPE: 깅관빔
        H_BEAM: H형강빔
        TRUSS: 4각트러스
        TRUSS_RHAMEN: 4각트러스라멘
    """
    PIPE = 0
    H_BEAM = 1
    TRUSS = 2
    TRUSS_RHAMEN = 3

    @property
    def label(self) -> str:
        return {
            BeamType.PIPE: "깅관빔",
            BeamType.H_BEAM: "H형강빔",
            BeamType.TRUSS: "트러스빔",
            BeamType.TRUSS_RHAMEN: "트러스라멘빔",
        }[self]