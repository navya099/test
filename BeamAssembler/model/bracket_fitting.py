from dataclasses import dataclass


@dataclass
class FittingDATA:
    index: int
    xoffset: float = 0.0
    yoffset: float = 0.0
    rotation: float = 0.0
    label: str = ""