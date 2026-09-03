# ============================================================
# Calculator
# ============================================================


class Calculator:

    # ========================================================
    # 효율
    # ========================================================

    @staticmethod
    def efficiency(character, stat_name):
        """
        캐릭터의 효율표에서 특정 스탯의
        1당 최종 데미지 상승량을 반환한다.

        예:
            INT 30 = 최종뎀 0.282

            → INT 1당
              0.282 / 30
        """

        table = character.efficiency_table

        if stat_name not in table:
            return 0.0

        data = table[stat_name]

        value = float(data.get("value", 0))
        final = float(data.get("final", 0))

        if value == 0:
            return 0.0

        return final / value

    # ========================================================
    # 옵션 하나의 최종뎀 계산
    # ========================================================

    @classmethod
    def option_damage(cls, option, character):
        """
        StatOption 하나가 만들어내는 최종뎀을 계산한다.

        예:
            INT +84
            → 84 × INT 효율

            올스탯 +4%
            → 4 × 올스탯% 효율
        """

        return (
            float(option.value)
            * cls.efficiency(
                character,
                option.stat
            )
        )

    # ========================================================
    # 옵션 목록의 최종뎀 계산
    # ========================================================

    @classmethod
    def options_damage(cls, options, character):
        """
        옵션 목록 전체의 최종뎀을 계산한다.
        """

        result = 0.0

        for option in options:
            result += cls.option_damage(
                option,
                character
            )

        return result

    # ========================================================
    # 최종뎀
    # ========================================================

    @classmethod
    def final_damage(cls, item, character):

        result = 0.0

        # ----------------------------------------------------
        # 추옵
        # ----------------------------------------------------

        result += cls.options_damage(
            item.flame_options,
            character
        )

        # ----------------------------------------------------
        # 작
        # ----------------------------------------------------

        result += cls.options_damage(
            item.scroll_options,
            character
        )

        # ----------------------------------------------------
        # 잠재
        # ----------------------------------------------------

        result += cls.options_damage(
            item.potential_options,
            character
        )

        # ----------------------------------------------------
        # 에디셔널 잠재
        # ----------------------------------------------------

        result += cls.options_damage(
            item.additional_potential_options,
            character
        )

        return result

    # ========================================================
    # 차이
    # ========================================================

    @classmethod
    def damage_difference(
        cls,
        item,
        base,
        character
    ):

        return (
            cls.final_damage(
                item,
                character
            )
            -
            cls.final_damage(
                base,
                character
            )
        )

    # ========================================================
    # 가격 차이
    # ========================================================

    @staticmethod
    def price_difference(item, base):

        return (
            item.actual_price
            -
            base.actual_price
        )

    # ========================================================
    # 가성비
    # ========================================================

    @classmethod
    def efficiency_score(
        cls,
        item,
        base,
        character
    ):

        damage_diff = cls.damage_difference(
            item,
            base,
            character
        )

        price_diff = cls.price_difference(
            item,
            base
        )

        # ----------------------------------------------------
        # 가격 동일
        # ----------------------------------------------------

        if price_diff == 0:

            if damage_diff > 0:
                return float("inf")

            return 0.0

        # ----------------------------------------------------
        # 더 비싼데 성능이 같거나 낮음
        # ----------------------------------------------------

        if price_diff > 0:

            if damage_diff <= 0:
                return 0.0

            return (
                damage_diff
                / price_diff
            )

        # ----------------------------------------------------
        # 더 싼 경우
        # ----------------------------------------------------

        if damage_diff >= 0:
            return float("inf")

        return (
            damage_diff
            / abs(price_diff)
        )

    # ========================================================
    # 정렬용 점수
    # ========================================================

    @classmethod
    def ranking_score(
        cls,
        item,
        base,
        character
    ):

        efficiency = cls.efficiency_score(
            item,
            base,
            character
        )

        if efficiency == float("inf"):
            return 999999999

        return efficiency