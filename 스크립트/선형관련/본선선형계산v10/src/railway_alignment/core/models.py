# ============================================================
# 데이터 클래스
# ============================================================
from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class CurveParams:
    """IP별 선형 계산 결과 (매직 인덱스 제거)"""

    ip_no: int
    ip_xy: tuple[float, float]
    curve_type: str                     # 'simplecurve' | 'cubic'
    direction: str                      # 'LEFT CURVE' | 'RIGHT CURVE'
    h1: float                           # 방위각 1
    h2: float                           # 방위각 2
    ia_degree: float                    # 교각 (도)
    center_xy: tuple[float, float]
    radius: float
    ip_distance1: float
    ip_distance2: float
    m: float
    z: float
    v: float
    params: list                        # simplecurve_parameter 또는 cubic_parameter
    o_pc_bearing: float
    sp_pc_bearing: float
    theta_pc: float
    ip_sta: float

    # 측점 (curve_type에 따라 다름)
    sp_sta: Optional[float] = None
    pc_sta: Optional[float] = None
    cp_sta: Optional[float] = None
    ps_sta: Optional[float] = None
    bc_sta: Optional[float] = None
    ec_sta: Optional[float] = None

    # 좌표
    sp_xy: Optional[tuple[float, float]] = None
    pc_xy: Optional[tuple[float, float]] = None
    cp_xy: Optional[tuple[float, float]] = None
    ps_xy: Optional[tuple[float, float]] = None
    bc_xy: Optional[tuple[float, float]] = None
    ec_xy: Optional[tuple[float, float]] = None

    # 편의 프로퍼티
    @property
    def tl(self) -> float:
        if self.curve_type == "simplecurve":
            return self.params[0]
        return self.params[10]

    @property
    def cl(self) -> float:
        if self.curve_type == "simplecurve":
            return self.params[1]
        return self.params[12]

    @property
    def spiral_length(self) -> float:
        """완화곡선 길이 L (단곡선이면 0)"""
        return 0.0 if self.curve_type == "simplecurve" else self.params[3]


@dataclass
class StationRow:
    """측점 1개 행 데이터"""

    label: str
    sta: float
    station_offset: float
    coord: tuple[float, float]
    shiftx: float
    shifty: float
    ta: float                # 접선방위각
    chord_length: float      # 사거리
    q: float                 # 편기각
    t: float                 # 접선각
    azimuth: float           # 방위각