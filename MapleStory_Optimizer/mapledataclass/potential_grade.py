from enum import Enum


class PotentialGrade(Enum):
    """잠재능력 등급
    Attributes:
        RARE: 레어
        EPIC: 에픽
        UNIQUE: 유니크
        LEGENDARY: 레전드리
        NULL: 널

    """
    RARE = 0
    EPIC = 1
    UNIQUE = 2
    LEGENDARY = 3
    NULL = 4
