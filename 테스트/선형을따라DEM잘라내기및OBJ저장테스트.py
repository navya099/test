import shutil
import time
from tkinter.filedialog import askopenfilename
import os
import meshio
from rasterio.merge import merge
from shapely.geometry import LineString, Point, Polygon
import numpy as np
import rasterio
from coordinate_utils import convert_coordinates
from srtm30 import SrtmDEM30
import geopandas as gpd
from shapely.geometry import box
from shapely.ops import nearest_points
from rasterio.crs import CRS

#전역변수
qml_template = """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
    <qgis version="3.16" styleCategories="Symbology">
      <renderer-v2 type="singleSymbol">
        <symbols>
          <symbol name="0" type="fill" alpha="1">
            <layer pass="0" class="SimpleFill" locked="0">
              <prop k="color" v="255,255,255,0"/> <!-- 채우기 없음 -->
              <prop k="outline_color" v="0,0,0,255"/> <!-- 외곽선 검정 -->
              <prop k="outline_width" v="0.1"/> <!-- 외곽선 두께 -->
              <prop k="style" v="no"/> <!-- 내부 채움 없음 -->
            </layer>
          </symbol>
        </symbols>
      </renderer-v2>
    </qgis>
    """

def save_dem_as_geotiff(mosaic, out_transform, filename):
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
        crs=CRS.from_epsg(4326),   # 좌표계 WGS84 (EPSG:4326)
        transform=out_transform,
    ) as dst:
        dst.write(band, 1)

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
            coordinates.append((x,y,z))
    return coordinates

def save_dem_as_obj(band, transform, filename):
    rows, cols = band.shape
    jj, ii = np.meshgrid(np.arange(cols), np.arange(rows))
    lon, lat = rasterio.transform.xy(transform, ii, jj, offset='center')
    lon = np.array(lon).flatten()
    lat = np.array(lat).flatten()
    coords = list(zip(lon, lat))
    xy = np.array(convert_coordinates(coords, 4326, 5186))
    z = band.flatten()
    vertices = np.column_stack((xy[:,0], xy[:,1], z))
    faces = []
    for i in range(rows-1):
        for j in range(cols-1):
            v1 = i*cols + j
            v2 = v1 + 1
            v3 = v1 + cols
            v4 = v3 + 1
            faces.append([v1, v2, v3])
            faces.append([v2, v4, v3])
    mesh = meshio.Mesh(points=vertices, cells=[("triangle", np.array(faces))])
    meshio.write(filename, mesh)
    return mesh

def sampling_coords(coords: list, distance_m: int, base_interval_m: int = 25):
    """
    coords: [(x,y,z), ...] EPSG:5186 좌표 (미터 단위)
    distance_m: 샘플링 간격 (미터)
    base_interval_m: 원본 좌표 간격 (기본값 25m)
    """
    step = distance_m // base_interval_m  # 인덱스 간격 계산
    return [(x, y) for i, (x, y, z) in enumerate(coords) if i % step == 0]

def _create_buffered(xy_list, buffer_m: int):
    # 구간 분할 설정
    segments = []
    for idx, (x, y) in enumerate(xy_list, start=1):
        point = Point(x, y)  # 샘플링된 점 자체를 중심점으로 사용
        buffered = point.buffer(buffer_m)  # 좌우 1km 버퍼
        segments.append(buffered.bounds)

    # 마지막 점도 별도로 저장
    last_point = Point(xy_list[-1][0], xy_list[-1][1])
    buffered_last = last_point.buffer(buffer_m)
    last_segment = buffered_last.bounds

    return segments, last_segment

def extract_segment_dem(segment, strm: SrtmDEM30):
    """세그먼트별 DEM 추출"""
    minx, miny, maxx, maxy = segment
    bounds_4326 = convert_coordinates([(minx, miny), (maxx, maxy)], 5186, 4326)
    minx, miny = bounds_4326[0]
    maxx, maxy = bounds_4326[1]

    datasets = strm.selected_datasets
    if not datasets:
        return None, None

    mosaic, out_transform = merge(datasets, bounds=(minx, miny, maxx, maxy))
    return mosaic, out_transform


