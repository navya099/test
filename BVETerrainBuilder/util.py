import numpy as np

def interpolate_z(orig_tri, p_2d):
    """원래 삼각형 평면 위의 (x, y)에 대응하는 정밀한 Z값을 계산"""
    p1, p2, p3 = orig_tri
    # 평면의 법선 벡터 (Normal Vector)
    v1 = p2 - p1
    v2 = p3 - p1
    n = np.cross(v1, v2)
    # 평면 방정식: a(x-x1) + b(y-y1) + c(z-z1) = 0
    # z = z1 - (a(x-x1) + b(y-y1)) / c
    if abs(n[2]) < 1e-9: return p1[2]  # 수직 평면 예외 처리
    z = p1[2] - (n[0] * (p_2d[0] - p1[0]) + n[1] * (p_2d[1] - p1[1])) / n[2]
    return z