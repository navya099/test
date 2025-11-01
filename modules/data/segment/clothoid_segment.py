from dataclasses import dataclass

from data.segment import Segment


@dataclass
class ClothoidSegment(Segment):
    """
    클로소이드 완화곡선 세그먼트
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