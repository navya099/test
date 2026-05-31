import math
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory

import chardet
import pandas as pd
import os

def file_valid_check(ext, filepath):
    # 헤더만 읽기
    if ext == '.xls':
        header_df = pd.read_excel(filepath, nrows=0)
    elif ext == '.csv':
        with open(filepath, 'rb') as f:
            result = chardet.detect(f.read(10000))  # 앞부분 샘플
        encoding = result['encoding']
        header_df = pd.read_csv(filepath, encoding=encoding, nrows=0)
    else:
        return False

    cols = header_df.columns.tolist()
    if ext == '.xls':
        required = ['선형 증분 측점 보고서']
    else:  # csv
        required = ['Display_Station', 'Bearing(Rad)', 'Northing', 'Easting', 'Real_Station']

    return all(col in cols for col in required)


def read_civil3d_data(filepath):
    """엑셀 파일에서 좌표 리스트 얻기"""

    file_ext = os.path.splitext(filepath)[1].lower()
    #유효성 체크
    vaild = file_valid_check(file_ext, filepath)
    if not vaild:
        raise Exception('지원하지 않는 파일입니다. 올바른 파일을 선택하세요')

    #파일 확장에따라 입력소스 분기
    if file_ext == '.xls':
        mode = 'civil3dreport'
        skiprows=14
        station_colum = '측점'
        bearing_colum = '접선 방향'
        df = pd.read_excel(filepath, skiprows=skiprows)
    elif file_ext == '.csv':
        mode = 'acadlisp'
        skiprows=0
        station_colum = 'Display_Station'
        bearing_colum = 'Bearing(Rad)'
        df = pd.read_csv(filepath, skiprows=skiprows)
    else:
        raise Exception(f'지원하지 않는 파일 형식 {file_ext}')

    coords = df[['Northing', 'Easting']].values.tolist()
    chainages = df[station_colum].values.tolist()
    bearings = df[bearing_colum].values.tolist()
    return chainages, coords, bearings, mode

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
    a = nx**2 + ny**2 - 1
    b = -2*(dx*nx + dy*ny)
    c = dx**2 + dy**2

    disc = b**2 - 4*a*c
    if disc < 0:
        return None

    # 직선 구간 처리
    if disc == 0:
        return [{"R": 0, "center": None, "side": None}]

    lam1 = (-b + math.sqrt(disc)) / (2*a)
    lam2 = (-b - math.sqrt(disc)) / (2*a)

    arcs = []
    for lam in [lam1, lam2]:
        cx = x1 + lam*nx
        cy = y1 + lam*ny
        r = abs(lam)

        # 좌/우 판별
        cvec = (cx - x1, cy - y1)
        cross = t[0]*cvec[1] - t[1]*cvec[0]
        side = "left" if cross > 0 else "right"

        arcs.append({"R": r, "center": (cx, cy), "side": side})

    return arcs





def generate_curve_cmds(chainages, coords, bearings: list[str], mode, tol=1e-6):
    results = []
    radii = []
    cmds = []

    for i in range(len(bearings) - 1):
        start = coords[i]
        end = coords[i + 1]
        chainage = chainages[i]

        theta1 = parse_bearing(bearings[i],mode)
        theta2 = parse_bearing(bearings[i + 1],mode)

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
    filepath = None
    while True:
        try:
            filepath = askopenfilename(title="Civil3D 보고서 또는 AcadLisp CSV 선택")
            if not filepath:
                raise FileNotFoundError("대상 파일을 찾을 수 없습니다")

            # 파일 읽기
            chainages, coords, bearings, mode = read_civil3d_data(filepath)

            print(f"파일 읽기 성공: {filepath}, 모드={mode}")
            break

        except Exception as e:
            print(f"오류 발생: 파일: {filepath}는 {e}")
            print("올바른 Civil3D 보고서(.xls) 또는 AcadLisp CSV(.csv)를 선택하세요.")
    # 좌표계 변환 (Civil 좌표계 → 수학 좌표계)
    coords = [[y, x] for x, y in coords]

    # 곡선반경 계산
    curve_cmds, radii, cmds = generate_curve_cmds(chainages, coords, bearings, mode)

    # 좌표 검산
    result = compute_coords(chainages, bearings, radii, start_coord=coords[0], mode=mode)

    # 에러 체크 (Δx, Δy, 거리오차)
    error_check_list = error_check(result, coords)

    #저장
    filepath_curve = askdirectory()
    if not filepath_curve:
        raise FileNotFoundError('저장 파일 경로가 선택되지 않았습니다.')

    # 곡선 결과 저장
    curve_file = os.path.join(filepath_curve, '평면선형.txt')
    save_txt(cmds, curve_file)

    # 오차 결과 저장
    filepath_error = os.path.join(filepath_curve, 'error_check.txt')
    save_errors(error_check_list, chainages, filepath_error)

def normalize_angle_diff(theta1, theta2):
    delta = theta2 - theta1
    # -pi ~ +pi 범위로 보정
    while delta > math.pi:
        delta -= 2 * math.pi
    while delta < -math.pi:
        delta += 2 * math.pi
    return delta


def compute_coords(chainages, bearings, radii, start_coord, mode):
    coords_calc = [start_coord]
    theta = parse_bearing(bearings[0], mode)  # 시작 방위각
    print(math.degrees(theta))
    for i in range(len(chainages) - 1):
        ds = chainages[i + 1] - chainages[i]
        r = radii[i]

        if r == float('inf') or r == 0:  # 직선
            x_new = coords_calc[-1][0] + ds * math.cos(theta)
            y_new = coords_calc[-1][1] + ds * math.sin(theta)
        else:  # 곡선
            dtheta = ds / r
            theta_new = theta + dtheta
            x_new = coords_calc[-1][0] + r * (math.sin(theta_new) - math.sin(theta))
            y_new = coords_calc[-1][1] - r * (math.cos(theta_new) - math.cos(theta))
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

def parse_bearing(bearing, mode):
    if mode == 'civil3dreport':
        return dms_to_radians(bearing)  # 문자열 → rad 변환
    elif mode == 'acadlisp':
        return float(bearing)           # 이미 rad 값

if __name__ == '__main__':
    main()
