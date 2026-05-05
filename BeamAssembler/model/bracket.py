from dataclasses import dataclass


@dataclass
class Bracket:

    """브래킷 데이터
    Attributes:
        rail_no:선로번호
        type:브래킷 이름
        xoffset:X
        yoffset:Y
        rotation:회전
        index: 오브젝트 인덱스
    """
    rail_no: int
    type: str
    xoffset: float
    yoffset: float
    rotation: float
    index: int
    rail_type: str
    fittings: list