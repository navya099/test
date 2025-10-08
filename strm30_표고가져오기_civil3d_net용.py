import os
import datetime
import pyproj
import rasterio
from rasterio.windows import Window
import glob
import time

def read_coordinates(input_txt):
    coords = []
    with open(input_txt, encoding="utf-8-sig") as f:  # BOM 자동 제거
        for i, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                x, y = map(float, stripped.split(','))
                coords.append((x, y))
            except ValueError:
                print(f"{i}번째 줄 좌표 변환 실패: '{stripped}'")
    return coords


def tm2wgs(coords_array):
    transformed = []
    p1 = pyproj.CRS.from_epsg(5186)
    p2 = pyproj.CRS.from_epsg(4326)
    transformer = pyproj.Transformer.from_crs(p1, p2, always_xy=True)
    for x, y in coords_array:
        lon, lat = transformer.transform(x, y)
        transformed.append((lon, lat))
    return transformed

def get_elevations(coords, dem_files):
    elevations = []
    datasets = [rasterio.open(f) for f in dem_files]
    for lon, lat in coords:
        ele = 0
        for ds in datasets:
            if ds.bounds.left <= lon <= ds.bounds.right and ds.bounds.bottom <= lat <= ds.bounds.top:
                row, col = ds.index(lon, lat)
                ele = float(ds.read(1, window=Window(col, row, 1, 1))[0, 0])
                break
        elevations.append(ele)
    for ds in datasets:
        ds.close()
    return elevations

def write_file(elevations, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        for ele in elevations:
            f.write(f"{ele}\n")

# ===== CONFIG =====
input_txt = 'c:/temp/Coordinates.txt'
input_folder = os.path.dirname(input_txt)
output_txt = os.path.join(input_folder, 'elevation.txt')
dem_folder = r"D:\도면\DEM\stm30m"

dem_files = glob.glob(os.path.join(dem_folder, "n*_e*_1arc_v3*.tif"))
if not dem_files:
    raise ValueError("DEM 파일을 찾을 수 없습니다.")

if not os.path.exists(input_txt):
    time.sleep(1)

start_time = datetime.datetime.now()
print(f"작업 시작 시간: {start_time}")

coords_tm = read_coordinates(input_txt)
print(len(coords_tm))
coords = tm2wgs(coords_tm)

# 최소 범위 계산
min_lon = min(lon for lon, lat in coords)
max_lon = max(lon for lon, lat in coords)
min_lat = min(lat for lon, lat in coords)
max_lat = max(lat for lon, lat in coords)

selected_files = []
for f in dem_files:
    name = os.path.basename(f)
    try:
        lat_tile = int(name[1:3])
        lon_tile = int(name[5:8])
    except ValueError:
        continue
    if min_lat-1 <= lat_tile <= max_lat+1 and min_lon-1 <= lon_tile <= max_lon+1:
        selected_files.append(f)

if not selected_files:
    raise ValueError("좌표 범위에 맞는 DEM 파일이 없습니다.")

elevations = get_elevations(coords, selected_files)
write_file(elevations, output_txt)

end_time = datetime.datetime.now()
print(f"표고파일 저장 완료: {output_txt}")
print(f"작업 완료 시간: {end_time}")
print(f"총 소요 시간: {end_time - start_time}")