def save_segment_files(idx, mosaic, out_transform):
    """세그먼트 DEM을 GeoTIFF와 OBJ로 저장"""
    # GeoTIFF 저장
    save_dem_as_geotiff(mosaic, out_transform, f"F:/temp/DEM/terrain_part_{idx}.tif")

def extract_dem_and_obj(segments, strm: SrtmDEM30):
    """전체 세그먼트 처리"""
    meshes = []
    shutil.rmtree("F:/temp/DEM/", ignore_errors=True)
    os.makedirs("F:/temp/DEM/", exist_ok=True)

    for idx, segment in enumerate(segments, start=1):
        mosaic, out_transform = extract_segment_dem(segment, strm)
        if mosaic is None:
            print(f"Segment {idx}: DEM 없음, 건너뜀")
            continue

        save_segment_files(idx, mosaic, out_transform)
        mesh = save_dem_as_obj(mosaic[0] + 100, out_transform, f"C:/temp/OBJ/terrain_part_{idx}.obj")
        meshes.append(mesh)

    return meshes


def save_shp(segments):
    # 구간별 Shapefile 저장
    shutil.rmtree("C:/temp/shp/", ignore_errors=True)
    os.makedirs("C:/temp/shp/", exist_ok=True)

    for idx, (minx, miny, maxx, maxy) in enumerate(segments, start=1):
        poly = box(minx, miny, maxx, maxy)
        gdf = gpd.GeoDataFrame([{"id": idx, "geometry": poly}], crs="EPSG:5186")
        out_shp = f"C:/temp/shp/segment_{idx}.shp"
        gdf.to_file(out_shp)
        #print("저장 완료:", out_shp)

def save_qml(segments):
    # 구간별 QML 생성
    for idx in range(1, len(segments) + 1):
        qml_path = f"C:/temp/shp/segment_{idx}.qml"
        with open(qml_path, "w", encoding="utf-8") as f:
            f.write(qml_template)
        #print("QML 저장 완료:", qml_path)


class MeshModifier:
    def __init__(self, mesh):
        self.mesh = mesh

    def add_slope(self, track_edges, dem: SrtmDEM30, slope_ratio, side="left"):
        slope_side = []
        n = len(track_edges)

        for i in range(n):
            x, y, z = track_edges[i]

            # 1. 해당 지점의 법선 벡터(Normal Vector) 계산
            # 현재 점과 다음 점(또는 이전 점)을 이용하여 진행 방향의 수직 벡터를 구함
            if i < n - 1:
                dx = track_edges[i + 1][0] - x
                dy = track_edges[i + 1][1] - y
            else:
                dx = x - track_edges[i - 1][0]
                dy = y - track_edges[i - 1][1]

            length = np.sqrt(dx ** 2 + dy ** 2)
            nx, ny = (-dy / length, dx / length) if side == "left" else (dy / length, -dx / length)

            # 2. 성토/절토 판정 (선로 바로 옆 지면 높이 확인)
            long, lat = convert_coordinates([x + nx * 0.1, y + ny * 0.1], 5186, 4326)
            dem_z = dem.get_elevation(long, lat) + 100  # 보정치 포함
            is_cut = z < dem_z  # 선로가 지면보다 낮으면 절토

            # 3. 이진 탐색으로 Daylight Point(교점) 찾기
            low = 0.0
            high = 500.0  # 최대 탐색 거리
            intersect_pos = [x, y, z]

            for _ in range(15):  # 15회 반복으로 정밀도 확보
                mid = (low + high) / 2
                curr_x = x + nx * mid
                curr_y = y + ny * mid

                # 사면의 높이 계산
                # 절토(is_cut): 위로 올라감(+), 성토: 아래로 내려감(-)
                slope_z = z + (mid / slope_ratio) if is_cut else z - (mid / slope_ratio)

                # 해당 지점의 실제 지면 높이
                l, a = convert_coordinates([curr_x, curr_y], 5186, 4326)
                curr_dem_z = dem.get_elevation(l, a) + 100

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

            # 탐색 완료된 최종 좌표 저장
            final_dist = (low + high) / 2
            fx, fy = x + nx * final_dist, y + ny * final_dist
            fl, fa = convert_coordinates([fx, fy], 5186, 4326)
            fz = dem.get_elevation(fl, fa) + 100
            slope_side.append((fx, fy, fz))

        # 4. 메쉬 생성 (기존 로직 유지)
        vertices = np.array(track_edges + slope_side)
        faces = []
        for i in range(n - 1):
            ti, ti_next = i, i + 1
            si, si_next = i + n, i + 1 + n
            faces.append([ti, si, ti_next])
            faces.append([si, si_next, ti_next])

        return meshio.Mesh(points=vertices, cells=[("triangle", np.array(faces))])


