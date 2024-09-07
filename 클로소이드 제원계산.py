import math

#입력 파라메터

R= 300 #곡선반경
B= 2.2 #직선구간 B
AA = 2.66 #곡선구간 A'
D = 4.4 #직선구간 선로중심간격
L= 68.85 #완화곡선길이

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

#상수
digit = 3#반올림 자릿수

#R1계산
RR = R + D/2 #R'

#외측궤도중심선
Lo = L
So = round((Lo ** 2 / (24 * RR)),digit)
Ro= round((R +(D/2))-So, digit)

#내측궤도중심선
Ri= round((Ro -(B + AA)), digit)
Si = round((B + AA) - D + So,digit)
Li = round(math.sqrt(24 * Ri * Si),3)

#구축중심선
Rc= round((Ro - AA ), digit)
Sc = round((B + AA) - D + So,digit)
Lc = round(math.sqrt(24 * Rc * Sc),3)

print(f'외측궤도 R= {Ro},구축중심 R= {Rc},내측궤도 R=  {Ri}') 
print(f'외측궤도 L= {L},구축중심 L= {Lc},내측궤도 L=  {Li}') 
    
