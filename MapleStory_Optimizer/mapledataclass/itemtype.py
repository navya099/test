from enum import Enum


class ItemType(Enum):
    """아이템 타입 열거형
        Attributes:
            EQUIPMENT: 장비
            POS: 소비 (Potion / Possession 등)
            ETC: 기타
    """
    EQUIPMENT = 'Equipment'
    POS = 'Potion'
    ETC = 'Etc'
