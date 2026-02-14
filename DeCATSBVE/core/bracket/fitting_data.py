from dataclasses import dataclass


@dataclass
class FittingDATA:
    index: int
    offset: tuple[float, float] = (0, 0)
    rotation: float = 0.0
    label: str = ""