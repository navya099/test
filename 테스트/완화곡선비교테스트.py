import math

import matplotlib.pyplot as plt
import numpy as np

# 사인반파장 체감곡선 함수
def sine_half_wave_xy(s, R, L, n=100):
    u = np.linspace(0, s, n)
    du = u[1] - u[0]

    theta = (1/(2*R)) * (u - (L/np.pi)*np.sin(np.pi*u/L))

    x = np.sum(np.cos(theta)) * du
    y = np.sum(np.sin(theta)) * du

    return x, y

def cubic_parabola(s, R, L, X1):
    """3차포물선 로컬좌표 (x, y) 계산"""
    x = s - (s ** 5) / (40 * R * R * (L ** 2))
    y = (x ** 3) / (6 * R * X1) if X1 != 0 else 0

    return x, y

def clothoid(s, a):
    """클로소이드
    s:곡선 거리
    a: 클로소이드 매개변수 A"""
    l = s / a
    r = 1 / l
    x = l * (1 - ((l**2) / (40 * r**2)) + ((l**4) / (3456 * r**4)) - ((l**6) / (599040 * r**6)))
    y = (l**2) / (6 * r) * (1 - ((l**2) / (56 * r**2)) + ((l**4) / (7040 * r**4)) - ((l**6) / (1612800 * r**6)))

    return x * a, y * a


# ------------------------
# 파라미터
# ------------------------
R = 140
L = 97.1284898

X1 = 96
A = math.sqrt(R * L) # 클로소이드 매개변수 예시
N=100
s_values = np.linspace(0, L, N)  # 곡선거리 0~L

# ------------------------
# 좌표 계산
# ------------------------
x_sine, y_sine = [], []
x_cubic, y_cubic = [], []
x_clothoid, y_clothoid = [], []

for s in s_values:
    xs, ys = sine_half_wave_xy(s, R ,L, N)
    x_sine.append(xs)
    y_sine.append(ys)

    xc, yc = cubic_parabola(s, R, L, X1)
    x_cubic.append(xc)
    y_cubic.append(yc)

    xcl, ycl = clothoid(s, A)
    x_clothoid.append(xcl)
    y_clothoid.append(ycl)

for x, y in zip(x_cubic, y_cubic):
    print(f'{x},{y}')
# ------------------------
# 시각화
# ------------------------
plt.figure(figsize=(10, 6))
plt.plot(x_sine, y_sine, label="Sine Half-Wave Curve", color='blue')
plt.plot(x_cubic, y_cubic, label="Cubic Parabola", color='green')
plt.plot(x_clothoid, y_clothoid, label="Clothoid (approx)", color='red')
plt.scatter([0, s_values[-1]], [0, y_sine[-1]], color='black', label='Start/End')
plt.xlabel("X (m)")
plt.ylabel("Y (m)")
plt.title("Comparison of 3 Transition Curves")
plt.grid(True)
plt.axis('auto')
plt.legend()
plt.show()