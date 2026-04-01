from dataclasses import dataclass

from curvepost.curve_util import CurveDirection


@dataclass
class IPdata:
    IPNO: int = 0
    curvetype: str = '' #곡선 종류(원곡선, 완화곡선, 복심곡선)
    curve_direction: CurveDirection = CurveDirection.RIGHT  # 기본값 우향
    radius: float = 0.0
    cant: float = 0.0
    BC_STA: float = None
    EC_STA: float = None
    SP_STA: float = None
    PC_STA: float = None
    CP_STA: float = None
    PS_STA: float = None