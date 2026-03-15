from dataclasses import dataclass

from core.mast.base.mast_base import MastBase
from core.mast.mast_accessory.mast_accessory import MastAccessory


@dataclass
class Mast:
    name: str
    index: int
    offset: tuple[float, float]
    rotation: float = 0.0
    base: MastBase | None = None
    accessories: list[MastAccessory] = None
