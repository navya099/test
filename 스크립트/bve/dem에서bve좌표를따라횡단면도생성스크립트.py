
from tkinter.filedialog import askopenfilename
import tkinter as tk

import meshio
from matplotlib import pyplot as plt
import math
import numpy as np
from tkinter import ttk, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import rasterio
import glob
from rasterio.windows import Window
from rasterio.merge import merge
import threading
from tkinter import messagebox
from scipy.interpolate import LinearNDInterpolator

class ExistGround:
    @staticmethod
    def extract_ground_line(terrain_mesh, center_pt, normal_vec, width=50, step=1.0):
        """
        3D Mesh로부터 2D 횡단면 데이터를 추출하는 핵심 함수

        :param terrain_mesh: meshio.Mesh 또는 정점/면 데이터
        :param center_pt: 중심점 좌표 [x, y, z]
        :param normal_vec: 진행방향 법선 벡터 (좌우 방향) [dx, dy, 0]
        :param width: 추출할 좌우 폭 (예: 50이면 좌 50m, 우 50m 총 100m)
        :param step: 샘플링 간격 (m)
        :return: (distances, elevations) 튜플
        """
        try:
            # 1. 메쉬 데이터 추출 (meshio 기준)
            points = terrain_mesh.points  # [N, 3] 배열
            x_mesh = points[:, 0]
            y_mesh = points[:, 1]
            z_mesh = points[:, 2]

            # 2. 2D 보간 함수 생성 (Scipy의 LinearNDInterpolator 사용)
            # 3D 공간의 (x, y) 좌표를 입력하면 z(고도)를 반환하는 함수입니다.
            interp_func = LinearNDInterpolator(list(zip(x_mesh, y_mesh)), z_mesh)

            # 3. 샘플링 포인트 생성
            # 법선 벡터를 단위 벡터로 정규화
            normal_vec = np.array(normal_vec[:2])  # z축 제외한 2D 평면 벡터
            norm = np.linalg.norm(normal_vec)
            if norm == 0:
                return np.array([]), np.array([])
            unit_normal = normal_vec / norm

            # 중심에서 좌(-)에서 우(+)까지 거리 생성
            distances = np.arange(-width, width + step, step)

            # 실제 좌표(X, Y) 계산
            sample_pts_x = center_pt[0] + distances * unit_normal[0]
            sample_pts_y = center_pt[1] + distances * unit_normal[1]

            # 4. 고도값 보간 (Interpolation)
            elevations = interp_func(sample_pts_x, sample_pts_y)

            # 5. 결과 필터링 (NaN 값 제거 - 메쉬 범위를 벗어난 지점)
            mask = ~np.isnan(elevations)
            return distances[mask], elevations[mask]

        except Exception as e:
            print(f"Ground extraction error: {e}")
            return np.array([]), np.array([])
def create_segment(xy_coord, buffer_x: int, buffer_y: int):
    """
    구간 분할 설정 (직사각형 범위)
    buffer_x: 노선 횡방향(또는 X축) 확장 거리
    buffer_y: 노선 진행방향(또는 Y축) 확장 거리
    """
    x, y = xy_coord
    minx = x - buffer_x
    miny = y - buffer_y
    maxx = x + buffer_x
    maxy = y + buffer_y

    return minx, miny, maxx, maxy

