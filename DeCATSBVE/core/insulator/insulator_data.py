from dataclasses import dataclass


@dataclass
class InsulatorData:
    pos: int
    index: int
    type: str
    offset: tuple[float, float]
    yaw: float
    pitch: float
    roll: float
