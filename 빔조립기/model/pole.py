from dataclasses import dataclass
from .rail import Rail

@dataclass
class Pole:
    station: float
    pole_number: str
    left_x: float
    right_x: float
    rails: list[Rail]