class SectionProvider:
    def __init__(self, dem_processor, structure_list, track_edges, slope_ratio, read_coords):
        self.dem_p = dem_processor
        self.structures = structure_list
        self.track_edges = track_edges
        self.slope_ratio = slope_ratio
        self.read_coords = read_coords

    def get_section(self, station_idx):
        """특정 인덱스의 측점을 3D Slice하여 2D 데이터로 반환"""
        try:
            center = self.xy_list[station_idx]
            seg = create_segment(center, buffer_x=500, buffer_y=100)
            # 1. Micro-Mesh 범위 설정 (중심 기준 좌우 50m, 전후 5m)
            # TerrainBuilder가 이 범위를 인식하도록 수정하거나,
            # seg 데이터를 해당 범위에 맞게 crop해서 전달
            terrain_builder = TerrainBuilder(self.dem_p, seg)
            terrain_mesh = terrain_builder.build(station_idx)

            # 2. 사면 생성 (해당 지점만)
            # SlopeManager 역시 Micro-Mesh 위에서만 동작하므로 매우 빠름
            slope_manager = SlopeManager(self.dem_p, terrain_mesh)
            slope_left, slope_right = slope_manager.build_slopes(self.track_edges[station_idx], self.slope_ratio)
            lside, rside = self.track_edges[station_idx]

            # get_section 내부에서 호출 시
            # normal_vec 계산 (진행방향 벡터 [dx, dy]를 90도 회전)
            p1 = np.array(self.xy_list[station_idx])
            p2 = np.array(self.xy_list[min(station_idx + 1, len(self.xy_list) - 1)])
            direction = p2 - p1
            normal = np.array([-direction[1], direction[0]])  # 시계반대방향 90도 회전

            ld = horizontal_distance(lside, slope_left)
            rd = horizontal_distance(rside, slope_right)

            # 함수 실행
            dist_g, elev_g = ExistGround.extract_ground_line(
                terrain_mesh=terrain_mesh,
                center_pt=self.xy_list[station_idx][1:4],  # [x, y, z]
                normal_vec=normal,
                width=50,  # 좌우 50m
                step=0.5  # 0.5m 간격으로 정밀하게 추출
            )
            return {
                'station': station, #측점
                'isstructure': False, #구조물 여부
                'center': center, #중심 좌표 x,y,z
                'left': lside, #좌측 선로끝 좌표
                'right': rside, #우측 선로 끝 좌표
                'left_end': slope_left, #좌측 사면 좌표
                'right_end': slope_right, #우측 사면 좌표
                'left_dist': dist_g[0], #좌측 선로끝 좌표에서 좌측사면 끝까지의 수평거리
                'right_dist': dist_g[1],#우측 선로끝 좌표에서 우측사면 끝까지의 수평거리
                'ground_profile': (dist_g, elev_g)  # ✅ 원지반선 저장
            }
        except Exception as e:
            raise e
class SlopeManager:
    """슬로프 빌더"""
    def __init__(self, dem, terrain_mesh):
        self.dem = dem
        self.slope_builder = None
        self.terrain_mesh = terrain_mesh
    def build_slopes(self, track_edges, slope_ratio=1.5):
        #트랙 사이드
        left_side, right_side = track_edges
        #빌더 초기화
        self.slope_builder = SlopeBuilder(self.terrain_mesh)

        # 좌측 사면
        slope_left = self.slope_builder.add_slope(left_side, self.dem, slope_ratio, side="left")

        # 우측 사면
        slope_right = self.slope_builder.add_slope(right_side, self.dem, slope_ratio, side="right")

        return slope_left, slope_right



class DEMExporter:
    """DEM 출력 모듈"""
    @staticmethod
    def export_as_geotiff(mosaic, out_transform, filename):
        # mosaic은 (bands, rows, cols) 형태
        band = mosaic[0]
        rows, cols = band.shape


        with rasterio.open(
                filename,
                'w',
                driver='GTiff',
                height=rows,
                width=cols,
                count=1,
                dtype=band.dtype,
                crs=CRS.from_epsg(4326),  # 좌표계 WGS84 (EPSG:4326)
                transform=out_transform,
        ) as dst:
            dst.write(band, 1)

    @staticmethod
    def export_as_mesh(band, transform):
        rows, cols = band.shape
        jj, ii = np.meshgrid(np.arange(cols), np.arange(rows))
        lon, lat = rasterio.transform.xy(transform, ii, jj, offset='center')
        lon = np.array(lon).flatten()
        lat = np.array(lat).flatten()
        coords = list(zip(lon, lat))
        xy = np.array(convert_coordinates(coords, 4326, 5186))
        z = band.flatten()
        vertices = np.column_stack((xy[:, 0], xy[:, 1], z))
        faces = []
        for i in range(rows - 1):
            for j in range(cols - 1):
                v1 = i * cols + j
                v2 = v1 + 1
                v3 = v1 + cols
                v4 = v3 + 1
                faces.append([v1, v2, v3])
                faces.append([v2, v4, v3])
        mesh = meshio.Mesh(points=vertices, cells=[("triangle", np.array(faces))])
        return mesh

