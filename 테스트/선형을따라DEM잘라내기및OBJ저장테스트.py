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

    def add_slope(self, track_edges, dem: SrtmDEM30, slope_ratio, width=25, side="left"):
        slope_side = []
        for (x, y, z) in track_edges:
            # DEM에서 해당 좌표의 표고 추출
            long, lat = convert_coordinates([x,y], 5186, 4326) #좌표변환
            dem_z = dem.get_elevation(long, lat)  # DEM 클래스에서 제공하는 함수라고 가정
            dem_z += 100
            # 성토/절토 자동 판정
            z_dir = -slope_ratio if z > dem_z else slope_ratio

            # 좌/우 방향 벡터
            dx, dy = track_edges[-1][0] - track_edges[0][0], track_edges[-1][1] - track_edges[0][1]
            length = np.sqrt(dx ** 2 + dy ** 2)
            nx, ny = -dy / length, dx / length

            if side == "left":
                offset_vec = np.array([nx, ny, z_dir])
            else:
                offset_vec = np.array([-nx, -ny, z_dir])

            slope_side.append((x + offset_vec[0] * width,
                               y + offset_vec[1] * width,
                               z + offset_vec[2] * width))

        # 트랙 edge와 slope edge 연결
        vertices = np.array(track_edges + slope_side)
        faces = []
        n = len(track_edges)
        for i in range(n - 1):
            ti, ti_next = i, i + 1
            si, si_next = i + n, i + 1 + n
            faces.append([ti, si, ti_next])
            faces.append([si, si_next, ti_next])

        return meshio.Mesh(points=vertices,
                           cells=[("triangle", np.array(faces))])


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

        # 저장
        save_obj_with_groups(f"c:/temp/obj/segment_{idx}.obj",
                             terrain_vertices, terrain_faces,
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


