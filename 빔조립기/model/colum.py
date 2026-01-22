from dataclasses import dataclass

from Electric.Overhead.Pole.poletype import PoleType


@dataclass
class Column:
    """전주 기둥
        Attributes:
            type: 기둥 종류
            width: 기둥 폭
            xoffset: x위치
            yoffset: y위치
            index: 기둥 오브젝트 인덱스
            """
    name: str
    type: PoleType
    width: float
    xoffset: float
    yoffset: float
    height: float
    index: int