class TerrainBuilder:
    """지형 빌더"""
    def __init__(self, dem_processor, seg_coords):
        self.dem_processor = dem_processor
        self.seg_coords = seg_coords

    def build(self, idx):
        """메쉬 빌드"""
        dem_mosaic, dem_out_transform = self.dem_processor.extract_segment(self.seg_coords)
        terrain_mesh = DEMExporter.export_as_mesh(dem_mosaic[0] + 100, dem_out_transform)

        return terrain_mesh

class DEMProcessor:
    """DEM 처리 클래스"""
    def __init__(self, coords):
        self.strm = SrtmDEM30(coords)

    def close(self):
        """DEM 닫기"""
        self.strm.close()

    def extract_by_segments(self, segments):
        """전체 세그먼트 처리"""
        results = []
        for idx, segment in enumerate(segments, start=1):
            mosaic, out_transform = self.extract_segment(segment)
            if mosaic is None:
                print(f"Segment {idx}: DEM 없음, 건너뜀")
                continue
            results.append((idx, mosaic, out_transform))
        return results

    def extract_segment(self, segment):
        """세그먼트별 DEM 추출"""
        try:
            minx, miny, maxx, maxy = segment
            bounds_4326 = convert_coordinates([(minx, miny), (maxx, maxy)], 5186, 4326)
            minx, miny = bounds_4326[0]
            maxx, maxy = bounds_4326[1]

            datasets = self.strm.selected_datasets
            if not datasets:
                return None, None

            mosaic, out_transform = merge(datasets, bounds=(minx, miny, maxx, maxy))
            return mosaic, out_transform
        except Exception as e:
            raise e
    def extract_tiff(self, segment):
        mosaic, out_transform = self.extract_segment(segment)

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
    def __init__(self, mesh):
        self.mesh = mesh

    def add_slope(self, track_edges, dem, slope_ratio, side="left"):
        slope_side = []
        n = len(track_edges)

        for i in range(n):
            x, y, z = track_edges[i]

            # 1. 해당 지점의 법선 벡터(Normal Vector) 계산
            # 현재 점과 다음 점(또는 이전 점)을 이용하여 진행 방향의 수직 벡터를 구함
            nx, ny = self._compute_normal_vector(track_edges, i, side)

            # 2. 성토/절토 판정 (선로 바로 옆 지면 높이 확인)
            is_cut = self._is_cut(x, y, z, nx, ny, dem)

            # 3. 이진 탐색으로 Daylight Point(교점) 찾기
            fx, fy, fz = self._find_daylight_point(x, y, z, nx, ny, slope_ratio, is_cut, dem)
            slope_side.append((fx, fy, fz))

        # 4. 메쉬 생성 (기존 로직 유지)
        return self._build_mesh(track_edges, slope_side)

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
        dem_z = dem.strm.get_elevation(lon, lat) + 100
        return z < dem_z

    def _find_daylight_point(self, x, y, z, nx, ny, slope_ratio, is_cut, dem):
        low, high = 0.0, 500.0
        for _ in range(15):
            mid = (low + high) / 2
            curr_x, curr_y = x + nx * mid, y + ny * mid
            slope_z = z + (mid / slope_ratio) if is_cut else z - (mid / slope_ratio)
            lon, lat = convert_coordinates([curr_x, curr_y], 5186, 4326)
            curr_dem_z = dem.strm.get_elevation(lon, lat) + 100

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
        fz = dem.strm.get_elevation(lon, lat) + 100
        return fx, fy, fz

    def _build_mesh(self, track_edges, slope_side):
        n = len(track_edges)
        vertices = np.array(track_edges + slope_side)
        faces = []
        for i in range(n - 1):
            ti, ti_next = i, i + 1
            si, si_next = i + n, i + 1 + n
            faces.append([ti, si, ti_next])
            faces.append([si, si_next, ti_next])
        return meshio.Mesh(points=vertices, cells=[("triangle", np.array(faces))])

    def extract_daylight_points(self, slope_l, slope_r):
        """사면의 끝점을 추출하여 폴리곤 경계 생성"""
        # 1. 각 사면의 끝점(Daylight Points)들 추출
        n_half_l = len(slope_l.points) // 2
        n_half_r = len(slope_r.points) // 2
        l_daylight = slope_l.points[n_half_l:]
        r_daylight = slope_r.points[n_half_r:]

        return l_daylight, r_daylight

    def create_polygon(self, l_daylight, r_daylight):
        # 왼쪽 끝점과 오른쪽 끝점을 역순으로 이어 붙여 닫힌 루프 생성
        poly_coords = np.concatenate([l_daylight[:, :2], r_daylight[::-1, :2]])

        return Polygon(poly_coords)


