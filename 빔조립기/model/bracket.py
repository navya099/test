from dataclasses import dataclass


@dataclass
class Bracket:
    rail_no: int
    type: str
    xoffset: float
    yoffset: float
    rotation: float
    index: int
