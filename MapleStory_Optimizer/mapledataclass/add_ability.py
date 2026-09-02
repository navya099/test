from dataclasses import dataclass
from mapledataclass.base_stats import BaseStats


@dataclass
class AddAbility:
    """장비 추가옵션 클래스
    Attributes:
        stats: 추가옵션으로 상승하는 스탯 묶음 (str, dex, 공, 마 등)
    """
    stats: BaseStats = None
