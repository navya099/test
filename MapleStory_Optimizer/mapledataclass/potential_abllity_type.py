from enum import Enum, auto


class PotentialAbilityType(Enum):
    """잠재능력 종류
    Attributes:

        STR:  힘
        DEX: 덱스
        INT: 인트
        LUK: 럭
        ALL_STAT : 올스탯
        ATK: 공격력
        MAGIC: 마력
        BOSSATK: 보스 공격력 데미지
        IGNORE_DEF : 방어율 무시
        DMG: 데미지
        CRITICAL_DMG: 크리티컬 데미지
        COOL_DOWN_REDUCTION : 재사용 대기시간 감소
        MESO_DROP : 메소 획득량
        ITEM_DROP : 메소 획득량

        NULL: NONE
    """
    STR = auto()
    DEX = auto()
    INT = auto()
    LUK = auto()
    ALL_STAT = auto()

    ATK = auto()
    MAGIC = auto()
    BOSSATK = auto()
    IGNORE_DEF = auto()
    DMG = auto()
    CRITICAL_DMG = auto()

    COOL_DOWN_REDUCTION = auto()
    MESO_DROP = auto()
    ITEM_DROP = auto()

    NULL = -1

