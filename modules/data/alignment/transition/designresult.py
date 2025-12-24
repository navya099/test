from dataclasses import dataclass, field
from AutoCAD.point2d import Point2d
from data.alignment.geometry.simplecurve.curvegeometry import CurveGeometry
from data.alignment.geometry.spiral.spiral_geometry import SpiralGeometry


@dataclass
class TransitionDesignResult:
    """
    완화곡선 설계 결과 정보
    Attributes:
        entry_geometry: 시작 완화곡선 지오메트리 정보
        curve_geometry: 원곡선 지오메트리 정보
        exit_geometry: 끝 완화곡선 지오메트리 정보
    """
    # 진입 완화곡선
    entry_geometry: SpiralGeometry = SpiralGeometry
    # 원곡선
    curve_geometry: CurveGeometry = CurveGeometry
    # 진출 완화곡선
    exit_geometry: SpiralGeometry = SpiralGeometry

    # 주요 제어점
    ts: Point2d = field(default_factory=lambda: Point2d(0, 0))
    sc: Point2d = field(default_factory=lambda: Point2d(0, 0))
    cs: Point2d = field(default_factory=lambda: Point2d(0, 0))
    st: Point2d = field(default_factory=lambda: Point2d(0, 0))
    cc: Point2d = field(default_factory=lambda: Point2d(0, 0))
    # 각도
    az_ts: float = 0.0
    az_sc: float = 0.0
    az_cs: float = 0.0
    az_st: float = 0.0




