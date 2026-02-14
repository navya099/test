from dataclasses import dataclass


@dataclass
class Mast:
    name: str
    index: int
    offset: float
    rotation: float