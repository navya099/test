import math
import pandas as pd

from math_utils import calculate_bearing


def read_civil3d_data():
    """엑셀 파일에서 좌표 리스트 얻기"""
    df = pd.read_excel(r"C:\Users\Administrator\Documents\CivilReport.XLS", skiprows=14)
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




#메인 로직
def generate_curve_cmds(chainages, coords, bearings, tol=0.005):
    cmds = []
    for i in range(len(bearings) -1):  # bearings 기준으로 순회
        if i <= len(coords)-1:
            start = coords[i]
            end = coords[i+1]
            chainage = chainages[i]
            start_bearing = bearings[i]
            end_bearing = bearings[i+1]

            # 방향각 변화량
            delta_bearing = end_bearing - start_bearing
            # 구간 길이
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            segment_length = 25

            # 직선 판정
            if abs(delta_bearing) < tol:
                cmds.append(f"{int(chainage)},.CURVE 0")
            else:
                # 반경 = 구간 길이 / 방향각 변화량
                r = abs(segment_length / delta_bearing)
                # 좌/우 판정
                side = "left" if delta_bearing > 0 else "right"
                r_signed = r if side == "right" else -r
                cmds.append(f"{int(chainage)},.CURVE {int(r_signed)}")

    return cmds

def save_txt(data, filepath):
    # 결과 확인
    with open(filepath, encoding='utf-8', mode='w') as file:
        for d in data:
            file.write(str(d) + '\n')
def main():

    #엑셀데이터 읽기
    chainages, coords, bearings = read_civil3d_data()

    #원본 좌표는 토목좌표계 기준(X-N,Y-E)으로 수학좌표계(X-E,Y-N)로 변환
    coords = [[y,x] for x,y in coords]

    """# 접선각 계산
    
    bearings= []
    for i in range(len(coords) - 1):
        start_coord = coords[i]
        end_coord = coords[i+1]
        bearing = calculate_bearing(start_coord, end_coord)
        bearings.append(bearing)"""

    #베어링 단위변환
    bearings = [math.radians(90 - bearing) for bearing in bearings]
    curve_cmds = generate_curve_cmds(chainages, coords ,bearings)
    filepath = r"D:\BVE\루트\Railway\Route\연습용루트\평면선형.txt"
    save_txt(curve_cmds, filepath)


if __name__ == '__main__':
    main()
