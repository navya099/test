from dataclasses import dataclass, field

from curvedirection import CurveDirection
from curvetype import CurveType
from model.segment import CurveSegment, SpiralSegment
from vector2 import Vector2

@dataclass
class BasePoint:
    """
    공통 좌표정보 클래스
    Attributes:
        coord(Vector2): 좌표
    """
    coord: Vector2 = Vector2(x=0, y= 0)

@dataclass
class EndPoint(BasePoint):
    """
    BP/EP용 클래스 (BasePoint 상속)
    Attributes:
        direction(float): 방향각도(라디안)
    """
    direction: float = 0.0

@dataclass
class IPdata(BasePoint):
    """
    IP 정보 저장용 데이터 클래스(BasePoint) 상속.

    Attributes:
        ipno (int): IP 번호
        curvetype (CurveType): 곡선 종류
        curve_direction (CurveDirection): 곡선 방향
        radius (float): 곡선 반지름
        ia (float): 교각
        segment (CurveSegment): 세그먼트 정보 리스트
    """
    ipno: int | str = 0
    curvetype: CurveType = CurveType.Simple
    curve_direction: CurveDirection = CurveDirection.RIGHT
    radius: float | tuple[float,...] = 0.0
    ia: float = 0.0
    segment: list[CurveSegment | SpiralSegment]  = field(default_factory=list)  # ⚡ 빈 리스트로 초기화