from dataclasses import dataclass

from model.tkraildata import TKRailData


@dataclass
class EquipmentDTO:
    """장비데이터
    Attributes:
        name: 장비명
        objindex: 오브젝트인덱스
        xoffset: 선로중심 기준 x 오프셋
        yoffset: 선로중심 기준 y 오프셋
        rotation: 회전
        base_rail_index: 설치레일 인덱스
        base_rail: 레일 객체
        """
    name: str = ''
    objindex: int = None
    xoffset: float = 0.0
    yoffset: float = 0.0
    rotation: float = 0.0
    base_rail_index: int = 0
    base_rail: TKRailData | None = None

