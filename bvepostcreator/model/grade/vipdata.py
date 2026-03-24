# 클래스 정의
from dataclasses import dataclass


@dataclass
class VIPdata:
    """
    VIPdata는 종단 선형의 VIP (Vertical Intersection Point) 정보를 표현하는 데이터 클래스입니다.

    Attributes:
        VIPNO (int): VIP 번호.
        isvcurve (bool): 종곡선 여부 (True이면 종곡선이 존재함).
        seg (str): 종곡선의 형태 ('볼록형' 또는 '오목형').
        vradius (float): 종곡선 반경 R (미터 단위).
        vlength (float): 종곡선 길이 (미터 단위).
        next_slope (float): VIP 지점 이후의 종단 경사 (퍼밀 단위).
        prev_slope (float): VIP 지점 이전의 종단 경사 (퍼밀 단위).
        BVC_STA (float): 종곡선 시작점 (BVC).
        VIP_STA (float): VIP.
        EVC_STA (float): 종곡선 종료점 (EVC).
    """
    VIPNO: int = 0
    isvcurve: bool = False
    seg: str = ''
    vradius: float = 0.0
    vlength: float = 0.0
    next_slope: float = 0.0
    prev_slope: float = 0.0
    BVC_STA: float = 0.0
    VIP_STA: float = 0.0
    EVC_STA: float = 0.0