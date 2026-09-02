# models.py

import copy
from config import (
    DEFAULT_EQUIPMENT_NAMES,
    create_default_efficiency_table,
)


# ============================================================
# Item
# ============================================================

class Item:
    def __init__(
        self,
        name="",
        price=0.0,
        flame_int=0.0,
        flame_all=0.0,
        scroll_int=0.0,
        scroll_magic=0.0,
        potential_int=0.0,
        additional_int=0.0,
        additional_magic=0.0,
        used_count=0,
        max_count=10,
        tax=False,
    ):
        self.name = name
        self.price = float(price)

        self.flame_int = float(flame_int)
        self.flame_all = float(flame_all)

        self.scroll_int = float(scroll_int)
        self.scroll_magic = float(scroll_magic)

        self.potential_int = float(potential_int)

        self.additional_int = float(additional_int)
        self.additional_magic = float(additional_magic)

        self.used_count = int(used_count)
        self.max_count = int(max_count)

        self.tax = bool(tax)

    # --------------------------------------------------------
    # 계산용 속성
    # --------------------------------------------------------

    @property
    def remaining_count(self):
        return self.max_count - self.used_count

    @property
    def actual_price(self):
        """
        관세가 체크되어 있으면 10% 추가.
        """
        if self.tax:
            return self.price * 1.10

        return self.price

    # --------------------------------------------------------
    # 표시용
    # --------------------------------------------------------

    def flame_text(self):
        parts = []

        if self.flame_int:
            parts.append(f"INT {self.flame_int:g}")

        if self.flame_all:
            parts.append(f"올스탯 {self.flame_all:g}%")

        return " / ".join(parts) if parts else "-"

    def scroll_text(self):
        parts = []

        if self.scroll_int:
            parts.append(f"INT +{self.scroll_int:g}")

        if self.scroll_magic:
            parts.append(f"마력 +{self.scroll_magic:g}")

        return " / ".join(parts) if parts else "-"

    def potential_text(self):
        if self.potential_int:
            return f"INT {self.potential_int:g}%"

        return "-"

    def additional_text(self):
        parts = []

        if self.additional_int:
            parts.append(f"INT {self.additional_int:g}%")

        if self.additional_magic:
            parts.append(f"마력 {self.additional_magic:g}")

        return " / ".join(parts) if parts else "-"

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    def to_dict(self):
        return {
            "name": self.name,
            "price": self.price,

            "flame_int": self.flame_int,
            "flame_all": self.flame_all,

            "scroll_int": self.scroll_int,
            "scroll_magic": self.scroll_magic,

            "potential_int": self.potential_int,

            "additional_int": self.additional_int,
            "additional_magic": self.additional_magic,

            "used_count": self.used_count,
            "max_count": self.max_count,

            "tax": self.tax,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get("name", ""),
            price=data.get("price", 0),

            flame_int=data.get("flame_int", 0),
            flame_all=data.get("flame_all", 0),

            scroll_int=data.get("scroll_int", 0),
            scroll_magic=data.get("scroll_magic", 0),

            potential_int=data.get("potential_int", 0),

            additional_int=data.get("additional_int", 0),
            additional_magic=data.get("additional_magic", 0),

            used_count=data.get("used_count", 0),
            max_count=data.get("max_count", 10),

            tax=data.get("tax", False),
        )


# ============================================================
# Equipment
# ============================================================

class Equipment:
    def __init__(self, name):
        self.name = name

        # 기준 아이템
        self.base_item = None

        # 경매장 매물
        self.items = []

    # --------------------------------------------------------
    # 기준템
    # --------------------------------------------------------

    def set_base(self, item):
        self.base_item = item

    # --------------------------------------------------------
    # 매물
    # --------------------------------------------------------

    def add_item(self, item):
        self.items.append(item)

    def remove_item_by_index(self, index):
        if 0 <= index < len(self.items):
            del self.items[index]

    def remove_item_by_name(self, name):
        self.items = [
            item for item in self.items
            if item.name != name
        ]

    def clear_items(self):
        self.items.clear()

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    def to_dict(self):
        return {
            "base_item": (
                self.base_item.to_dict()
                if self.base_item
                else None
            ),
            "items": [
                item.to_dict()
                for item in self.items
            ],
        }

    @classmethod
    def from_dict(cls, name, data):
        equipment = cls(name)

        base_data = data.get("base_item")

        if base_data:
            equipment.base_item = Item.from_dict(base_data)

        equipment.items = [
            Item.from_dict(item_data)
            for item_data in data.get("items", [])
        ]

        return equipment


