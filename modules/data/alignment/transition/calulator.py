import math

from data.alignment.geometry.spiral.params import TransitionCurveParams


class TransitionCalulator:
    """비대칭 대칭 완화곡선 TL및 CL 계산용 클래스"""
    def __init__(self):
        pass

    @staticmethod
    def cal_spec(radius: float,
                 params1: TransitionCurveParams,
                 params2: TransitionCurveParams, ia: float):
        """비대칭 대칭 완화곡선 TL및 CL 계산 메서드
        Arguments:
            radius: 곡선반경
            params1: 시작 완화곡선 파라메터 정보
            params2: 끝 완화곡선 파라메터 정보
            ia: 교각
        Returns:

        """
        r = params1.radius
        length1 = params1.l
        length2 = params2.l

        a1 = params1.a
        a2 = params2.a

        x1 = params1.x1
        y1 = params1.y1

        x2 = params2.x1
        y2 = params2.y1

        t1 = params1.theta_pc
        t2 = params2.theta_pc

        #XM 원곡선 중심 M의 X좌표
        xm1 = x1 - (r * math.sin(t1))
        xm2 = x2 - (r * math.sin(t2))

        #DR 원곡선 이정량 D
        dr1 = y1 + (r * math.cos(t1)) - r
        dr2 = y2 + (r * math.cos(t2)) - r

        #W
        w = (r + dr1) * math.tan(ia / 2)

        #접선장 차이 Z
        z1 = (dr2 - dr1) * (1 / math.sin(ia))
        z2 = (dr2 - dr1) * (1 / math.tan(ia))

        #접선장 D
        d1 = xm1 + w + z1
        d2 = xm2 + w - z2

        #원곡선교각 delta
        delta = ia - (t1 + t2)
        lc = r * delta

        return d1, d2, delta, lc