class TrackCreator:
    """OBJ 3D 트랙 생성 클래스"""

    def __init__(self, coords, track_width):
        self.coords = coords  # [(x,y,z)]
        self.track_width = track_width

    def create_track(self):
        """노선 중심 좌표에서 좌우 offset으로 트랙 메쉬 생성"""
        left_side = []
        right_side = []
        for i in range(len(self.coords) - 1):
            x1, y1, z1 = self.coords[i]
            x2, y2, z2 = self.coords[i + 1]
            dx, dy = x2 - x1, y2 - y1
            length = np.sqrt(dx ** 2 + dy ** 2)
            nx, ny = -dy / length, dx / length  # 수직 벡터
            left_side.append((x1 + nx * self.track_width / 2, y1 + ny * self.track_width / 2, z1))
            right_side.append((x1 - nx * self.track_width / 2, y1 - ny * self.track_width / 2, z1))

        # 좌우를 연결해 트랙 메쉬 생성
        vertices = np.array(left_side + right_side)
        faces = self.create_track_faces(left_side, right_side)
        return vertices, faces , left_side, right_side  # ✅ 둘 다 반환

    def create_track_faces(self, left_side, right_side):
        faces = []
        for i in range(len(left_side) - 1):
            # 좌측/우측 점 인덱스
            li, li_next = i, i + 1
            ri, ri_next = i + len(left_side), i + 1 + len(left_side)

            # 삼각형 두 개 생성
            faces.append([li, ri, li_next])
            faces.append([ri, ri_next, li_next])
        return faces

def filter_coords_by_segment(coords, segment_bounds):
    """구간 bounding box 안에 포함되는 좌표만 추출"""
    minx, miny, maxx, maxy = segment_bounds
    return [(x,y,z) for (x,y,z) in coords if minx <= x <= maxx and miny <= y <= maxy]

def save_obj_with_groups(filename,
                         terrain_vertices, terrain_faces,
                         track_vertices, track_faces,
                         slope_left=None, slope_right=None):
    with open(filename, "w") as f:
        # Terrain 그룹
        f.write("o Terrain\n")
        for v in terrain_vertices:
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")
        for face in terrain_faces:
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

        # Track 그룹
        f.write("o Track\n")
        offset = len(terrain_vertices)
        for v in track_vertices:
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")
        for face in track_faces:
            f.write(f"f {face[0]+1+offset} {face[1]+1+offset} {face[2]+1+offset}\n")

        # 좌측 slope 그룹
        if slope_left is not None:
            f.write("o SlopeLeft\n")
            offset2 = offset + len(track_vertices)
            for v in slope_left.points:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
            for face in slope_left.cells[0].data:
                f.write(f"f {face[0]+1+offset2} {face[1]+1+offset2} {face[2]+1+offset2}\n")

        # 우측 slope 그룹
        if slope_right is not None:
            f.write("o SlopeRight\n")
            offset3 = offset + len(track_vertices) + len(slope_left.points if slope_left else [])
            for v in slope_right.points:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
            for face in slope_right.cells[0].data:
                f.write(f"f {face[0]+1+offset3} {face[1]+1+offset3} {face[2]+1+offset3}\n")

class InputHandler:
    def __init__(self, filepath):
        self.filepath = filepath

    def load_segments(self):
        read_coords = read_coordinates(self.filepath)
        xy_list = sampling_coords(read_coords, 2000)
        segments, last_segment = _create_buffered(xy_list, 1000)
        return read_coords, xy_list, segments


class DEMProcessor:
    def __init__(self, coords):
        self.strm = SrtmDEM30(coords)

    def extract_segments(self, segments):
        return extract_dem_and_obj(segments, self.strm)

    def close(self):
        self.strm.close()


