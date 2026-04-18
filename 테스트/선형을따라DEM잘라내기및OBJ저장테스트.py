import shutil
import time
from tkinter.filedialog import askopenfilename
import os
import meshio
from rasterio.merge import merge
from shapely.geometry import LineString
import numpy as np
import rasterio

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

# 좌표 읽기
file = askopenfilename()
read_coords = read_coordinates(file)

# 200m 간격 샘플링
xy_list = [(x,y) for i,(x,y,z) in enumerate(read_coords) if i % 200 == 0]

# EPSG:5186 좌표계 그대로 사용 (미터 단위)
line = LineString(xy_list)

# 구간 분할 설정
segment_length = 2000  # 10km
buffer_m = 1000         # 좌우 1km 여유

total_length = line.length
segments = []
d = 0
while d < total_length:
    point = line.interpolate(d)
    buffered = point.buffer(buffer_m)  # 미터 단위 버퍼
    segments.append(buffered.bounds)
    d += segment_length

# ✅ 마지막 구간 추가 (노선 끝점 기준)
point = line.interpolate(total_length)
buffered = point.buffer(buffer_m)
last_segment = buffered.bounds

# 폴더 초기화
shutil.rmtree("C:/temp/OBJ", ignore_errors=True)
os.makedirs("C:/temp/OBJ", exist_ok=True)

# DEM 클래스 호출 (WGS84 좌표 필요)
converterd_coord = convert_coordinates(xy_list, 5186, 4326)
strm = SrtmDEM30(converterd_coord)

start_time = time.time()

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

# ✅ 마지막 구간은 특별히 표시된 파일 이름으로 저장
minx, miny, maxx, maxy = last_segment
bounds_4326 = convert_coordinates([(minx, miny), (maxx, maxy)], 5186, 4326)
minx, miny = bounds_4326[0]
maxx, maxy = bounds_4326[1]

datasets = [rasterio.open(f) for f in strm.selected_files]
mosaic, out_transform = merge(datasets, bounds=(minx, miny, maxx, maxy))
band = mosaic[0]

# ✅ 모든 표고값에 +100 더하기
band = band + 100

save_dem_as_obj(band, out_transform, "C:/temp/OBJ/terrain_last.obj")

for ds in datasets:
    ds.close()

elapsed = time.time() - start_time
print(f"전체 완료! 총 소요시간: {elapsed:.1f}초")
