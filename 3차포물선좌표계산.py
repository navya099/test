import math
from modules.math_utils import degrees_to_dms, calculate_bearing, calculate_coordinates, calculate_distance
from modules.utils import format_distance

class AlignmentCalculator:
    def __init__(self, BP, IP, EP, R, M, V, C, BP_STA):
        self.BP = BP
        self.IP = IP
        self.EP = EP
        self.R = R      # 원곡선 반경
        self.M = M      # 캔트배수
        self.V = V      # 설계속도
        self.C = C      # 캔트
        self.SP = []
        self.PC = []
        self.CP = []
        self.PS = []

    def basic_cal(self):
        # 기본 완화곡선 계산
        self.X1 = self.M * self.C
        self.Y1 = self.X1 ** 2 / (6 * self.R)
        self.T = math.atan(self.X1 / (2 * self.R))
        self.T_dms = degrees_to_dms(math.degrees(self.T))

        # 방위각 계산
        self.q1 = calculate_bearing(*self.BP, *self.IP)
        self.q2 = calculate_bearing(*self.IP, *self.EP)
        self.q1_reverse = calculate_bearing(*self.IP, *self.BP)
        self.q2_reverse = calculate_bearing(*self.EP, *self.IP)

        #거리계산
        self.d1 = calculate_distance(self.BP, self.IP)
        self.d2 = math.sqrt((self.EP[0] - self.IP[0])**2 + (self.EP[1] - self.IP[1])**2)

        #교각
        self.ia = abs(self.q1 - self.q2)
        #원곡선교각
        self.ia2 = self.ia - 2 * self.T

        #방향
        self.direction = self.define_direction(self.q1, self.q2)

        # 파생 변수
        self.f = self.Y1 - (self.R * (1 - math.cos(self.T))) #이정량F
        self.k = self.f * math.tan(self.ia / 2) #수평좌표차K
        self.cl = self.R * (self.ia - 2 * self.T) #원곡선장
        self.L = self.X1 * (1 + 0.1 * (math.tan(self.T) ** 2)) #완화곡선장
        self.X2 = self.X1 - (self.R * math.sin(self.T))
        self.TL = self.R * math.tan(self.ia / 2) + self.X2 + self.k #접선장
        self.CL1 = self.cl + 2 * self.L #전체곡선장


    def calculate_sp(self):
        N = self.TL * math.cos(self.q1_reverse)
        E = self.TL * math.sin(self.q1_reverse)
        X = self.IP[0] + N
        Y = self.IP[1] + E
        self.SP = X, Y

    def calculate_ps(self):
        N = self.TL * math.cos(self.q2)
        E = self.TL * math.sin(self.q2)
        X = IP[0] + N
        Y = IP[1] + E
        self.PS = X, Y

    @staticmethod
    def define_direction(dir1, dir2):
        return -1 if math.sin(dir2 - dir1) < 0 else 1

    def calculate_pc(self):

        s = math.sqrt(self.X1 ** 2 + self.Y1 ** 2)
        innerangle = math.atan(self.Y1 / self.X1)
        direction = self.define_direction(self.q1, self.q2)
        azimuth = self.q1 + innerangle * direction

        N = s * math.cos(azimuth)
        E = s * math.sin(azimuth)
        X = self.SP[0] + N
        Y = self.SP[1] + E
        self.PC =  X, Y

    def calculate_cp(self):

        s = math.sqrt(self.X1 ** 2 + self.Y1 ** 2)
        innerangle = math.atan(self.Y1 / self.X1)
        direction = self.define_direction(self.q1, self.q2)
        azimuth = self.q2_reverse - innerangle * direction

        N = s * math.cos(azimuth)
        E = s * math.sin(azimuth)
        X = self.PS[0] + N
        Y = self.PS[1] + E
        self.CP =  X, Y

    def calculate_target_coord(self, target_sta):
        if target_sta < self.SP_STA: #시작 직선
            section = 'start_line'
            return self.calculate_target_coord_by_line(target_sta, self.BP_STA, self.BP, self.q1)
        elif target_sta > self.PS_STA:
            section = 'end_line'
            return self.calculate_target_coord_by_line(target_sta, self.PS_STA, self.PS, self.q2)
        elif self.SP_STA <= target_sta <= self.PC_STA:
            section = 'start_spiral'
            print('section : start_spiral')
            return self.calculate_target_coord_by_spiral(target_sta, self.SP_STA, self.SP, self.q1, flag=section)
        elif self.CP_STA <= target_sta <= self.PS_STA:
            section = 'end_spiral'
            print(f'section : {section}')
            return self.calculate_target_coord_by_spiral(target_sta, self.PS_STA, self.PS, self.q2_reverse, flag=section)
        else:
            section = 'curve'
            print('section : curve')
            return self.calculate_target_coord_by_simplecurve(target_sta)

    def calculate_target_coord_by_line(self, target_sta, start_sta, start_point, start_bearing):
        l = target_sta - start_sta
        result = calculate_coordinates(*start_point, start_bearing, l)
        return result

    def calculate_target_coord_by_spiral(self, target_sta, start_sta, start_point, start_bearing, flag=''):
        """
        스파이럴 구간 좌표 계산 (SP~PC 또는 CP~PS 모두 지원)
        Args:
            target_sta: 목표 측점
            start_sta: 구간 시작 측점 (SP 또는 CP)
            start_point: 구간 시작 좌표 (SP 또는 CP)
            start_bearing: 구간 시작 방위각 (q1 또는 q2)
            flag: 플래그
        """
        l = abs(target_sta - start_sta)  # 곡선거리
        x = l - (l ** 5) / (40 * self.R ** 2 * self.L ** 2)
        y = (x ** 3) / (6 * self.R * self.X1)

        s = math.sqrt(x ** 2 + y ** 2)
        q = math.atan(x ** 2 / (6 * self.R * self.X1))
        # 편기각 근사
        print(f'편기각: {(math.degrees(q))}')
        t = (l **2) / (6 * self.R * self.L) *3 # 접선각
        print(f'접선각: {math.degrees(t)}')
        if flag == 'start_spiral':
            q2 = start_bearing + q
        else:
            q2 = start_bearing - q
        print(f'방위각: {degrees_to_dms(math.degrees(q2) - 90)}')
        N = s * math.cos(q2)
        E = s * math.sin(q2)

        X = start_point[0] + N
        Y = start_point[1] + E
        return X, Y

    def calculate_target_coord_by_simplecurve(self, target_sta):
        l = target_sta - self.PC_STA  # 곡선거리
        #직선거리
        s = 2 * self.R * math.sin(
            ((l / self.cl) * self.ia2 ) / 2
        )
        q = l / self.R  * (1 / 2)#편기각
        print(f'편기각: {degrees_to_dms(math.degrees(q))}')
        t = self.q1 - self.T - (2 * q) #접선방위각
        print(f'접선방위각: {degrees_to_dms(math.degrees(t) -90)}')
        if self.direction == -1:
            q2 = self.q1 - self.T - q #방위각
        else:
            q2 = self.q1 + self.T + q  # 방위각
        print(f'방위각: {degrees_to_dms(math.degrees(q2) -90)}')

        N = s * math.cos(q2)
        E = s * math.sin(q2)
        X = self.PC[0] + N
        Y = self.PC[1] + E
        return X, Y

    def compute_all(self):
        #기본 제원 계산
        self.basic_cal()

        # SP, PS 좌표
        self.calculate_sp()
        self.calculate_ps()

        # PC, CP 좌표
        self.calculate_pc()
        self.calculate_cp()

        # 측점
        self.BP_STA = BP_STA
        self.IP_STA = self.BP_STA + self.d1
        self.SP_STA = self.IP_STA - self.TL
        self.PC_STA = self.SP_STA + self.L
        self.CP_STA = self.PC_STA + self.cl
        self.PS_STA = self.CP_STA + self.L
        D = math.sqrt(
            (self.EP[0] - self.PS[0]) ** 2 + (self.EP[1] - self.PS[0]) ** 2
        )
        self.EP_STA = self.PS_STA + D


        return {
            'SP': self.SP,
            'PS': self.PS,
            'PC': self.PC,
            'CP': self.CP,
            'SP_STA': self.SP_STA,
            'PC_STA': self.PC_STA,
            'CP_STA': self.CP_STA,
            'PS_STA': self.PS_STA
        }

