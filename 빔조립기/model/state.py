# model/state.py
from dataclasses import dataclass, field

@dataclass
class RailState:
    name: str = ""
    index: int = 0
    brackets: list = field(default_factory=list)

@dataclass
class PoleInstallState:
    station: float = 0.0
    pole_number: str = ""
    railtype: str = "준고속철도"
    left_x: float = 0.0
    right_x: float = 0.0
    rails: list[RailState] = field(default_factory=list)
