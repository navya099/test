from dataclasses import dataclass, field, asdict
from typing import Dict, Optional

# Design
@dataclass
class Design:
    speed: int
    prefix: str

# Mast
@dataclass
class Band:
    index: Dict[str, Dict]
    yoffset: Dict[str, Dict]

@dataclass
class Mast:
    index: Dict[str, Dict[str, int]]
    gauge: Dict[str, float]
    foundation: Dict[str, int | None]
    band: Band

# Bracket
@dataclass
class Bracket:
    index: Dict[str, Dict]
    fitting: Dict[str, Dict]

# RailwayConfig 전체 구조
@dataclass
class RailwayConfig:
    design: Design
    mast: Mast
    bracket: Bracket
    feeder: Dict[str, int]
    spreader: Dict[str, Dict[str, int]]
    wire: Dict[str, Dict]
    airjoint: Dict[str, Dict]
    airsection : Dict[str, Dict]
