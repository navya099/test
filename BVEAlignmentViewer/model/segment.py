from dataclasses import dataclass, field

from vector2 import Vector2


@dataclass
class Segment:
    """
    공통 세그멘트 객체
    Attributes:
        start_sta (float): 시작 측점
        end_sta (float): 끝 측점
        start_coord (Vector2): 시작 좌표
        end_coord (Vector2): 끝 좌표
        start_azimuth (float): 시작 각도(라디안)
        end_azimuth (float): 종점 각도(라디안)
        length(float): 길이
    """
    start_sta: float = 0.0
    end_sta: float = 0.0
    start_coord: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    end_coord: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    start_azimuth: float = 0.0
    end_azimuth: float = 0.0
    length: float = 0.0

@dataclass
class StraightSegment(Segment):
    pass

@dataclass
class CurveSegment(Segment):
    """
    구간별 곡선 세그먼트 저장용 클래스 (단곡선).
    Attributes:
        radius(float): 원곡선 반경 R
        center_coord (Vector2): 원곡선 중심 좌표
        tl (float): 접선장(Tangent Length, TL)
        sl (float): 외할장(Chord Length, SL)
        m (float): 중앙종거(Middle Ordinate)

    """
    radius: float = 0.0
    center_coord: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    tl: float = 0.0
    sl: float = 0.0
    m: float = 0.0

@dataclass
class SpiralSegment(Segment):
    """
    구간별 곡선 세그먼트 저장용 클래스 (완화곡선).
    Attributes:
        x1(float):X1
        x2(float): X2
        w13(float): -R
        y1(float):Y1
        w15(float): W-Y
        f(float): 이정량 F
        s(float): 이정량 S
        k(float): 수평좌표차 K
        w(float): W
        tl(float): 전체 접선장 TL
        lc(float): 원곡선 길이 LC
        total_length(float): 전체곡선길이 CL
        sl(float); SL
        ria(float): 원곡선 교각 RIA
        c:(float): Thita
        xb(float): XB
        b(float): B
        isstarted(bool): 시작 완화곡선 여부
    """
    x1: float = 0.0
    x2: float = 0.0
    w13: float = 0.0
    y1: float = 0.0
    w15: float = 0.0
    f: float = 0.0
    s: float = 0.0
    k: float = 0.0
    w: float = 0.0
    tl: float = 0.0
    lc: float = 0.0
    total_length: float = 0.0
    sl: float = 0.0
    ria: float = 0.0
    c: float = 0.0
    xb: float = 0.0
    b: float = 0.0
    isstarted: bool = False