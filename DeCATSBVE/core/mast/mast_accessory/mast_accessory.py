from dataclasses import dataclass


@dataclass
class MastAccessory:
    """전주용 부속 악세서리(밴드, 표지류 등)"""
    name: str
    index: int
    offset: tuple[float, float] = (0, 0)
    rotation: float = 0.0