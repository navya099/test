import math
import numpy as np
import matplotlib.pyplot as plt

from curvedirection import CurveDirection
from line import Line2d
from point2d import Point2d

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# --- 클로소이드 함수 ---
def clothoid(s, a):
    """클로소이드
    s: 곡선 거리
    a: 클로소이드 매개변수 A"""
    l = s / a
    r = 1 / l
    x = l * (1 - ((l**2)/(40*r**2)) + ((l**4)/(3456*r**4)) - ((l**6)/(599040*r**6)))
    y = (l**2)/(6*r) * (1 - ((l**2)/(56*r**2)) + ((l**4)/(7040*r**4)) - ((l**6)/(1612800*r**6)))

    return x * a, y * a

def global_xy_cls(s, a, orizin,origin_az, isexit=False ,dir=CurveDirection):
    """클로소이드 글로벌 좌표"""
    x ,y = clothoid(s, a)
    if isexit:
        x = -x
    # 회전방향 부호
    if dir == CurveDirection.RIGHT:
        y = -y

    ca = math.cos(origin_az)
    sa = math.sin(origin_az)

    gx = orizin.x + x * ca - y * sa
    gy = orizin.y + x * sa + y * ca

    return Point2d(gx, gy)

def cal_intersect_point(line1: Line2d, line2: Line2d):
    """
    두 직선의 교점 계산
    line1, line2: Line2d 객체
        Line2d는 시작점 p1, 끝점 p2를 가짐
    반환: Point2d (교점 좌표)
    """

    x1, y1 = line1.start.x, line1.start.y
    x2, y2 = line1.end.x, line1.end.y

    x3, y3 = line2.start.x, line2.start.y
    x4, y4 = line2.end.x, line2.end.y

    # 직선 방정식: (x1,y1)->(x2,y2), (x3,y3)->(x4,y4)
    denom = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
    if denom == 0:
        raise ValueError("두 직선이 평행하여 교점이 없습니다.")

    Px = ((x1*y2 - y1*x2)*(x3-x4) - (x1-x2)*(x3*y4 - y3*x4)) / denom
    Py = ((x1*y2 - y1*x2)*(y3-y4) - (y1-y2)*(x3*y4 - y3*x4)) / denom

    return Point2d(Px, Py)

# --- 기본 파라미터 ---
R = 600      # 원곡선 반지름
L = 160     # 클로소이드 길이
a = math.sqrt(R * L)
t = (a**2) / (2 * R**2)  # 접선각
#ip좌표 추출
#교점함수 구현
h1 = 0

# BTC = (0,0)
BTC = Point2d(0,0)
x1,y1  = clothoid(L, a)
BCC = BTC.moved(h1, x1)  # 클로소이드 끝점 / 원곡선 시작점
BCC.move(h1 + math.pi / 2, y1)



C = BCC.moved(t + math.pi/2, R)  # 원곡선 중심
# --- ECC 계산 (원곡선 끝점) ---
delta = 2  # 원곡선 각도
ECC = C.moved(t - math.pi/2 + delta, R)

# --- 원곡선 좌표 ---
theta_start = math.atan2(BCC.y - C.y, BCC.x - C.x)
theta_end = math.atan2(ECC.y - C.y, ECC.x - C.x)
theta_vals = np.linspace(theta_start, theta_end, 100)
x_vals2 = C.x + R * np.cos(theta_vals)
y_vals2 = C.y + R * np.sin(theta_vals)

tangent_angle = delta + t * 2 # 원곡선 끝점의 접선 방향
ETC = ECC.moved(tangent_angle - math.pi /2 , y1)
ETC.move(tangent_angle, x1)


h2 = tangent_angle + math.pi
line1 = Line2d(BTC, BTC.moved(0,1000))
line2 = Line2d(ETC, ETC.moved(h2,1000))
IP = cal_intersect_point(line1, line2)

# ---시점부 클로소이드 좌표 ---
s_pos = np.linspace(0, L, 500)
x_vals, y_vals = [], []
for s in s_pos:
    pt = global_xy_cls(s, a, orizin=BTC, dir=CurveDirection.LEFT, isexit=False, origin_az=h1)
    x_vals.append(pt.x)
    y_vals.append(pt.y)

# --- 종점부 클로소이드 좌표 ---
s_pos2 = np.linspace(0, L, 50)
x_vals3, y_vals3 = [], []

for s in s_pos2:
    revs = L - s
    pt = global_xy_cls(revs, a, origin_az=tangent_angle, orizin=ETC, dir=CurveDirection.LEFT, isexit=True)
    x_vals3.append(pt.x)
    y_vals3.append(pt.y)

# --- print 출력 ---
print(f'BTC: X={BTC.x},Y={BTC.y}')
print(f'BCC: X={BCC.x},Y={BCC.y}')
print(f'ECC: X={ECC.x},Y={ECC.y}')
print(f'ETC: X={ETC.x},Y={ETC.y}')
print(f'IP: X={IP.x},Y={IP.y}')

# --- 시각화 ---
plt.figure(figsize=(8,6))
plt.plot(x_vals, y_vals, color='blue', label='진입클로소이드')
plt.plot(x_vals2, y_vals2, color='red', label='원곡선')
plt.plot(x_vals3, y_vals3, color='blue', label='진출클로소이드')

plt.scatter([BTC.x], [BTC.y], color='green', label='BTC')
plt.scatter(BCC.x, BCC.y, color='orange', label='BCC')
plt.scatter(ECC.x, ECC.y, color='purple', label='ECC')
plt.scatter(ETC.x, ETC.y, color='brown', label='ETC')
plt.scatter(IP.x, IP.y, color='black', label='IP')

plt.plot([BTC.x,IP.x], [BTC.y,IP.y], color='gray', label='h1')
plt.plot([IP.x ,ETC.x], [IP.y,ETC.y], color='gray', label='h2')

plt.text(IP.x, IP.y, 'IP',fontsize=12, color='black')
plt.text(BTC.x, BTC.y, 'BTC', fontsize=12, color='green')
plt.text(BCC.x, BCC.y, 'BCC', fontsize=12, color='orange')
plt.text(ECC.x, ECC.y, 'ECC', fontsize=12, color='purple')
plt.text(ETC.x, ETC.y, 'ETC', fontsize=12, color='brown')

plt.axis('equal')
plt.title("클로소이드 + 원곡선 + ETC")
plt.xlabel("X (m)")
plt.ylabel("Y (m)")
plt.grid(True)
plt.legend()
plt.show()
