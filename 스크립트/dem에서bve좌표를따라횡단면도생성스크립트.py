
from tkinter.filedialog import askopenfilename
import tkinter as tk
from matplotlib import pyplot as plt
import math
import numpy as np
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from coordinate_utils import convert_coordinates
from srtm30 import SrtmDEM30

def read_coordinates(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    coordinates = []
    for line in lines:
        parts = line.strip().split(',')
        if len(parts) == 3:
            x = float(parts[0].strip())
            y = float(parts[1].strip())
            z = float(parts[2].strip())
            coordinates.append((x,y, z))
    return coordinates

def get_track_edges(coords, track_width):
    """노선 중심 좌표에서 좌우 offset으로 트랙 생성"""
    left_side = []
    right_side = []
    for i in range(len(coords)):
        if i < len(coords) - 1:
            x1, y1, z1 = coords[i]
            x2, y2, z2 = coords[i + 1]
            dx, dy = x2 - x1, y2 - y1
        else:
            # 마지막 점은 이전 점과 방향 벡터 사용
            x1, y1, z1 = coords[i]
            x2, y2, z2 = coords[i - 1]
            dx, dy = x1 - x2, y1 - y2


        length = np.sqrt(dx ** 2 + dy ** 2)
        nx, ny = -dy / length, dx / length
        left_side.append((x1 + nx * track_width / 2, y1 + ny * track_width / 2, z1))
        right_side.append((x1 - nx * track_width / 2, y1 - ny * track_width / 2, z1))

    return left_side, right_side  # ✅ 둘 다 반환

def horizontal_distance(p1, p2):
    return math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)

def write_slope_file(path, results):
    with open(path, 'w') as f:
        for res in results:
            cx, cy, cz = res['center']   # ✅ z까지 포함
            lx, ly, lz = res['left']
            rx, ry, rz = res['right']
            le = res['left_end']
            re = res['right_end']
            ld = res['left_dist']
            rd = res['right_dist']
            f.write(
                f"Center({cx:.2f},{cy:.2f},{cz:.2f}) "
                f"L({lx:.2f},{ly:.2f},{lz:.2f}) R({rx:.2f},{ry:.2f},{rz:.2f}) "
                f"Lend({le[0]:.2f},{le[1]:.2f},{le[2]:.2f}) "
                f"Rend({re[0]:.2f},{re[1]:.2f},{re[2]:.2f}) "
                f"Ldist={ld:.2f} Rdist={rd:.2f}\n"
            )



def plot_cross_section(ax, res):
    ax.clear()
    cx, cy, cz = res['center']   # ✅ z까지 포함

    le = res['left_end']
    re = res['right_end']

    center_elev = (le[2] + re[2]) / 2
    dist_left = -res['left_dist']
    dist_right = res['right_dist']
    elev_left = le[2]
    elev_right = re[2]

    ax.plot([dist_left, 0, dist_right],
            [elev_left, center_elev, elev_right],
            'o-', color='blue')
    ax.axhline(y=center_elev, color='gray', linestyle='--', label='Track Level')
    ax.set_title("Cross Section View")
    ax.set_xlabel("Horizontal Distance (m)")
    ax.set_ylabel("Elevation (m)")
    ax.legend()
    ax.figure.canvas.draw()


def gui_select_point(results):
    root = tk.Tk()
    root.title("Cross Section Viewer")

    fig, ax = plt.subplots(figsize=(8,6))
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def update_plot(event):
        idx = combo.current()
        if idx >= 0:
            plot_cross_section(ax, results[idx])

    combo = ttk.Combobox(root, values=[str(i) for i in range(len(results))])
    combo.current(0)
    combo.bind("<<ComboboxSelected>>", update_plot)
    combo.pack(side=tk.BOTTOM, fill=tk.X)

    # 초기 표시
    plot_cross_section(ax, results[0])

    root.mainloop()

from tqdm import tqdm

