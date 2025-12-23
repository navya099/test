from dataclasses import dataclass


@dataclass
class Feederdata:
    """급전선데이터
    Attributes:
        type: 급전선 지지물 종류
        index: 급전선 지지물 인덱스
        xoffset: 선로중심 기준 x 오프셋
        yoffset: 선로중심 기준 y 오프셋
        """
    type: str = ''
    index: int = 0
    xoffset: float = 0.0
    yoffset: float = 0.0