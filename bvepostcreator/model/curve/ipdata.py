from dataclasses import dataclass

from curvepost.curve_util import CurveDirection


@dataclass
class IPdata:
    IPNO: int = 0
    curvetype: str = '' #곡선 종류(원곡선, 완화곡선, 복심곡선)
    curve_direction: CurveDirection = CurveDirection.RIGHT  # 기본값 우향
    radius: float = 0.0
    cant: float = 0.0
    BC_STA: float = 0.0
    EC_STA: float = 0.0
    SP_STA: float = 0.0
    PC_STA: float = 0.0
    CP_STA: float = 0.0
    PS_STA: float = 0.0