class SlopeBuilder:
    def add_slope(self, track_edges, dem, slope_ratio, side="left"):
        slope_side = []
        n = len(track_edges)

        for i in tqdm(range(n), desc=f"{side} 사면 계산"):
            x, y, z = track_edges[i]

            # 1. 해당 지점의 법선 벡터(Normal Vector) 계산
            # 현재 점과 다음 점(또는 이전 점)을 이용하여 진행 방향의 수직 벡터를 구함
            nx, ny = self._compute_normal_vector(track_edges, i, side)

            # 2. 성토/절토 판정 (선로 바로 옆 지면 높이 확인)
            is_cut = self._is_cut(x, y, z, nx, ny, dem)

            # 3. 이진 탐색으로 Daylight Point(교점) 찾기
            fx, fy, fz = self._find_daylight_point(x, y, z, nx, ny, slope_ratio, is_cut, dem)
            slope_side.append((fx, fy, fz))
        return slope_side

    def _compute_normal_vector(self, track_edges, i, side):
        x, y = track_edges[i][:2]
        if i < len(track_edges) - 1:
            dx = track_edges[i + 1][0] - x
            dy = track_edges[i + 1][1] - y
        else:
            dx = x - track_edges[i - 1][0]
            dy = y - track_edges[i - 1][1]

        length = np.sqrt(dx ** 2 + dy ** 2)
        return (-dy / length, dx / length) if side == "left" else (dy / length, -dx / length)

    def _is_cut(self, x, y, z, nx, ny, dem):
        lon, lat = convert_coordinates([x + nx * 0.1, y + ny * 0.1], 5186, 4326)
        dem_z = dem.get_elevation(lon, lat) + 100
        return z < dem_z

    def _find_daylight_point(self, x, y, z, nx, ny, slope_ratio, is_cut, dem):
        low, high = 0.0, 500.0
        for _ in range(15):
            mid = (low + high) / 2
            curr_x, curr_y = x + nx * mid, y + ny * mid
            slope_z = z + (mid / slope_ratio) if is_cut else z - (mid / slope_ratio)
            lon, lat = convert_coordinates([curr_x, curr_y], 5186, 4326)
            curr_dem_z = dem.get_elevation(lon, lat) + 100

            if is_cut:
                if slope_z < curr_dem_z:
                    low = mid
                else:
                    high = mid
            else:
                if slope_z > curr_dem_z:
                    low = mid
                else:
                    high = mid

        final_dist = (low + high) / 2
        fx, fy = x + nx * final_dist, y + ny * final_dist
        lon, lat = convert_coordinates([fx, fy], 5186, 4326)
        fz = dem.get_elevation(lon, lat) + 100
        return fx, fy, fz

    def extract_daylight_points(self, slope_l, slope_r):
        """사면의 끝점을 추출하여 폴리곤 경계 생성"""
        # 1. 각 사면의 끝점(Daylight Points)들 추출
        n_half_l = len(slope_l.points) // 2
        n_half_r = len(slope_r.points) // 2
        l_daylight = slope_l.points[n_half_l:]
        r_daylight = slope_r.points[n_half_r:]

        return l_daylight, r_daylight

def main():
    read_file = askopenfilename()
    if not read_file:
        raise FileNotFoundError('파일 오류')
    read_coords = read_coordinates(read_file)
    xy_list = [[x, y] for x, y, z in read_coords]

    # 좌표 변환
    print('좌표변환 시작')
    converted_coord = convert_coordinates(xy_list, 5186, 4326)
    dem = SrtmDEM30(converted_coord)

    track_width = 8.0 # 예시: 5m 폭
    slope_ratio = 1.5  # 기본 1:1.5

    results = []
    #트랙 생성
    print('트랙 생성 시작')
    left_side, right_side = get_track_edges(read_coords, track_width)

    # 좌우 사면 끝점 찾기
    print('사면 생성 시작')
    sb = SlopeBuilder()
    left_end = sb.add_slope(left_side, dem, slope_ratio, side="left")
    right_end = sb.add_slope(right_side, dem, slope_ratio, side="right")

    results = []
    print('결과 생성 시작')
    for i in range(len(read_coords)):
        center = read_coords[i]
        ld = horizontal_distance(left_side[i], left_end[i])
        rd = horizontal_distance(right_side[i], right_end[i])

        results.append({
            'center': center,
            'left': left_side[i],
            'right': right_side[i],
            'left_end': left_end[i],
            'right_end': right_end[i],
            'left_dist': ld,
            'right_dist': rd
        })

    # TXT 저장
    print('result 저장 시작')
    save_file = r'c:/temp/slope_result.txt'
    write_slope_file(save_file, results)

    # GUI로 측점 선택 → 횡단면도 표시
    print('횡단면도 작성 시작')
    gui_select_point(results)

    print('프로그램 종료')
if __name__ == '__main__':
    main()