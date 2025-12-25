import math

from curvedirection import CurveDirection


class TransitionPointCalulator:
    """완화곡선 주요 좌표 계산 클래스"""
    def __init__(self, ip, h1 ,h2, params1, params2, tl1, tl2, direction):
        self.center_circle = None
        self.end_circle = None
        self.start_circle = None
        self.end_transition = None
        self.start_transition = None

        self.ip = ip
        self.h1 = h1
        self.h2 = h2
        self.params1 = params1
        self.params2 = params2
        self.tl1 = tl1
        self.tl2 = tl2
        self.dir = direction

    def run(self):
        """실행 메서드 (TS,ST,SC,CS, CENTER순서)"""
        self.cal_start_transition()
        self.cal_end_transition()
        self.cal_start_circle()
        self.cal_end_circle()
        self.cal_circle_center()

    def cal_start_transition(self):
        """완화곡선 시작 좌표 계산 메서드"""
        # ip에서 h1 역방향만큼 tl만큼 이동한 점
        point = self.ip.moved(self.h1 + math.pi, self.tl1)
        self.start_transition = point

    def cal_end_transition(self):
        """완화곡선 끝 좌표 계산 메서드"""
        # ip에서 h2만큼 tl만큼 이동한 점
        point = self.ip.moved(self.h2, self.tl2)
        self.end_transition = point

    def cal_start_circle(self):
        """원곡선 시작 좌표 계산 메서드"""
        # start_transition에서 x1만큼 이동
        point = self.start_transition.moved(self.h1, self.params1.x1)
        # y1만큼 이동(방향에 따라 +-)
        if self.dir == CurveDirection.LEFT:
            point.move(self.h1 + math.pi / 2, self.params1.y1)
        else:
            point.move(self.h1 - math.pi / 2, self.params1.y1)
        self.start_circle = point

    def cal_end_circle(self):
        """원곡선 종점 좌표 계산 메서드"""
        # end_transition에서 x1만큼 이동
        point = self.end_transition.moved(self.h2 + math.pi, self.params2.x1)
        # y1만큼 이동(방향에 따라 +-)
        if self.dir == CurveDirection.LEFT:
            point.move(self.h2 + math.pi / 2, self.params2.y1)
        else:
            point.move(self.h2 - math.pi / 2, self.params2.y1)

        self.end_circle = point

    def cal_circle_center(self):
        """원곡선 중심좌표 계산 메서드"""
        #방법1. start_circle과 cal_end_circle을 잇는 현으로 중짐점 구하기
        #pass
        #방법2. start_circle과 방위각으로 R을 통해 중짐점 구하기
        #방위각 계산
        if self.dir == CurveDirection.LEFT:
            theta = self.h1 + self.params1.theta_pc
            center = self.start_circle.moved(theta + math.pi /2, self.params1.radius)
        else:
            theta = self.h1 - self.params1.theta_pc
            center = self.start_circle.moved(theta - math.pi /2, self.params2.radius)

        self.center_circle = center
