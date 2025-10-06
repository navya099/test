import os
import xml.etree.ElementTree as ET
from tkinter.filedialog import askopenfilename
from simplekml import Kml
import rasterio
import glob

# ===== CONFIG =====
input_kml = askopenfilename(title="txt 파일 선택")
input_folder = os.path.dirname(input_kml)
output_kml = os.path.join(input_folder, 'elevation.txt')
dem_folder = r"D:\도면\DEM\stm30m"  # DEM 폴더

# DEM 파일명 패턴으로 타일만 선택
dem_files = glob.glob(dem_folder + r"\n*_e*_1arc_v3*.tif")

if not dem_files:
    raise ValueError("DEM 타일을 찾을 수 없습니다.")

#step 파일읽기
def read_cooridnates(input_kml):
    with open(input_kml, encoding="utf-8") as f:
        lines = f.readline()
    return lines

#step1 txt파싱
def parse_coordinates(lines):
    coords = []
    for line in lines:
        try:
            x = lines.split(',')[0]
            y = lines.split(',')[1]
            coords.append((x, y))
        except IndexError:
            pass
    return coords


# ===== STEP 2: KML 범위 계산 후 해당 타일만 선택 =====
lines = read_cooridnates(input_kml)
coords = parse_coordinates(lines)

#좌표게 변환 epsg 5187 -> wgs94

min_lon = min(lon for lon, lat in coords)
max_lon = max(lon for lon, lat in coords)
min_lat = min(lat for lon, lat in coords)
max_lat = max(lat for lon, lat in coords)

selected_files = []
for f in dem_files:
    name = f.split("\\")[-1]
    try:
        lat_tile = int(name[1:3])
        lon_tile = int(name[5:8])
    except ValueError:
        continue  # 파일명 형식 안 맞으면 무시
    # KML 범위에 포함되거나 주변 1도 버퍼 포함
    if min_lat-1 <= lat_tile <= max_lat+1 and min_lon-1 <= lon_tile <= max_lon+1:
        selected_files.append(f)

if not selected_files:
    raise ValueError("KML 범위에 맞는 DEM 파일을 찾을 수 없습니다.")

print(f"선택된 DEM 타일 수: {len(selected_files)}")

# ===== STEP 3: 좌표별 고도 추출 =====
def get_elevation(lon, lat):
    """KML 좌표별로 범위에 맞는 DEM 타일에서 고도 추출"""
    for f in selected_files:
        with rasterio.open(f) as ds:
            if ds.bounds.left <= lon <= ds.bounds.right and ds.bounds.bottom <= lat <= ds.bounds.top:
                row, col = ds.index(lon, lat)
                return float(ds.read(1)[row, col])
    return 0  # DEM 범위 밖이면 0 처리

elevations = [get_elevation(lon, lat) for lon, lat in coords]

# ===== STEP 4: 새 KML 생성 =====
kml = Kml()
linestring = kml.newlinestring(name="Track with Elevation")
linestring.coords = [(lon, lat, ele) for (lon, lat), ele in zip(coords, elevations)]
linestring.altitudemode = 'absolute'
kml.save(output_kml)

print(f"KML 저장 완료: {output_kml}")
