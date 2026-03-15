from dataclasses import dataclass


@dataclass
class MastBase:
    name: str
    index: int
    offset: tuple[float, float]
    rotation: float