# ============================================================
# Character
# ============================================================

class Character:
    def __init__(self, name):
        self.name = name

        # ★ 캐릭터별 독립 효율표
        self.efficiency_table = create_default_efficiency_table()

        # 실제 사용하는 장비만 생성
        self.equipments = {}

    # --------------------------------------------------------
    # 장비
    # --------------------------------------------------------

    def add_equipment(self, name):
        if name in self.equipments:
            return False

        self.equipments[name] = Equipment(name)
        return True

    def remove_equipment(self, name):
        if name not in self.equipments:
            return False

        del self.equipments[name]
        return True

    def get_equipment(self, name):
        return self.equipments.get(name)

    def get_equipment_names(self):
        return list(self.equipments.keys())

    # --------------------------------------------------------
    # 효율표
    # --------------------------------------------------------

    def reset_efficiency_table(self):
        self.efficiency_table = create_default_efficiency_table()

    def set_efficiency_table(self, table):
        self.efficiency_table = copy.deepcopy(table)

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    def to_dict(self):
        return {
            "efficiency_table": copy.deepcopy(
                self.efficiency_table
            ),
            "equipments": {
                name: equipment.to_dict()
                for name, equipment in self.equipments.items()
            },
        }

    @classmethod
    def from_dict(cls, name, data):
        character = cls(name)

        # v3 효율표
        saved_table = data.get("efficiency_table")

        if saved_table:
            character.efficiency_table = (
                cls._merge_efficiency_table(saved_table)
            )

        # 장비
        for equipment_name, equipment_data in (
            data.get("equipments", {}).items()
        ):
            character.equipments[equipment_name] = (
                Equipment.from_dict(
                    equipment_name,
                    equipment_data
                )
            )

        return character

    @staticmethod
    def _merge_efficiency_table(saved_table):
        """
        저장파일에 일부 항목이 없더라도
        기본값을 사용해서 안전하게 복원한다.
        """

        default_table = create_default_efficiency_table()

        for stat_name, stat_data in saved_table.items():

            if stat_name not in default_table:
                # 앞으로 새로운 스탯을 추가했을 때도 유지
                default_table[stat_name] = copy.deepcopy(stat_data)
                continue

            if isinstance(stat_data, dict):
                if "value" in stat_data:
                    default_table[stat_name]["value"] = (
                        float(stat_data["value"])
                    )

                if "final" in stat_data:
                    default_table[stat_name]["final"] = (
                        float(stat_data["final"])
                    )

        return default_table


# ============================================================
# CharacterManager
# ============================================================

class CharacterManager:
    SAVE_VERSION = 3

    def __init__(self):
        self.characters = {}

    # --------------------------------------------------------
    # 캐릭터
    # --------------------------------------------------------

    def add_character(self, name):
        if not name:
            return False

        if name in self.characters:
            return False

        self.characters[name] = Character(name)

        return True

    def remove_character(self, name):
        if name not in self.characters:
            return False

        del self.characters[name]

        return True

    def get_character(self, name):
        return self.characters.get(name)

    def get_names(self):
        return list(self.characters.keys())

    # --------------------------------------------------------
    # JSON 데이터
    # --------------------------------------------------------

    def to_dict(self):
        return {
            "version": self.SAVE_VERSION,
            "characters": {
                name: character.to_dict()
                for name, character in self.characters.items()
            },
        }

    def load_dict(self, data):
        version = data.get("version", 2)

        self.characters.clear()

        # v2 / v3 모두 읽을 수 있음
        if version not in (2, 3):
            raise ValueError(
                f"지원하지 않는 저장파일 버전입니다: {version}"
            )

        for name, character_data in (
            data.get("characters", {}).items()
        ):
            self.characters[name] = Character.from_dict(
                name,
                character_data
            )