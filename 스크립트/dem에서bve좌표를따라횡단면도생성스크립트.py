
from tkinter.filedialog import askopenfilename
import tkinter as tk
from matplotlib import pyplot as plt
import math
import numpy as np
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import rasterio
import glob
from rasterio.windows import Window

def is_bridge_tunnel(sta, structure_list):
    """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
    for name, start, end in structure_list['bridge']:
        if start <= sta <= end:
            return True

    for name, start, end in structure_list['tunnel']:
        if start <= sta <= end:
            return True

    return False

def parse_structure(filepath):
    structure_list = {'bridge': [], 'tunnel': []}

    df_bridge = pd.read_excel(filepath, sheet_name='교량', header=None)
    df_tunnel = pd.read_excel(filepath, sheet_name='터널', header=None)

    df_bridge.columns = ['br_NAME', 'br_START_STA', 'br_END_STA', 'br_LENGTH']
    df_tunnel.columns = ['tn_NAME', 'tn_START_STA', 'tn_END_STA', 'tn_LENGTH']

    for _, row in df_bridge.iterrows():
        structure_list['bridge'].append((row['br_NAME'], row['br_START_STA'], row['br_END_STA']))
    for _, row in df_tunnel.iterrows():
        structure_list['tunnel'].append((row['tn_NAME'], row['tn_START_STA'], row['tn_END_STA']))
    return structure_list

class SrtmDEM30:
    def __init__(self, coords: list):
        self.selected_files = []
        self.selected_datasets = []  # ✅ dataset 객체를 직접 저장
        self.max_lat = 0.0
        self.min_lat = 0.0
        self.max_lon = 0.0
        self.min_lon = 0.0
        self.dem_folder = r"D:\도면\DEM\stm30m"
        self.dem_files = glob.glob(self.dem_folder + r"\n*_e*_1arc_v3*.tif")
        self.datasets = [rasterio.open(f) for f in self.dem_files]
        self.coords = coords
        self._init()

    #초기화 메소드
    def _init(self):
        """초기화 메소드"""
        self._find_boundary()
        self._set_selected_files()
        self._set_selected_datases()

    def _find_boundary(self):
        """최소 최대 범위선택"""
        self.min_lon = min(lon for lon, lat in self.coords)
        self.max_lon = max(lon for lon, lat in self.coords)
        self.min_lat = min(lat for lon, lat in self.coords)
        self.max_lat = max(lat for lon, lat in self.coords)

    #공개 API
    def get_elevations(self):
        """표고 리스트 반환용 API"""
        elevations = []
        for lon, lat in self.coords:
            ele = 0
            for ds in self.datasets:
                if ds.bounds.left <= lon <= ds.bounds.right and ds.bounds.bottom <= lat <= ds.bounds.top:
                    row, col = ds.index(lon, lat)
                    ele = float(ds.read(1, window=Window(col, row, 1, 1))[0, 0])
                    break
            elevations.append(ele)
        return elevations

    def get_elevation(self, lon, lat):
        """단일 표고 반환용 API
        Argumnets:
            lon: 경도
            lat: 위도
        """

        ele = 0
        for ds in self.datasets:
            if ds.bounds.left <= lon <= ds.bounds.right and ds.bounds.bottom <= lat <= ds.bounds.top:
                row, col = ds.index(lon, lat)
                ele = float(ds.read(1, window=Window(col, row, 1, 1))[0, 0])
                break
        return ele

    def _set_selected_files(self):
        """범위내 dem파일 선택"""
        selected_files = []

        for f in self.dem_files:
            name = f.split("\\")[-1]
            try:
                lat_tile = int(name[1:3])
                lon_tile = int(name[5:8])
            except ValueError:
                continue  # 파일명 형식 안 맞으면 무시
            # KML 범위에 포함되거나 주변 1도 버퍼 포함
            if self.min_lat - 1 <= lat_tile <= self.max_lat + 1 and self.min_lon - 1 <= lon_tile <= self.max_lon + 1:
                selected_files.append(f)
        #print(f"선택된 DEM 타일 수: {len(selected_files)}")
        self.selected_files = selected_files
        if not selected_files:
            raise ValueError("KML 범위에 맞는 DEM 파일을 찾을 수 없습니다.")

    def _set_selected_datases(self):
        """범위내 dem dataset 선택"""
        selected = []
        for ds in self.datasets:
            b = ds.bounds
            if (self.min_lat - 1 <= b.top and self.max_lat + 1 >= b.bottom and
                    self.min_lon - 1 <= b.right and self.max_lon + 1 >= b.left):
                selected.append(ds)
        self.selected_datasets = selected
        if not selected:
            raise ValueError("KML 범위에 맞는 DEM 파일을 찾을 수 없습니다.")

    def close(self):
        for ds in self.datasets:
            ds.close()

# coordinate_utils.py
import pyproj
from functools import lru_cache

@lru_cache(maxsize=8)
def _get_transformer(src: int, target: int):
    """Transformer 객체 캐싱 - 매 호출마다 재생성 방지"""
    return pyproj.Transformer.from_crs(src, target, always_xy=True)

def convert_coordinates(coords, src: int, target: int):
    """
    좌표 변환 (단일 또는 리스트/튜플)

    Args:
        coords: (x, y) 또는 [(x1, y1), (x2, y2), ...]
        src: 소스 EPSG
        target: 타겟 EPSG
    Returns:
        tuple 또는 list[tuple]
    """
    transformer = _get_transformer(src, target)  # ✅ 캐시에서 꺼냄

    # 단일 좌표
    if isinstance(coords[0], (int, float)):
        return transformer.transform(coords[0], coords[1])

    # ✅ 배치 변환 - 루프 없이 한번에 처리
    xs, ys = zip(*coords)
    result_xs, result_ys = transformer.transform(xs, ys)
    return list(zip(result_xs, result_ys))

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
        elif len(parts) == 4:
            station = float(parts[0].strip())
            x = float(parts[1].strip())
            y = float(parts[2].strip())
            z = float(parts[3].strip())
            coordinates.append((station, x, y, z))
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
            # 구조물 구간이면 None 처리
            if res['left'] is None or res['right'] is None:
                f.write(
                    f"Station {res['station']} - 구조물 구간\n"
                )
                continue

            cx, cy, cz = res['center']
            lx, ly, lz = res['left']
            rx, ry, rz = res['right']
            le = res['left_end']
            re = res['right_end']
            ld = res['left_dist']
            rd = res['right_dist']

            # None 값 방어
            if le is None or re is None:
                f.write(
                    f"Station {res['station']} - 사면 계산 불가\n"
                )
                continue

            f.write(
                f"Station {res['station']} "
                f"Center({cx:.2f},{cy:.2f},{cz:.2f}) "
                f"L({lx:.2f},{ly:.2f},{lz:.2f}) R({rx:.2f},{ry:.2f},{rz:.2f}) "
                f"Lend({le[0]:.2f},{le[1]:.2f},{le[2]:.2f}) "
                f"Rend({re[0]:.2f},{re[1]:.2f},{re[2]:.2f}) "
                f"Ldist={ld:.2f} Rdist={rd:.2f}\n"
            )




def plot_cross_section(ax, res):
    ax.clear()
    isstructure = res['isstructure']
    cx, cy, cz = res['center']
    if isstructure:
        # ✅ 원지반선 추가
        if 'ground_profile' in res:
            gx, gy = res['ground_profile']
            ax.plot(gx, gy, 'g-', label='Original Ground')

        # 구조물 구간 → 원지반선만 표시하거나 빈 화면
        ax.set_title("Cross Section View")
        ax.set_xlabel("Horizontal Distance (m)")
        ax.set_ylabel("Elevation (m)")
        ax.set_aspect('equal')
        ax.legend()
        ax.set_xlim(-50, 50)
        ax.set_ylim(cz - 50, cz + 50)
        ax.figure.canvas.draw()
        return

    lt = res['left']
    rt = res['right']
    le = res['left_end']
    re = res['right_end']

    center_elev = (le[2] + re[2]) / 2

    # 좌우 트랙 끝점의 수평거리
    dist_left = -horizontal_distance(res['center'], lt)
    dist_right = horizontal_distance(res['center'], rt)

    # 좌우 daylight의 수평거리
    dist_left_end = -horizontal_distance(res['center'], le)
    dist_right_end = horizontal_distance(res['center'], re)

    # 트랙
    ax.plot([dist_left, 0, dist_right],
            [lt[2], cz, rt[2]],
            'o-', color='black', label='Track')

    # 사면
    ax.plot([dist_left, dist_left_end],
            [lt[2], le[2]],
            'c-', label='Left Slope')
    ax.plot([dist_right, dist_right_end],
            [rt[2], re[2]],
            'm-', label='Right Slope')

    # ✅ 원지반선 추가
    if 'ground_profile' in res:
        gx, gy = res['ground_profile']
        ax.plot(gx, gy, 'g-', label='Original Ground')

    ax.set_title("Cross Section View")
    ax.set_xlabel("Horizontal Distance (m)")
    ax.set_ylabel("Elevation (m)")
    ax.set_aspect('equal')
    ax.set_xlim(-50, 50)
    ax.set_ylim(cz - 50, cz + 50)
    ax.legend()
    ax.figure.canvas.draw()


def extract_ground_profile(center, direction_vec, dem, width=25, step=5):
    """중심점 기준 좌우 폭으로 원지반선 추출"""
    cx, cy, cz = center
    dx, dy = direction_vec
    # 좌우 단위 벡터 (트랙 방향에 수직)
    ux, uy = -dy, dx
    length = math.sqrt(ux**2 + uy**2)
    ux, uy = ux/length, uy/length

    distances = []
    elevations = []
    for offset in np.arange(-width, width+step, step):
        px = cx + ux * offset
        py = cy + uy * offset
        lon, lat = convert_coordinates([px, py], 5186, 4326)
        elev = dem.get_elevation(lon, lat)
        distances.append(offset)
        elevations.append(elev + 100)
    return distances, elevations


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

    combo = ttk.Combobox(root, values=[f'{i * 25}' for i in range(len(results))])
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
    read_file = askopenfilename(title='좌표 파일 선택')
    if not read_file:
        raise FileNotFoundError('파일 오류')
    structure_file = askopenfilename(title='구조물 파일 선택')
    if not structure_file:
        raise FileNotFoundError('파일 오류')
    read_coords = read_coordinates(read_file)

    #리스트 길이에 따라 측점 선택
    if read_coords and len(read_coords[0]) == 4:
        stations = [sta for sta, x, y, z in read_coords]
        xy_list = [[x, y] for sta, x, y, z in read_coords]
    elif read_coords and len(read_coords[0]) == 3:
        stations = [i * 25 for i, (x, y, z) in enumerate(read_coords)]
        xy_list = [[x, y] for x, y, z in read_coords]
    else:
        raise ValueError(f'an error occured while reading {read_coords}')

    structure_list = parse_structure(structure_file)

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

    for i in tqdm(range(len(read_coords)), desc="트랙 처리"):
        center = read_coords[i]
        ld = horizontal_distance(left_side[i], left_end[i])
        rd = horizontal_distance(right_side[i], right_end[i])

        # 방향 벡터는 좌우 트랙 끝점으로부터 구함
        direction_vec = (right_side[i][0] - left_side[i][0],
                         right_side[i][1] - left_side[i][1])
        ground_x, ground_y = extract_ground_profile(center, direction_vec, dem)
        station = stations[i]
        if is_bridge_tunnel(station, structure_list):
            results.append({
                'station': station,
                'isstructure': True,
                'center': center,
                'left': None,
                'right': None,
                'left_end': None,
                'right_end': None,
                'left_dist': None,
                'right_dist': None,
                'ground_profile': (ground_x, ground_y)  # ✅ 원지반선 저장
            })
        else:
            results.append({
                'station': station,
                'isstructure': False,
                'center': center,
                'left': left_side[i],
                'right': right_side[i],
                'left_end': left_end[i],
                'right_end': right_end[i],
                'left_dist': ld,
                'right_dist': rd,
                'ground_profile': (ground_x, ground_y)  # ✅ 원지반선 저장
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