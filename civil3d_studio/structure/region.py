from dataclasses import dataclass


@dataclass
class StructureRegion:
    name: str
    structure_type: str   # "BRIDGE", "TUNNEL", "RETAINING_WALL"
    start_station: float
    end_station: float
    wall_side: str = "BOTH"