import matplotlib.pyplot as plt
import numpy as np

class AlignmentPlotter:
    def __init__(self, alignment_calc):
        """
        Args:
            alignment_calc: AlignmentCalculator 객체
        """
        self.calc = alignment_calc

    def sample_curve(self, SP_STA, PS_STA, num_points=100):
        """
        완화곡선 구간을 num_points로 샘플링하여 좌표 리스트 생성
        """
        sta_values = np.linspace(SP_STA, PS_STA, num_points)
        curve_coords = [self.calc.calculate_target_coord(sta, SP_STA, self.calc.q1,
                                                         self.calc.compute_all(SP_STA)['SP'])
                        for sta in sta_values]
        return curve_coords

    def plot_curve(self, results, target_coord=None):
        """
        완화곡선 및 주요 점 시각화
        Args:
            results: AlignmentCalculator.compute_all() 결과
            target_coord: 타겟 좌표
        """
        # 곡선 샘플링
        curve_coords = self.sample_curve(results['SP_STA'], results['PS_STA'], num_points=200)
        curve_x = [c[0] for c in curve_coords]
        curve_y = [c[1] for c in curve_coords]

        # 주요 점
        major_points = {
            'SP': results['SP'],
            'PC': results['PC'],
            'CP': results['CP'],
            'PS': results['PS'],
        }
        if target_coord:
            major_points['Target'] = target_coord

        plt.figure(figsize=(10, 8))
        # 곡선 그리기
        plt.plot(curve_x, curve_y, '-', color='blue', label='Curve Path')

        # 주요 점 표시
        for name, coord in major_points.items():
            plt.plot(coord[0], coord[1], 'o' if name != 'Target' else 'x',
                     markersize=8 if name != 'Target' else 10,
                     color='red' if name == 'Target' else 'green')
            plt.text(coord[0], coord[1], f'{name}', fontsize=10,
                     ha='right', va='bottom', color='black')

        plt.xlabel('X (m)')
        plt.ylabel('Y (m)')
        plt.title('Alignment Curve Visualization')
        plt.axis('equal')
        plt.grid(True)
        plt.legend()
        plt.show()

# ---------------------------
# 사용 예제
BP = (240574.609, 474571.811)
IP = (241154.550, 474800.296)
EP = (243732.851, 477831.087)
R = 2000
M = 1300
V = 150
C = 0.133
BP_STA = 45199.9998

# AlignmentCalculator 객체 생성 (기존 코드)
calc = AlignmentCalculator(BP, IP, EP, R, M, V, C, BP_STA)

results = calc.compute_all()

target_sta = 46300
target_coord = calc.calculate_target_coord(target_sta)

#결과출력
print(f'target_sta: {format_distance(target_sta ,3)}')
print(f'SP좌표: {calc.SP}')
print(f'PC좌표: {calc.PC}')
print(f'CP좌표: {calc.CP}')
print(f'PS좌표: {calc.PS}')
print(f'SP측점: {format_distance(calc.SP_STA, 3)}')
print(f'PC측점: {format_distance(calc.PC_STA, 3)}')
print(f'CP측점: {format_distance(calc.CP_STA, 3)}')
print(f'PS측점: {format_distance(calc.PS_STA, 3)}')

print(f'목표좌표: {target_coord}')