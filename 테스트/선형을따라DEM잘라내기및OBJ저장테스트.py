import shutil
import time
from tkinter.filedialog import askopenfilename
import os
import meshio
from rasterio.merge import merge
from shapely.geometry import LineString, Point
import numpy as np
import rasterio

from coordinate_utils import convert_coordinates
from srtm30 import SrtmDEM30
import geopandas as gpd
from shapely.geometry import box

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

def extract_dem_and_obj(segments, strm: SrtmDEM30):
    # 각 구간별 DEM 추출
    for idx, (minx, miny, maxx, maxy) in enumerate(segments, start=1):
        bounds_4326 = convert_coordinates([(minx, miny), (maxx, maxy)], 5186, 4326)
        minx, miny = bounds_4326[0]
        maxx, maxy = bounds_4326[1]

        datasets = [rasterio.open(f) for f in strm.selected_files]
        mosaic, out_transform = merge(datasets, bounds=(minx, miny, maxx, maxy))
        band = mosaic[0]

        # ✅ 모든 표고값에 +100 더하기
        band = band + 100

        save_dem_as_obj(band, out_transform, f"C:/temp/OBJ/terrain_part_{idx}.obj")

        for ds in datasets:
            ds.close()

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

def main():
    # 좌표 읽기
    file = askopenfilename()
    read_coords = read_coordinates(file)
    xy_list = sampling_coords(read_coords, 2000) #1km간격 샘플링

    segments, last_segment = _create_buffered(xy_list, 1000)

    # 폴더 초기화
    shutil.rmtree("C:/temp/OBJ", ignore_errors=True)
    os.makedirs("C:/temp/OBJ", exist_ok=True)

    # DEM 클래스 호출 (WGS84 좌표 필요)
    converterd_coord = convert_coordinates(xy_list, 5186, 4326)
    strm = SrtmDEM30(converterd_coord)

    start_time = time.time()

    # 각 구간별 DEM 추출
    print('각 구간별 DEM 추출')
    extract_dem_and_obj(segments, strm)
    #구간별 Shapefile 저장
    print('구간별 Shapefile 저장')
    save_shp(segments)
    print('구간별 QML 생성')
    # 구간별 QML 생성
    save_qml(segments)
    elapsed = time.time() - start_time
    print(f'작업 완료: {elapsed}')

if __name__ == '__main__':
    main()


