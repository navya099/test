# ============================================================
# Equipment
# ============================================================
from models.item import Item


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