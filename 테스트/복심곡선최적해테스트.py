import math

def design_compound_curve_from_IA(
    IA_deg,
    R1, R2,
    alpha=0.25, beta=0.25
):
    """복심곡선 최적해 탐색 L1=/=L2인경우\n
    주어진 IA, R1, R2에 대해
    접선각 비율(α, β)을 설계자가 정하면
    →    L1, L2, CL1, CL2를 자동 폐합
    Arguments:
        alpha:교각 대비 시점부 접선각T 비율
        beta:교각 대비 종점부 접선각T 비율
    """
    IA = math.radians(IA_deg)

    if alpha + beta >= 1.0:
        raise ValueError("alpha + beta must be < 1")

    # --- 접선각
    T1 = alpha * IA
    T2 = beta * IA

    # --- 완화곡선 길이
    L1 = 2 * R1 * math.tan(T1)
    L2 = 2 * R2 * math.tan(T2)

    # --- 원곡선 각
    delta = IA - (T1 + T2)

    delta1 = delta * R1 / (R1 + R2)
    delta2 = delta * R2 / (R1 + R2)

    CL1 = R1 * delta1
    CL2 = R2 * delta2

    return {
        "L1": L1,
        "L2": L2,
        "CL1": CL1,
        "CL2": CL2,
        "T1_deg": math.degrees(T1),
        "T2_deg": math.degrees(T2),
        "IA_check_deg": math.degrees(T1 + delta1 + delta2 + T2)
    }

import math

def design_compound_curve_symmetric_L(
    IA_deg, R1, R2,
    tol=1e-10
):
    """복심곡선 최적해 탐색 ,L1=L2인경우"""
    IA = math.radians(IA_deg)

    def f(L):
        T1 = math.atan(L / (2 * R1))
        T2 = math.atan(L / (2 * R2))
        return T1 + T2 - IA * 0.5  # 기준값

    a, b = 0.0, 10000.0
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError("해가 구간에 없음")

    for _ in range(100):
        m = 0.5 * (a + b)
        fm = f(m)
        if abs(fm) < tol:
            break
        if fa * fm < 0:
            b, fb = m, fm
        else:
            a, fa = m, fm

    L = m
    T1 = math.atan(L / (2 * R1))
    T2 = math.atan(L / (2 * R2))

    delta = IA - (T1 + T2)
    delta1 = delta * R1 / (R1 + R2)
    delta2 = delta * R2 / (R1 + R2)

    CL1 = R1 * delta1
    CL2 = R2 * delta2

    return {
        "L": L,
        "L1": L,
        "L2": L,
        "CL1": CL1,
        "CL2": CL2,
        "T1_deg": math.degrees(T1),
        "T2_deg": math.degrees(T2),
        "IA_check_deg": math.degrees(T1 + delta1 + delta2 + T2)
    }
l1=53.94074
l2 = 42.01158
t1 = math.atan(
    (l1)/(2*310)
     )
t2 = math.atan(
    (l2)/(2*400)
     )
IA_deg=57+55 +45/60+36/60 + 8.25/3600+36.27/3600
IA = math.radians(IA_deg)
alpha = t1 / IA
beat = t2 / IA
res = design_compound_curve_from_IA(
    IA_deg=IA_deg,
    R1=310,
    R2=400,
    alpha=alpha,
    beta=beat
)

res2 = design_compound_curve_symmetric_L(IA_deg=IA_deg,R1=310,R2=400)
for k, v in res.items():
    print(f"{k:12s} : {v:.6f}")