class TrackProcessor:
    def __init__(self, coords):
        self.trm = TrackCreator(coords, track_width=6)

    def build_track(self):
        return self.trm.create_track()


class MeshMerger:
    def __init__(self, terrain_mesh):
        self.msh = MeshModifier(terrain_mesh)

    def add_slopes(self, left_side, right_side, dem):
        slope_l = self.msh.add_slope(left_side, slope_ratio=1.5, side="left", dem=dem)
        slope_r = self.msh.add_slope(right_side, slope_ratio=1.5, side="right", dem=dem)
        return slope_l, slope_r

    def save(self, filename, terrain_vertices, terrain_faces, track_vertices, track_faces, slope_l, slope_r):
        save_obj_with_groups(filename, terrain_vertices, terrain_faces,
                             track_vertices, track_faces, slope_l, slope_r)


class OutputExporter:
    @staticmethod
    def save_shapefile(segments):
        save_shp(segments)

    @staticmethod
    def save_qml(segments):
        save_qml(segments)


import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from scipy.spatial import Delaunay
import meshio


def clip_with_shapely_delaunay(terrain_mesh, clipping_poly):
    vertices = terrain_mesh.points
    faces = terrain_mesh.cells[0].data

    final_vertices = []
    final_faces = []
    # 정점 중복 확인을 위한 딕셔너리 (좌표를 키로 사용)
    v_map = {}

    def get_v_idx(pt):
        pt_tuple = (round(pt[0], 4), round(pt[1], 4), round(pt[2], 4))
        if pt_tuple not in v_map:
            v_map[pt_tuple] = len(final_vertices)
            final_vertices.append(list(pt))
        return v_map[pt_tuple]

    for face in faces:
        tri_coords = vertices[face]
        tri_poly = Polygon(tri_coords[:, :2])

        # 1. 차집합 연산
        try:
            clipped_area = tri_poly.difference(clipping_poly)
        except:
            continue  # 기하학적 오류 스킵

        if clipped_area.is_empty: continue

        # 2. 결과물 분해 (Polygon/MultiPolygon)
        geoms = [clipped_area] if clipped_area.geom_type == 'Polygon' else clipped_area.geoms

        for poly in geoms:
            if poly.area < 0.001: continue  # 너무 작은 면적 제거 (크래시 방지 핵심)

            ext_coords = np.array(poly.exterior.coords)[:-1]  # 마지막 중복점 제거
            if len(ext_coords) < 3: continue

            # 3. 삼각 분할
            try:
                tri = Delaunay(ext_coords[:, :2])
                for t in tri.simplices:
                    # 삼각형의 중심점이 실제로 폴리곤 내부에 있는지 검사 (Delaunay의 오작동 방지)
                    pts_2d = ext_coords[t][:, :2]
                    centroid = np.mean(pts_2d, axis=0)
                    if not poly.contains(Point(centroid)): continue

                    # 4. 정점 인덱싱 및 Z값 보간
                    f_indices = []
                    for pt_2d in pts_2d:
                        z = interpolate_z(tri_coords, pt_2d)
                        idx = get_v_idx((pt_2d[0], pt_2d[1], z))
                        f_indices.append(idx)

                    final_faces.append(f_indices)
            except:
                continue

    return meshio.Mesh(points=np.array(final_vertices), cells=[("triangle", np.array(final_faces))])


def interpolate_z(orig_tri, p_2d):
    """원래 삼각형 평면 위의 (x, y)에 대응하는 정밀한 Z값을 계산"""
    p1, p2, p3 = orig_tri
    # 평면의 법선 벡터 (Normal Vector)
    v1 = p2 - p1
    v2 = p3 - p1
    n = np.cross(v1, v2)
    # 평면 방정식: a(x-x1) + b(y-y1) + c(z-z1) = 0
    # z = z1 - (a(x-x1) + b(y-y1)) / c
    if abs(n[2]) < 1e-9: return p1[2]  # 수직 평면 예외 처리
    z = p1[2] - (n[0] * (p_2d[0] - p1[0]) + n[1] * (p_2d[1] - p1[1])) / n[2]
    return z

