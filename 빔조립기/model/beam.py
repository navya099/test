from dataclasses import dataclass

from Electric.Overhead.Structure.beamtype import BeamType


@dataclass
class Beam:
    """빔 구성요소
    Attributes:
        type: 빔 종류
        length: 빔 길이
        index: 빔 오브젝트 인덱스
        """
    name: str
    type: BeamType
    length: float
    index: int