class Run(tk.Tk):
    def __init__(self):
        super().__init__()
        self.provider = None
        self.title('DEM 횡단면도 실시간 뷰어 (3D Slice 기반)')
        self.geometry('1000x800')
        self.current_idx = -1
        self.read_coords = []
        self.provider = None
        self.track_width = 8.0
        self.slope_ratio = 1.5
        self.is_processing = False  # 스레드 중복 실행 방지 플래그
        # --- UI 구성 ---
        # 상단 제어바 (슬라이더 및 스테이션 정보)
        self.ctrl_frame = ttk.Frame(self)
        self.ctrl_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.station_label = ttk.Label(self.ctrl_frame, text="측점: 0 (No Data)")
        self.station_label.pack(side=tk.LEFT, padx=5)

        self.slider = ttk.Scale(self.ctrl_frame, from_=0, to=len(self.read_coords) - 1,
                                orient=tk.HORIZONTAL, command=self._on_slider_move)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # 수정 코드
        self.btn_run = ttk.Button(self.ctrl_frame, text='실행', command=self._start_process)
        self.btn_run.pack(side=tk.LEFT, padx=5)
        # 수정 코드
        ttk.Button(self.ctrl_frame, text='종료', command=self.destroy).pack(side=tk.LEFT, padx=5)
        # 수정 코드
        ttk.Button(self.ctrl_frame, text='옵션', command=self.show_option).pack(side=tk.LEFT, padx=5)

        # 상태 표시줄
        self.status_var = tk.StringVar(value="대기 중...")
        # 수정 후 (복사 가능한 Entry로 변경)
        self.status_bar = tk.Entry(self, textvariable=self.status_var,
                                   relief=tk.SUNKEN,
                                   state='readonly',  # 사용자가 직접 타이핑하는 것은 방지
                                   readonlybackground='#f0f0f0',  # 배경색을 라벨처럼 설정
                                   borderwidth=1)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 차트 영역
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def show_option(self):
        """트랙 폭과 사면 기울기를 설정하는 팝업 창 생성"""
        # 팝업 창 설정
        option_win = tk.Toplevel(self)
        option_win.title("설정 옵션")
        option_win.geometry("300x200")
        option_win.grab_set()  # 설정 창이 닫히기 전까지 메인 창 조작 방지 (Modal)

        # 기본값 설정 (현재 클래스에 저장된 값 혹은 기본값)
        current_width = getattr(self, 'track_width', 8.0)
        current_ratio = getattr(self, 'slope_ratio', 1.5)

        # 입력 필드 레이아웃
        tk.Label(option_win, text="트랙 폭 (m):").pack(pady=(15, 0))
        ent_width = tk.Entry(option_win)
        ent_width.insert(0, str(current_width))
        ent_width.pack(pady=5)

        tk.Label(option_win, text="사면 기울기 (1:n):").pack(pady=(10, 0))
        ent_ratio = tk.Entry(option_win)
        ent_ratio.insert(0, str(current_ratio))
        ent_ratio.pack(pady=5)

        def save_and_close():
            try:
                # 입력값 검증 및 저장
                self.track_width = float(ent_width.get())
                self.slope_ratio = float(ent_ratio.get())
                self.status_var.set(f"옵션 변경 완료: 폭 {self.track_width}m, 기울기 1:{self.slope_ratio}")
                option_win.destroy()

                # 값이 바뀌었으므로 현재 화면 갱신 (이미 데이터가 로드된 경우)
                if self.provider:
                    self._on_slider_move(self.current_idx)

            except ValueError:

                messagebox.showerror("입력 오류", "숫자 형식을 입력해주세요.")

        # 저장 버튼
        tk.Button(option_win, text="적용", command=save_and_close).pack(pady=15)

    def _start_process(self):
        """데이터 로드 및 엔진 초기화 예외 처리 강화"""
        try:
            self.status_var.set('파일 선택 중...')

            # 1. 파일 선택 예외 처리
            read_file = filedialog.askopenfilename(title='좌표 파일 선택',
                                                   filetypes=[("CSV/TXT", "*.csv *.txt"), ("All Files", "*.*")])
            if not read_file: return

            struct_file = filedialog.askopenfilename(title='구조물 파일 선택',
                                                     filetypes=[("xlsx", "*.xlsx"), ("All Files", "*.*")])
            if not struct_file: return

            # 2. 데이터 로드 및 파싱 검증
            self.read_coords = read_coordinates(read_file)
            if not self.read_coords:
                raise ValueError("좌표 파일이 비어있거나 형식이 잘못되었습니다.")

            self.structure_list = parse_structure(struct_file)

            # 3. 데이터 추출 (stations, xy_list)
            if len(self.read_coords[0]) == 4:
                self.xy_list = [[x, y] for sta, x, y, z in self.read_coords]
                self.xyz_list = [[x, y, z] for sta, x, y, z in self.read_coords]
                self.stations = [sta for sta, x, y, z in self.read_coords]
            elif len(self.read_coords[0]) == 3:
                self.xy_list = [[x, y] for x, y, z in self.read_coords]
                self.xy_zlist = [[x, y, z] for x, y, z in self.read_coords]
                self.stations = [i * 25 for i, (x, y, z) in enumerate(self.read_coords)]
            else:
                raise ValueError("좌표 데이터의 컬럼 수가 맞지 않습니다. (Station, X, Y, Z 필요)")

            # 4. 좌표 변환 및 엔진 가동
            self.status_var.set('좌표변환 중...')
            converted_coord = convert_coordinates(self.xy_list, 5186, 4326)
            track_edges = get_track_edges(self.read_coords, self.track_width)

            self.status_var.set('DEM 데이터 처리 중...')
            self.dem_processor = DEMProcessor(converted_coord)

            self.provider = SectionProvider(
                dem_processor=self.dem_processor,
                structure_list=self.structure_list,
                track_edges=track_edges,
                slope_ratio=self.slope_ratio,
                read_coords=self.read_coords
            )

            # 5. UI 업데이트
            self.btn_run.config(state='disabled')
            self.slider.configure(from_=0, to=len(self.read_coords) - 1)
            self.slider.set(0)
            self._on_slider_move(0)

        except Exception as e:
            messagebox.showerror("실행 오류", f"프로세스 시작 중 오류가 발생했습니다:\n{str(e)}")
            self.status_var.set("준비 단계에서 오류 발생")
            self.btn_run.config(state='enabled')

    def _on_slider_move(self, val):
        """슬라이더 이동 시 메인 스레드에서 직접 호출"""
        if self.provider is None:
            return

        idx = int(float(val))
        if idx == self.current_idx:
            return

        self.current_idx = idx

        try:
            # 1. 상태 표시줄 업데이트 및 UI 강제 갱신
            self.status_var.set(f"측점 {idx} 연산 중... (Main Thread)")
            self.update_idletasks()  # "연산 중" 메시지가 화면에 즉시 보이게 함

            # 2. 직접 연산 수행 (스레드 없이 실행)
            data = self.provider.get_section(idx)

            # 3. 차트 그리기
            if data:
                self._draw_chart(data)
                self.status_var.set("연산 완료")
            else:
                self.status_var.set("데이터 없음")

        except Exception as e:
            error_msg = str(e)
            self._show_error(error_msg)
            messagebox.showerror("연산 오류", f"측점 {idx} 처리 중 오류:\n{error_msg}")
            self.btn_run.config(state='enabled')

    def _async_update(self, idx):
        """백그라운드 연산 및 GUI 업데이트 요청"""
        try:
            # SectionProvider에서 3D Micro-Mesh 기반 데이터 추출
            data = self.provider.get_section(idx)

            # GUI 업데이트는 메인 스레드에서 수행
            self.after(0, self._draw_chart, data)
        except Exception as e:
            import traceback
            err_details = traceback.format_exc()  # 상세 에러 내용 추출
            error_msg = str(e)
            # 람다 대신 직접 인자를 전달하는 메서드 호출
            self.after(0, self._show_error, err_details)

    def _show_error(self, message):
        self.status_var.set(f"Error: {message}")

    def _draw_chart(self, data):
        """전달받은 2D 데이터를 Matplotlib에 그리기"""
        self.ax.clear()

        # 지반선
        dist_g, elev_g = data['ground']
        self.ax.plot(dist_g, elev_g, color='green', label='Ground')

        # 사면
        dist_l, elev_l = data['slope_l']
        dist_r, elev_r = data['slope_r']
        self.ax.plot(dist_l, elev_l, color='purple', lw=2, label='Left Slope')
        self.ax.plot(dist_r, elev_r, color='red', lw=2, label='Right Slope')

        self.ax.legend()
        self.ax.set_title(f"Station: {data['station']}")
        self.canvas.draw()

        self.status_var.set("연산 완료")
        self.station_label.config(text=f"측점: {data['station']}")

    def _fetch_and_plot(self, idx):
        """SectionProvider를 통한 데이터 수집 및 그래프 갱신"""
        try:
            # 3D Micro-Mesh 생성 및 Slice 연산 (핵심 로직)
            data = self.provider.get_section(idx)

            # 메인 스레드에서 차트 업데이트 호출
            self.after(0, self._update_chart, data)
        except Exception as e:
            self.after(0, lambda: self.status_var.set(f"오류 발생: {str(e)}"))

    def _update_chart(self, data):
        """데이터를 바탕으로 실제 Matplotlib 그래프 갱신"""
        self.ax.clear()

        # 1. 지반선 (초록색)
        g_dist, g_elev = data['ground']
        self.ax.plot(g_dist, g_elev, color='green', label='Original Ground', lw=1.5)
        self.ax.fill_between(g_dist, g_elev, min(g_elev) - 5, color='green', alpha=0.1)

        # 2. 좌/우 사면 (보라색/빨간색 등)
        l_dist, l_elev = data['slope_l']
        r_dist, r_elev = data['slope_r']
        self.ax.plot(l_dist, l_elev, color='purple', lw=2, label='Left Slope')
        self.ax.plot(r_dist, r_elev, color='red', lw=2, label='Right Slope')

        self.ax.set_title(f"Cross Section at Station {data['station']}")
        self.ax.grid(True, alpha=0.3)
        self.ax.legend()
        self.ax.set_xlabel("Distance from Center (m)")
        self.ax.set_ylabel("Elevation (m)")

        self.canvas.draw()
        self.status_var.set("연산 완료")
        self.station_label.config(text=f"측점: {data['station']}")

if __name__ == '__main__':
    r = Run()
    r.mainloop()