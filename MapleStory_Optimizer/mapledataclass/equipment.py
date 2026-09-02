from dataclasses import dataclass

from mapledataclass.add_ability import AddAbility
from mapledataclass.base_stats import BaseStats
from mapledataclass.item import Item
from mapledataclass.potentials import Potentials
from mapledataclass.scroll import Scroll
from mapledataclass.starforce import Starforce


@dataclass
class Equipment(Item):
    """장비 아이템 데이터클래스
        Attributes:
            req_level: 요구레벨
            base_stats: 기본 스탯
            starforce_info: 스타포스
            potential: 잠재능력
            add_potential: 에디셔널 잠재능력
            add_ability: 추가옵션
            scroll: 주문서 강화값

    """
    #장비 기초 능력치
    req_level: int = 0
    base_stats: BaseStats = None

    starforce_info: Starforce = None
    potential: Potentials = None
    add_potential: Potentials = None
    add_ability: AddAbility = None
    scroll: Scroll = None

    # [Equipment 클래스 내부에 추가할 최종 깡스탯 합산 함수 수식]

    def get_final_flat_stats(self) -> BaseStats:
        pure_atk = (self.base_stats.atk if self.base_stats else 0) + \
                   (self.scroll.stats.atk if self.scroll and self.scroll.stats else 0)

        pure_magic = (self.base_stats.magic if self.base_stats else 0) + \
                     (self.scroll.stats.magic if self.scroll and self.scroll.stats else 0)

        if self.starforce_info:
            self.starforce_info.pure_scroll_atk = pure_atk
            self.starforce_info.pure_scroll_magic = pure_magic

        total = BaseStats()

        if self.base_stats:
            total += self.base_stats
        if self.add_ability:
            total += self.add_ability.stats
        if self.scroll:
            total += self.scroll.stats
        if self.starforce_info:
            total += self.starforce_info.get_bonus_stats()

        return total