from dataclasses import dataclass


@dataclass
class VIPObjectDATA:
    no: int = 0
    vcurve_type: str = ''
    structure: str = ''
    station: float = 0.0
    object_index: int = 0
    filename: str = ''
    object_path: str = ''
    offset: tuple[float, float] = (0,0)
    rotation: float = 0.0