from dataclasses import dataclass

from maple_util.math_util import maple_round
from mapledataclass.base_stats import BaseStats


@dataclass
class Starforce:
    star: int
    req_level: int

    # Equipment에서 주입됨
    pure_scroll_atk: int = 0
    pure_scroll_magic: int = 0

    def get_bonus_stats(self) -> BaseStats:
        """스타포스 최종 스탯 반환 (실제 메이플 공식)"""

        bonus = BaseStats()

        # -------------------------
        # ✅ 무기 공격력 / 마력 계산
        # -------------------------
        atk_gain = self._calc_weapon_atk(self.pure_scroll_atk)
        magic_gain = self._calc_weapon_atk(self.pure_scroll_magic)

        bonus.atk += atk_gain
        bonus.magic += magic_gain

        return bonus

    # =========================
    # 🔥 핵심: 누적 성장 계산
    # =========================
    def _calc_weapon_atk(self, base_value: int) -> int:
        if base_value <= 0:
            return 0

        current = base_value
        total_gain = 0

        # ✅ 1~15성
        for s in range(1, min(self.star, 15) + 1):
            gain = maple_round(current / 50) + 1
            current += gain
            total_gain += gain

        # ✅ 16~22성
        if self.star >= 16:
            total_gain += self._get_16_22_gain()

        return total_gain

    def _get_16_22_gain(self) -> int:
        table_200 = {
            16: 16,
            17: 17,
            18: 18,
            19: 19,
            20: 20,
            21: 22,
            22: 24,
        }

        gain = 0
        for s in range(16, min(self.star, 22) + 1):
            gain += table_200.get(s, 0)

        return gain