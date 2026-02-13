from dataclasses import dataclass


@dataclass
class AirjointDataContext:
    airjoint_fitting: int
    flat_fitting: list
    steady_arm_fitting: list
    mast_type: int
    mast_name: str
    aj_bracket_values: list
    f_bracket_valuse: list
    feeder_idx: int
    feeder_name: str
    spreader_name: str
    spreader_idx: int
    f_bracket_height: float
