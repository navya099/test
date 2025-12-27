from dataclasses import dataclass, field

@dataclass
class RailData:
    """레일데이터
    Attributes:
        name:선로명
        index:선로인덱스
        brackets:브래킷들
    """
    name: str = ''
    index: int = 0
    brackets: list = field(default_factory=list)
