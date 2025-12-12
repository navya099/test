from AutoCAD.point2d import Point2d
from curvedirection import CurveDirection
from transitioncurveparams import TransitionCurveParams
import math

class TransitionCurvatureCalculator:
    """완화곡선 좌표 계산 클래스
        Attributes:
            params:완화곡선 파라메터
            h1: ip시작 방위각(rad)
            h2: ip끝 방위각(rad)
            ip:IP좌표
            dir: 방향
            start_transition: 완화곡선 시작점
            start_circle: 원곡선 시작점
            end_circle: 원곡선 끝점
            end_transition: 완화곡선 끝점

    """
    def __init__(self, tr_params: TransitionCurveParams, h1: float, h2: float, ip: Point2d, direction: CurveDirection):
        self.params = tr_params
        self.h1 = h1
        self.h2 = h2
        self.ip = ip
        self.dir = direction
        self.start_transition = None
        self.start_circle = None
        self.end_circle = None
        self.end_transition = None

    def run(self):
        self.cal_start_transition()
        self.cal_end_transition()
        self.cal_start_circle()
        self.cal_end_circle()

    def cal_start_transition(self):
        """완화곡선 시작 좌표 계산 메서드"""
        #ip에서 h1 역방향만큼 tl만큼 이동한 점
        point = self.ip.moved(self.h1 + math.pi, self.params.total_tangent_length)
        self.start_transition = point

    def cal_end_transition(self):
        """완화곡선 끝 좌표 계산 메서드"""
        #ip에서 h2만큼 tl만큼 이동한 점
        point = self.ip.moved(self.h2, self.params.total_tangent_length)
        self.end_transition = point

    def cal_start_circle(self):
        """원곡선 시작 좌표 계산 메서드"""
        #start_transition에서 x1만큼 이동
        point = self.start_transition.moved(self.h1, self.params.x1)
        #y1만큼 이동(방향에 따라 +-)
        if self.dir == CurveDirection.LEFT:
            point.move(self.h1 + math.pi /2, self.params.y1)
        else:
            point.move(self.h1 - math.pi / 2, self.params.y1)
        self.start_circle = point

    def cal_end_circle(self):
        """원곡선 종점 좌표 계산 메서드"""
        # end_transition에서 x1만큼 이동
        point = self.end_transition.moved(self.h2 + math.pi, self.params.x1)
        # y1만큼 이동(방향에 따라 +-)
        if self.dir == CurveDirection.LEFT:
            point.move(self.h2 + math.pi / 2, self.params.y1)
        else:
            point.move(self.h2 - math.pi / 2, self.params.y1)

        self.end_circle = point