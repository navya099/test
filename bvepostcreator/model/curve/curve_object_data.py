from dataclasses import dataclass


@dataclass
class CurveObjectDATA:
    no: int = 0
    curvetype: str = ''
    structure: str = ''
    station: float = 0.0
    object_index: int = 0
    filename: str = ''
    object_path: str = ''
    speed: int = 0
    offset: tuple[float, float] = (0, 0)
    rotation: float = 0.0