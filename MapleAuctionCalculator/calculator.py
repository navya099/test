# calculator.py


class Calculator:

    # ========================================================
    # 효율
    # ========================================================

    @staticmethod
    def efficiency(character, stat_name):
        table = character.efficiency_table

        if stat_name not in table:
            return 0.0

        data = table[stat_name]

        value = float(data["value"])
        final = float(data["final"])

        if value == 0:
            return 0.0

        return final / value

    # ========================================================
    # 최종뎀
    # ========================================================

    @classmethod
    def final_damage(cls, item, character):

        result = 0.0

        # ----------------------------------------------------
        # 추옵
        # ----------------------------------------------------

        result += (
            item.flame_int
            * cls.efficiency(character, "INT")
        )

        result += (
            item.flame_all
            * cls.efficiency(character, "올스탯%")
        )

        # ----------------------------------------------------
        # 작
        # ----------------------------------------------------

        result += (
            item.scroll_int
            * cls.efficiency(character, "INT")
        )

        result += (
            item.scroll_magic
            * cls.efficiency(character, "마력")
        )

        # ----------------------------------------------------
        # 잠재
        # ----------------------------------------------------

        result += (
            item.potential_int
            * cls.efficiency(character, "INT%")
        )

        # ----------------------------------------------------
        # 에디
        # ----------------------------------------------------

        result += (
            item.additional_int
            * cls.efficiency(character, "INT%")
        )

        result += (
            item.additional_magic
            * cls.efficiency(character, "마력")
        )

        return result

    # ========================================================
    # 차이
    # ========================================================

    @classmethod
    def damage_difference(cls, item, base, character):
        return (
            cls.final_damage(item, character)
            - cls.final_damage(base, character)
        )

    @staticmethod
    def price_difference(item, base):
        return (
            item.actual_price
            - base.actual_price
        )

    # ========================================================
    # 가성비
    # ========================================================

    @classmethod
    def efficiency_score(cls, item, base, character):

        damage_diff = cls.damage_difference(
            item,
            base,
            character
        )

        price_diff = cls.price_difference(
            item,
            base
        )

        # 가격 동일
        if price_diff == 0:

            if damage_diff > 0:
                return float("inf")

            return 0.0

        # 더 비싼데 성능이 같거나 낮음
        if price_diff > 0:

            if damage_diff <= 0:
                return 0.0

            return damage_diff / price_diff

        # 더 싼 경우
        if damage_diff >= 0:
            return float("inf")

        return damage_diff / abs(price_diff)

    # ========================================================
    # 정렬용 점수
    # ========================================================

    @classmethod
    def ranking_score(cls, item, base, character):

        efficiency = cls.efficiency_score(
            item,
            base,
            character
        )

        if efficiency == float("inf"):
            return 999999999

        return efficiency