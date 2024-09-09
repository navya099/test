
import math
import numpy as np
from scipy.optimize import fsolve

#상수
digit = 32#반올림 자릿수

# Define the function for the equation L
def equation(L, R, S):
    return L - np.sqrt((24 * R * S) / (1 - (L**2 / (112 * R**2)) + (L**4 / (2112 * R**4))))

def get_input_parameter():
    while True:
        try:
            # 입력 파라미터
            R = float(input('R (곡선반경) : '))
            B = float(input('B (직선구간 B) : '))
            AA = float(input('AA (곡선구간 A) : '))
            D = float(input('D (선로중심간격) : '))
            L = float(input('L (완화곡선길이) : '))
            
            parameter = [R, B, AA, D, L]
            return parameter
        except ValueError:
            print("잘못된 입력입니다. 숫자를 입력해주세요.")

def mainloop():
    while True:
        mode = select_mode()
        if mode == 0:
            parameter = get_input_parameter()
        else:
            parameter = cal_parameter()
        result = cal_clothoid(parameter)
        print_clothoid(result)
        print('계산이 끝났습니다. 계속하시려면 1, 종료는 0을 입력해주세요.')
        
        while True:
            try:
                isexit = int(input())  # 0 또는 1을 입력받음
                if isexit in [0, 1]:
                    break  # 0 또는 1이 입력되면 루프 종료
                else:
                    print("잘못된 입력입니다. 0 또는 1을 입력해주세요.")
            except ValueError:
                print("잘못된 입력입니다. 0 또는 1을 입력해주세요.")
        
        if isexit == 0:  # 종료 조건
            break

        
def cal_parameter():
    while True:
        try:
            R = float(input('R (곡선반경) : '))
            B = float(input('B (내측궤도 B) : '))
            D = float(input('D (선로중심간격) : '))
            
            V = (R * 160 / 11.8) ** 0.5
            if V >= 120:
                V = 120
            C = 11.8 * V ** 2 / R
            
            if C >= 160:
                C = 160
            
            L = 600 * C / 1000
            theta = math.atan(C / 1500)

            W = 24000 / R
            Qc = 4300 * math.sin(theta) - 1050 * (1 - math.cos(theta))
            S = 2400 / R
            alpha = round(W + Qc + S, -1)
            AA = B + alpha * 0.001

            print('parameter 계산 결과')
            print(f'AA = {AA}')
            print(f'L = {L}')
            
            parameter = [R, B, AA, D, L]
            return parameter
        except ValueError:
            print("잘못된 입력입니다. 숫자를 입력해주세요.")

class TrackData:
    def __init__(self, name, R, L):
        self.name = name
        self.R = R
        self.L = L
        
def cal_clothoid(parameter):

    #R1계산
    R,B,AA,D,L = parameter
    
    RR = R + D/2 #R'

    #외측궤도중심선
    Lo = L
    So = round((Lo ** 2 / (24 * RR)),digit)
    Ro= round((R +(D/2))-So, digit)

    #내측궤도중심선
    Ri= round((Ro -(B + AA)), digit)
    Si = round((B + AA) - D + So,digit)
    # Li 계산 (순서 변경)
    # Initial guess for L
    L_initial_guess = L

    # Solve for L
    Li = fsolve(equation, L_initial_guess, args=(Ri, Si))
    Li_value = Li[0]  # Extract the scalar value
    Li_value = round(Li_value, digit)  # Rounding to precision

    #구축중심선
    Rc= round((Ro - AA ), digit)
    Sc = round((B + AA) - D + So,digit)
    Lc = fsolve(equation, L_initial_guess, args=(Rc, Sc))
    Lc_value = Lc[0]  # Extract the scalar value
    Lc_value = round(Lc_value, digit)  # Rounding to precision

    # Create and return a list of TrackData objects
    result = [
        TrackData('외측궤도', Ro, L),
        TrackData('구축중심', Rc, Lc_value),
        TrackData('내측궤도', Ri, Li_value)
    ]
    
    return result

def print_clothoid(result):
    out, center, inner = result
    
    # 외측궤도, 구축중심, 내측궤도의 R과 L 값을 출력
    print(f'외측궤도 R= {out.R:.3f}, 구축중심 R= {center.R:.3f}, 내측궤도 R= {inner.R:.3f}') 
    print(f'외측궤도 L = {out.L:.3f}, 구축중심 L = {center.L:.3f}, 내측궤도 L = {inner.L:.3f}')

def select_mode():
    while True:
        try:
            print('완화곡선 제원을 알고 있는 경우 0, 모르는 경우 1')
            mode = int(input('계산 방법 선택: '))
            if mode in [0, 1]:
                return mode
            else:
                print("잘못된 입력입니다. 0 또는 1을 입력해주세요.")
        except ValueError:
            print("잘못된 입력입니다. 0 또는 1을 입력해주세요.")

def main():
    print('지하철 클로소이드 계산 프로그램')

    mainloop()
    print('프로그램을 종료합니다.')
    
if __name__ == '__main__':
    main()
