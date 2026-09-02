from dataclasses import dataclass


@dataclass
class BaseStats:
    """장비의 순수 기초 능력치 (노작 스탯)
    Attributes:
        str_val: 힘 스탯
        int_val: 인트 스탯
        dex_val: 덱스 스탯
        luk_val: 럭 스탯
        atk: 공격력
        magic: 마력
        allstat: 올스탯 (%)
        boss_atk: 보스 공격력 데미지
        ignore_def: 몬스터 방어율 무시 (%)
        max_hp: 최대 HP
        max_mp: 최대 MP
        base_def: 방어력
        dmg: 데미지
    """
    # 파이썬 예약어(str, int)와의 충돌을 피하기 위해 _val 접미사 사용
    str_val: int = 0
    int_val: int = 0
    dex_val: int = 0
    luk_val: int = 0
    atk: int = 0
    magic: int = 0
    allstat: int = 0
    boss_atk: int = 0
    ignore_def: int = 0
    max_hp: int = 0
    max_mp: int = 0
    base_def: int = 0
    dmg: int = 0

    def __add__(self, other):
        """BaseStats 객체끼리 '+' 연산자로 즉시 더할 수 있게 만드는 마법의 함수"""
        if not other:
            return self
        return BaseStats(
            str_val=self.str_val + other.str_val,
            dex_val=self.dex_val + other.dex_val,
            atk=self.atk + other.atk,
            # ... 다른 스탯들도 동일하게 더하기 ...
        )