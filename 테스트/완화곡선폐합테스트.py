import math

from data.alignment.geometry.spiral.params import TransitionCurveParams


import math
from data.alignment.geometry.spiral.params import TransitionCurveParams

def solve_L2_numeric(L1, R, ia, L2_min=0.0, L2_max=5000.0, tol=1e-10):
    """L1을 바탕으로 폐합할수 있는 L2찾기"""
    X1_1 = TransitionCurveParams.solve_x1(L1, R)

    def f(L2):
        X1_2 = TransitionCurveParams.solve_x1(L2, R)
        T1 = math.atan(X1_1 / (2 * R))
        T2 = math.atan(X1_2 / (2 * R))
        return T1 + T2 - ia

    a, b = L2_min, L2_max
    fa, fb = f(a), f(b)

    if fa * fb > 0:
        raise ValueError("해가 구간에 없음")

    for _ in range(100):
        m = 0.5 * (a + b)
        fm = f(m)
        if abs(fm) < tol:
            return m
        if fa * fm < 0:
            b, fb = m, fm
        else:
            a, fa = m, fm

    return m

def solve_L_equal(R, ia, L_min=0.0, L_max=5000.0, tol=1e-12):
    """R과 교각으로 폐합할수있는 완화곡선장 L 찾기
    L1==L2
    """
    def f(L):
        X1 = TransitionCurveParams.solve_x1(L, R)
        T = math.atan(X1 / (2 * R))
        return 2*T - ia

    a, b = L_min, L_max
    fa, fb = f(a), f(b)

    if fa * fb > 0:
        raise ValueError("해가 구간에 없음")

    for _ in range(200):
        m = 0.5 * (a + b)
        fm = f(m)
        if abs(fm) < tol:
            return m
        if fa * fm < 0:
            b, fb = m, fm
        else:
            a, fa = m, fm

    return m


# 예시
# 교각 IA (도분초 → rad)
ia = math.radians(59.48819023)
R  = 1200
L1 = 1200
L2 = solve_L2_numeric(L1, R, ia)
X1 = TransitionCurveParams.solve_x1(L1, R)
X2 = TransitionCurveParams.solve_x1(L2, R)

T1 = math.atan(X1 / (2 * R))
T2 = math.atan(X2 / (2 * R))

if abs((T1 + T2) - ia) < 1e-10:
    result = True
else:
    result = False

print(f"ia = { math.degrees(ia):.3f}")
print(f"X1 = {X1:.3f}")
print(f"X2 = {X2:.3f}")
print(f"L1 = {L1:.3f}")
print(f"L2 = {L2:.6f}")
print(f"T1 = { math.degrees(T1):.6f}")
print(f"T2 = { math.degrees(T2):.6f}")
print(f"T1+T2= { math.degrees(T1+T2):.6f}")
print(f"{result}")
