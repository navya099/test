from dataclasses import dataclass
from mapledataclass.base_stats import BaseStats


@dataclass
class Scroll:
    """장비 주문서 및 주문식 흔적 강화 클래스
    Attributes:
        stats: 주문서 강화로 상승한 총 누적 스탯 묶음
        upgrade_count: 현재 적용된 주문서 강화 횟수 (예: 8작이면 8)
    """
    stats: BaseStats = None
    upgrade_count: int = 0
