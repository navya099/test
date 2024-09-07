
import math
import numpy as np
from scipy.optimize import fsolve

# Define the function for the equation L
def equation(L, R, S):
    return L - np.sqrt((24 * R * S) / (1 - (L**2 / (112 * R**2)) + (L**4 / (2112 * R**4))))


#입력 파라메터

R= 300 #곡선반경
B= 2.2 #직선구간 B
AA = 2.66 #곡선구간 A'
D = 4.4 #직선구간 선로중심간격
L= 68.85 #완화곡선길이

'''
C = 0.076
THETA = math.atan(C / 1.5)
print(math.degrees(THETA))
W = 24000 / R
S = 2250 /R
H =2
HH = H + C / 2
F = HH * C / 1.5
print(F)
print(W)
print(S)
'''

#상수
digit = 32#반올림 자릿수

#R1계산
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

print(f'외측궤도 R= {Ro:.3f},구축중심 R= {Rc:.3f},내측궤도 R=  {Ri:.3f}') 
# Print results
print(f'외측궤도 L = {L:.3f}, 구축중심 L = {Lc_value:.3f}, 내측궤도 L = {Li_value:.3f}')
    