def main():
    # 좌표 읽기
    file = askopenfilename()
    read_coords = read_coordinates(file)
    xy_list = sampling_coords(read_coords, 2000) # 2km 간격 샘플링
    segments, last_segment = _create_buffered(xy_list, 1000)

    # 폴더 초기화
    shutil.rmtree("C:/temp/OBJ", ignore_errors=True)
    os.makedirs("C:/temp/OBJ", exist_ok=True)

    # DEM 클래스 호출
    converterd_coord = convert_coordinates(xy_list, 5186, 4326)
    strm = SrtmDEM30(converterd_coord)

    start_time = time.time()

    # 각 구간별 DEM 추출
    print('각 구간별 DEM 추출')
    meshes = extract_dem_and_obj(segments, strm)

    # 각 구간별 트랙 생성 후 지형에 병합
    print('각 구간별 트랙 생성')
    for idx, seg in enumerate(segments, start=1):
        seg_coords = filter_coords_by_segment(read_coords, seg)
        print(f"Segment {idx} coords:", len(seg_coords))
        if len(seg_coords) < 2:
            continue
        trm = TrackCreator(seg_coords, track_width=6)

        vertices, faces, left_side, right_side = trm.create_track()
        print("Vertices:", vertices.shape)
        print("Faces:", len(faces))
        track_mesh = meshio.Mesh(points=vertices, cells=[("triangle", np.array(faces))])

        msh = MeshModifier(meshes[idx-1])
        # 좌측/우측 edge에 slope 추가
        slope_l = msh.add_slope(left_side, slope_ratio=1.5, side="left", dem=strm)
        slope_r = msh.add_slope(right_side, slope_ratio=1.5, side="right", dem=strm)
        print("Slope Left vertices:", slope_l.points.shape)
        print("Slope Left faces:", slope_l.cells[0].data.shape)
        print("Slope Right vertices:", slope_r.points.shape)
        print("Slope Right faces:", slope_r.cells[0].data.shape)

        # DEM 메쉬에서 vertices, faces 추출
        terrain_vertices = meshes[idx - 1].points
        terrain_faces = meshes[idx - 1].cells[0].data

        # 트랙 메쉬에서 vertices, faces 추출
        track_vertices = vertices
        track_faces = np.array(faces)

        # 1. 각 사면의 끝점(Daylight Points)들만 추출
        # add_slope가 meshio.Mesh를 반환하므로, vertices의 뒷부분 절반이 끝점들입니다.
        n_half = len(slope_l.points) // 2
        l_daylight = slope_l.points[n_half:]
        r_daylight = slope_r.points[n_half:]

        # 1. 각 사면의 끝점(Daylight Points)들 추출
        n_half_l = len(slope_l.points) // 2
        n_half_r = len(slope_r.points) // 2
        l_daylight = slope_l.points[n_half_l:]
        r_daylight = slope_r.points[n_half_r:]

        # --- 추가된 부분: 클리핑용 폴리곤 생성 ---
        # 왼쪽 끝점과 오른쪽 끝점을 역순으로 이어 붙여 닫힌 루프 생성
        poly_coords = np.concatenate([l_daylight[:, :2], r_daylight[::-1, :2]])
        from shapely.geometry import Polygon
        clipping_poly = Polygon(poly_coords)
        # ---------------------------------------

        # 2. 지형 클리핑 수행 (이제 clipping_poly를 넘겨줍니다)
        print(f"Segment {idx} 클리핑 시작...")
        clipped_terrain = clip_with_shapely_delaunay(meshes[idx - 1], clipping_poly)

        # 3. 결과 저장 (clipped_terrain 사용)
        save_obj_with_groups(f"c:/temp/obj/segment_{idx}.obj",
                             clipped_terrain.points, clipped_terrain.cells[0].data,
                             track_vertices, track_faces, slope_l, slope_r)

        print(f"트랙 병합 저장 완료: track_part_{idx}.obj")
    strm.close()  # ✅ 프로그램 종료 직전에 닫기
    # 구간별 Shapefile 저장
    print('구간별 Shapefile 저장')
    save_shp(segments)
    print('구간별 QML 생성')
    save_qml(segments)

    elapsed = time.time() - start_time
    print(f'작업 완료: {elapsed}')

if __name__ == '__main__':
    main()


