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



