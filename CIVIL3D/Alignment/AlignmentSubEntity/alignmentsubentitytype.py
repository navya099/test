from enum import Enum


class AlignmentSubEntityType(Enum):
    """
    하위 엔터티 유형(예: 선, 호, 나선형 등)을 지정합니다.
    """
    Line = 0
    Arc = 1
    Spiral = 2