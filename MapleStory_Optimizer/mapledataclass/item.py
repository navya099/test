from abc import ABC
from dataclasses import dataclass

from mapledataclass.itemtype import ItemType


@dataclass # 👈 부모 추상 클래스에도 dataclass를 명시하여 상속 구조 안정화
class Item(ABC):
    """추상 아이템 클래스
    Attributes:
        type: 아이템 분류 (예: "장비", "소비", "기타")
        name: 아이템 이름 (예: "앱솔랩스 나이트글러브")
    """
    type: ItemType = ItemType.ETC
    name: str = ''
