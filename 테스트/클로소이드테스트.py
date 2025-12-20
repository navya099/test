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
    """클로소이드 좌표 계산"""
    if s == 0 or a == 0:
        return 0, 0
    l = s / a
    r = 1 / l
    x = l * (1 - ((l**2)/(40*r**2)) + ((l**4)/(3456*r**4)) - ((l**6)/(599040*r**6)))
    y = (l**2)/(6*r) * (1 - ((l**2)/(56*r**2)) + ((l**4)/(7040*r**4)) - ((l**6)/(1612800*r**4)))
    return x * a, y * a

# --- 글로벌 좌표 변환 ---
def global_xy_cls(s, a, origin, origin_az, isexit=False, dir=CurveDirection.LEFT):
    """클로소이드 글로벌 좌표 계산"""
    x, y = clothoid(s, a)
    if isexit:
        x = -x
    if dir == CurveDirection.RIGHT:
        y = -y

    ca = math.cos(origin_az)
    sa = math.sin(origin_az)

    gx = origin.x + x * ca - y * sa
    gy = origin.y + x * sa + y * ca

    return Point2d(gx, gy)

# --- 교점 계산 ---
def cal_intersect_point(line1: Line2d, line2: Line2d):
    """두 직선의 교점 계산"""
    x1, y1 = line1.start.x, line1.start.y
    x2, y2 = line1.end.x, line1.end.y
    x3, y3 = line2.start.x, line2.start.y
    x4, y4 = line2.end.x, line2.end.y

    denom = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
    if denom == 0:
        raise ValueError("두 직선이 평행하여 교점이 없습니다.")

    Px = ((x1*y2 - y1*x2)*(x3-x4) - (x1-x2)*(x3*y4 - y3*x4)) / denom
    Py = ((x1*y2 - y1*x2)*(y3-y4) - (y1-y2)*(x3*y4 - y3*x4)) / denom

    return Point2d(Px, Py)

# --- 전체 좌표 계산 함수 ---
def calculate_curve(R, L1, L2, delta=0.1):
    """클로소이드+원곡선+ETC+IP 좌표 계산"""
    A1 = math.sqrt(R * L1)
    A2 = math.sqrt(R * L2)
    t1 = (A1**2) / (2 * R**2)
    t2 = (A2**2) / (2 * R**2)

    BTC = Point2d(0,0)

    # BCC 계산
    x1, y1 = clothoid(L1, A1)
    BCC = BTC.moved(0, x1)
    BCC.move(math.pi/2, y1)

    # 원곡선 중심과 ECC 계산
    C = BCC.moved(t1 + math.pi/2, R)
    ECC = C.moved(t1 - math.pi/2 + delta, R)

    # 원곡선 좌표
    theta_start = math.atan2(BCC.y - C.y, BCC.x - C.x)
    theta_end = math.atan2(ECC.y - C.y, ECC.x - C.x)
    theta_vals = np.linspace(theta_start, theta_end, 200)
    x_curve = C.x + R * np.cos(theta_vals)
    y_curve = C.y + R * np.sin(theta_vals)

    # ETC 계산
    tangent_angle = delta + t1 + t2
    x2, y2 = clothoid(L2, A2)
    ETC = ECC.moved(tangent_angle - math.pi /2 , y2)
    ETC.move(tangent_angle, x2)

    # IP 계산
    h2 = tangent_angle + math.pi
    line1 = Line2d(BTC, BTC.moved(0, 1000))
    line2 = Line2d(ETC, ETC.moved(h2, 1000))
    IP = cal_intersect_point(line1, line2)

    # 시점부 클로소이드 좌표
    s_pos = np.linspace(0, L1, 500)
    x_in, y_in = [], []
    for s in s_pos:
        pt = global_xy_cls(s, A1, origin=BTC, dir=CurveDirection.LEFT, isexit=False, origin_az=0)
        x_in.append(pt.x)
        y_in.append(pt.y)

    # 종점부 클로소이드 좌표
    s_pos2 = np.linspace(0, L2, 200)
    x_out, y_out = [], []
    for s in s_pos2:
        revs = L2 - s
        pt = global_xy_cls(revs, A2, origin=ETC, origin_az=tangent_angle, dir=CurveDirection.LEFT, isexit=True)
        x_out.append(pt.x)
        y_out.append(pt.y)

    return {
        'BTC': BTC, 'BCC': BCC, 'ECC': ECC, 'ETC': ETC, 'IP': IP,
        'x_in': x_in, 'y_in': y_in,
        'x_curve': x_curve, 'y_curve': y_curve,
        'x_out': x_out, 'y_out': y_out,
        'L1': L1, 'L2': L2,
        'A1': A1, 'A2': A2,
        'R': R,
    }

# --- 시각화 함수 ---
def plot_curve(data):
    plt.figure(figsize=(8,6))
    plt.plot(data['x_in'], data['y_in'], color='blue', label='진입클로소이드')
    plt.plot(data['x_curve'], data['y_curve'], color='red', label='원곡선')
    plt.plot(data['x_out'], data['y_out'], color='blue', label='진출클로소이드')

    for name, pt, color in [('BTC', data['BTC'], 'green'),
                             ('BCC', data['BCC'], 'orange'),
                             ('ECC', data['ECC'], 'purple'),
                             ('ETC', data['ETC'], 'brown'),
                             ('IP', data['IP'], 'black')]:
        plt.scatter(pt.x, pt.y, color=color, label=name)
        plt.text(pt.x, pt.y, name, fontsize=12, color=color)

    y_offset = 50
    plt.plot([data['BTC'].x, data['IP'].x], [data['BTC'].y, data['IP'].y], color='gray', label='h1')
    plt.plot([data['IP'].x, data['ETC'].x], [data['IP'].y, data['ETC'].y], color='gray', label='h2')
    plt.text(data['IP'].x, data['IP'].y -  y_offset,f"X={data['IP'].x:.4f}\nY={data['IP'].y:.4f}\nR={data['R']}")
    # --- 클로소이드 중간점 좌표 ---
    y_offset = 20
    mid_idx = len(data['x_in']) // 2
    mid_x_in = data['x_in'][mid_idx]
    mid_y_in = data['y_in'][mid_idx] + y_offset
    plt.text(mid_x_in, mid_y_in, f"L1={ data['L1']}\nA1={ data['A1']:.2f}", fontsize=10, color='blue')

    mid_idx_out = len(data['x_out']) // 2
    mid_x_out = data['x_out'][mid_idx_out]
    mid_y_out = data['y_out'][mid_idx_out] + y_offset
    plt.text(mid_x_out, mid_y_out, f"L2={ data['L2']}\nA2={ data['A2']:.2f}", fontsize=10, color='blue')

    plt.axis('equal')
    plt.title("클로소이드 + 원곡선 + ETC + IP")
    plt.xlabel("X (m)")
    plt.ylabel("Y (m)")
    plt.grid(True)
    plt.legend()
    plt.show()

def print_coord(data):
    print(f"{'-' * 4} 완화곡선좌표출력 {'-' * 4}")
    for name, pt, color in [('BTC', data['BTC'], 'green'),
                            ('BCC', data['BCC'], 'orange'),
                            ('ECC', data['ECC'], 'purple'),
                            ('ETC', data['ETC'], 'brown'),
                            ('IP', data['IP'], 'black')]:
        print(f'{name}: X = {pt.x}, Y = {pt.y}')

# --- 실행 예제 ---
L1 = 160
L2 = 320
R = 600
delta = 0.1
data = calculate_curve(R=R, L1=L1, L2=L2, delta=delta)
print_coord(data)
plot_curve(data)
