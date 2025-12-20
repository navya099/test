import math
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def cubic_parabola_theta(s, R, L):
    """
    3차 포물선 기준 순간 접선각 θ(s)
    θ(s) = s^2 / (2 R L)
    """
    return s**2 / (2 * R * L)

def clothoid_integrate(R, L, num_points=500, x0=0, y0=0, theta0=0):
    """
    Civil3D 방식: 수치적분으로 클로소이드 좌표 계산
    R: 원곡선 반경
    L: 완화곡선 길이
    num_points: 분할 구간 수
    x0, y0: 시작점 좌표
    theta0: 초기 방위각 (라디안)
    """
    s_vals = np.linspace(0, L, num_points)
    x_vals = [x0]
    y_vals = [y0]

    ds = L / (num_points - 1)
    theta_prev = theta0

    for i in range(1, len(s_vals)):
        s = s_vals[i]
        # 순간 접선각 계산
        theta = theta0 + cubic_parabola_theta(s, R, L)
        # dx, dy 계산 (작은 구간 적분)
        dx = ds * math.cos(theta)
        dy = ds * math.sin(theta)
        # 누적
        x_vals.append(x_vals[-1] + dx)
        y_vals.append(y_vals[-1] + dy)

    return np.array(x_vals), np.array(y_vals)

# === 예제 ===
R = 100
L = 10000
x0, y0 = 0, 0
theta0 = 0  # 시작 방위각 0

x_vals, y_vals = clothoid_integrate(R, L, num_points=1000, x0=x0, y0=y0, theta0=theta0)

print(f"x_end = {x_vals[-1]:.3f}, y_end = {y_vals[-1]:.3f}")

# 시각화
plt.figure(figsize=(8,6))
plt.plot(x_vals, y_vals, label="Clothoid")
plt.scatter([x_vals[-1]], [y_vals[-1]], color='red', label="끝점")
plt.axis('equal')
plt.grid(True)
plt.legend()
plt.show()
