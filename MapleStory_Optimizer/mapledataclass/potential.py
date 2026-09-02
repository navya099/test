from dataclasses import dataclass

from mapledataclass.potential_abllity_type import PotentialAbilityType
from mapledataclass.potential_grade import PotentialGrade

@dataclass
class Potential:
    """잠재능력 객체
    grade: 등급(레어, 에픽, 유니크, 레전더리)
    ability: 능력치 옵션
    value: 값
    """
    grade: PotentialGrade = PotentialGrade.NULL
    ability: PotentialAbilityType = PotentialAbilityType.NULL
    value: int = 0