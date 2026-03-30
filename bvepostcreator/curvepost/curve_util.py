from enum import Enum

from model.curve.ipdata import IPdata


class CurveDirection(Enum):
    LEFT = '좌향'
    RIGHT = '우향'


#1. 곡선 구간(Line) 생성 분리
def get_curve_lines(ip: IPdata) -> list[list]:
    if ip.curvetype == '원곡선':
        return [['BC', ip.BC_STA], ['EC', ip.EC_STA]]
    elif ip.curvetype == '완화곡선':
        return [['SP', ip.SP_STA], ['PC', ip.PC_STA], ['CP', ip.CP_STA], ['PS', ip.PS_STA]]
    return []

def cal_speed(radius: float) -> float:
    return (radius * 160 / 11.8) ** 0.5

