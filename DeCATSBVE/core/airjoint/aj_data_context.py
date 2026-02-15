from dataclasses import dataclass


@dataclass
class AirjointDataContext:
    contact_wire_fitting: int
    messenger_wire_fittings: dict
    steady_arm_fitting: dict
    mast_type: int
    mast_name: str
    aj_bracket_values: list
    f_bracket_valuse: list
    feeder_idx: int
    feeder_name: str
    spreader_name: str
    spreader_idx: int
    f_bracket_height: float
