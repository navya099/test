import math
import pandas as pd

from math_utils import calculate_bearing


def read_civil3d_data():
    """엑셀 파일에서 좌표 리스트 얻기"""
    df = pd.read_excel(r"C:\Temp\CivilReport.XLS", skiprows=14)
    coords = df[['Northing', 'Easting']].values.tolist()
    chainages = df['측점'].values.tolist()
    bearings = df['접선 방향'].values.tolist()
    return chainages, coords, bearings


import math

def arc_from_points_and_tangent(p1, p2, start_tangent_angle):
    x1, y1 = p1
    x2, y2 = p2

    # 접선 방향 벡터
    t = (math.cos(start_tangent_angle), math.sin(start_tangent_angle))
    # 법선 벡터
    n = (-t[1], t[0])

    dx, dy = x2 - x1, y2 - y1
    nx, ny = n

    # λ에 대한 이차방정식
    A = nx**2 + ny**2 - 1
    B = -2*(dx*nx + dy*ny)
    C = dx**2 + dy**2

    disc = B**2 - 4*A*C
    if disc < 0:
        return None

    # 직선 구간 처리
    if disc == 0:
        return [{"R": 0, "center": None, "side": None}]

    lam1 = (-B + math.sqrt(disc)) / (2*A)
    lam2 = (-B - math.sqrt(disc)) / (2*A)

    arcs = []
    for lam in [lam1, lam2]:
        cx = x1 + lam*nx
        cy = y1 + lam*ny
        R = abs(lam)

        # 좌/우 판별
        cvec = (cx - x1, cy - y1)
        cross = t[0]*cvec[1] - t[1]*cvec[0]
        side = "left" if cross > 0 else "right"

        arcs.append({"R": R, "center": (cx, cy), "side": side})

    return arcs


import math


def generate_curve_cmds(chainages, coords, bearings: list[str], tol=1e-6):
    results = []
    radii = []
    cmds = []

    for i in range(len(bearings) - 1):
        start = coords[i]
        end = coords[i + 1]
        chainage = chainages[i]

        theta1 = dms_to_radians(bearings[i])
        theta2 = dms_to_radians(bearings[i + 1])

        # 각도 차이를 보정
        delta_theta = normalize_angle_diff(theta1, theta2)

        dx = end[0] - start[0]
        dy = end[1] - start[1]
        segment_length = math.hypot(dx, dy)

        if segment_length > 0 and abs(delta_theta) > tol:
            curvature = delta_theta / segment_length
            radius = abs(1 / curvature)
            side = -1 if delta_theta > 0 else 1
        else:
            radius = 0.0
            side = 1

        cmd = f"{chainage},.curve {radius * side};0;"
        results.append((chainage, radius))
        radii.append(radius)
        cmds.append(cmd)

    return results, radii, cmds



def dms_to_radians(dms_str: str) -> float:
    dms_str = dms_str.replace("N ", "").strip()
    deg, rest = dms_str.split("°")
    minutes, seconds = rest.split("'")
    seconds = seconds.replace('"', '')
    deg = float(deg)
    minutes = float(minutes)
    seconds = float(seconds)
    decimal_degrees = 90 - (deg + minutes/60 + seconds/3600)
    return decimal_degrees * math.pi / 180

def save_txt(data, filepath):
    # 결과 확인
    with open(filepath, encoding='utf-8', mode='w') as file:
        for d in data:
            file.write(str(d) + '\n')
def main():
    # 엑셀데이터 읽기
    chainages, coords, bearings = read_civil3d_data()

    # 좌표계 변환 (Civil 좌표계 → 수학 좌표계)
    coords = [[y, x] for x, y in coords]

    # 곡선반경 계산
    curve_cmds, radii, cmds = generate_curve_cmds(chainages, coords, bearings)
    filepath_curve = r"D:\BVE\루트\Railway\Route\연습용루트\평면선형.txt"
    save_txt(cmds, filepath_curve)

    # 좌표 검산
    result = compute_coords(chainages, bearings, radii, start_coord=coords[0])

    # 에러 체크 (Δx, Δy, 거리오차)
    error_check_list = error_check(result, coords)

    # 오차 저장
    filepath_error = r"D:\BVE\루트\Railway\Route\연습용루트\좌표오차.txt"
    save_errors(error_check_list, chainages, filepath_error)

def normalize_angle_diff(theta1, theta2):
    delta = theta2 - theta1
    # -pi ~ +pi 범위로 보정
    while delta > math.pi:
        delta -= 2 * math.pi
    while delta < -math.pi:
        delta += 2 * math.pi
    return delta


def compute_coords(chainages, bearings, radii, start_coord):
    coords_calc = [start_coord]
    theta = dms_to_radians(bearings[0])  # 시작 방위각
    print(math.degrees(theta))
    for i in range(len(chainages) - 1):
        ds = chainages[i + 1] - chainages[i]
        R = radii[i]

        if R == float('inf') or R == 0:  # 직선
            x_new = coords_calc[-1][0] + ds * math.cos(theta)
            y_new = coords_calc[-1][1] + ds * math.sin(theta)
        else:  # 곡선
            dtheta = ds / R
            theta_new = theta + dtheta
            x_new = coords_calc[-1][0] + R * (math.sin(theta_new) - math.sin(theta))
            y_new = coords_calc[-1][1] - R * (math.cos(theta_new) - math.cos(theta))
            theta = theta_new

        coords_calc.append((x_new, y_new))

    return coords_calc

def error_check(coords_calc, coords_orig):
    errors = []
    for (xc, yc), (xo, yo) in zip(coords_calc, coords_orig):
        dx = xc - xo
        dy = yc - yo
        dist_error = math.hypot(dx, dy)
        errors.append((dx, dy, dist_error))
    return errors

def save_errors(errors, chainages, filepath):
    with open(filepath, encoding='utf-8', mode='w') as file:
        for i, (dx, dy, dist_error) in enumerate(errors):
            file.write(
                f"Chainage {chainages[i]}: Δx = {dx:.4f}, Δy = {dy:.4f}, DistError = {dist_error:.4f}\n"
            )


if __name__ == '__main__':
    main()
