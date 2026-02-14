from dataclasses import dataclass


@dataclass
class EquipmentDATA:
    name: str
    index: int
    offset: tuple[float, float] = (0, 0)
    rotation: float = 0.0
    type:  str = ''