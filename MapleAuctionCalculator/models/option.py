# models/option.py

from dataclasses import dataclass


@dataclass
class StatOption:
    """
    하나의 스탯 옵션.

    예:
        INT +84
        올스탯 +4%
        마력 +10
        INT +12%
    """

    stat: str
    value: float

    def __post_init__(self):
        self.value = float(self.value)

    def to_dict(self):
        return {
            "stat": self.stat,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            stat=data.get("stat", ""),
            value=data.get("value", 0),
        )

    def text(self):
        """
        화면 표시용 문자열.
        """

        if self.stat in {
            "INT%",
            "STR%",
            "DEX%",
            "LUK%",
            "올스탯%",
        }:
            return f"{self.stat} +{self.value:g}%"

        return f"{self.stat} +{self.value:g}"