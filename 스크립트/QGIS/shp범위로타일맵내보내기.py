import math
import requests
from PIL import Image
from io import BytesIO
import time
from qgis.core import (
    QgsProject,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem
)

# =========================
# 🔥 설정값
# =========================
zoom = 16  # 해상도 (높을수록 선명, 느림)
output_path = r"D:\BVE\루트\Railway\Object\충남선\지형"

# =========================
# 🔥 타일 좌표 변환
# =========================
def deg2num(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return xtile, ytile

# =========================
# 🔥 타일 다운로드
# =========================
def get_tile(x, y, z):
    url = f"https://xdworld.vworld.kr/2d/Satellite/service/{z}/{x}/{y}.jpeg"
    time.sleep(0.05)  # 🔥 핵심 (50ms)
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers, timeout=5)
    return Image.open(BytesIO(r.content)).convert("RGB")

# =========================
# 🔥 extent → 위경도 변환
# =========================
def extent_to_wgs84(extent, crs):
    transform = QgsCoordinateTransform(
        crs,
        QgsCoordinateReferenceSystem("EPSG:4326"),
        QgsProject.instance()
    )

    min_pt = transform.transform(extent.xMinimum(), extent.yMinimum())
    max_pt = transform.transform(extent.xMaximum(), extent.yMaximum())

    return (
        min_pt.y(), min_pt.x(),  # min_lat, min_lon
        max_pt.y(), max_pt.x()   # max_lat, max_lon
    )
def deg2num_float(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
    return x, y

# =========================
# 🔥 타일 다운로드 + 합성
# =========================
def download_and_stitch(min_lat, min_lon, max_lat, max_lon, zoom):
    tile_size = 256

    # 🔥 float tile 좌표 (핵심)
    x_min_f, y_max_f = deg2num_float(min_lat, min_lon, zoom)
    x_max_f, y_min_f = deg2num_float(max_lat, max_lon, zoom)

    # 🔥 타일 index
    x_min = int(x_min_f)
    x_max = int(x_max_f)
    y_min = int(y_min_f)
    y_max = int(y_max_f)

    # 🔥 전체 타일 이미지 생성
    width = (x_max - x_min + 1) * tile_size
    height = (y_max - y_min + 1) * tile_size
    full_img = Image.new("RGB", (width, height))

    # 🔥 타일 붙이기
    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            try:
                tile = get_tile(x, y, zoom)
                px = (x - x_min) * tile_size
                py = (y - y_min) * tile_size
                full_img.paste(tile, (px, py))
            except Exception as e:
                print(f"타일 실패: {x},{y} -> {e}")

    # =========================
    # 🔥 여기부터가 핵심 (crop)
    # =========================

    crop_x_min = int((x_min_f - x_min) * tile_size)
    crop_y_min = int((y_min_f - y_min) * tile_size)
    crop_x_max = int((x_max_f - x_min) * tile_size)
    crop_y_max = int((y_max_f - y_min) * tile_size)

    cropped = full_img.crop((crop_x_min, crop_y_min, crop_x_max, crop_y_max))

    return cropped

# =========================
# 🔥 실행
# =========================
project = QgsProject.instance()

for i in range(3,4):
    layer_name = f"segment_{i}"
    layers = project.mapLayersByName(layer_name)

    if not layers:
        print(f"{layer_name} 없음")
        continue

    layer = layers[0]
    extent = layer.extent()

    if extent.width() == 0 or extent.height() == 0:
        print(f"{layer_name} extent 오류")
        continue

    print(f"{layer_name} 처리중...")

    # 🔥 extent → 위경도
    min_lat, min_lon, max_lat, max_lon = extent_to_wgs84(extent, layer.crs())

    # 🔥 타일 다운로드 + 합성
    image = download_and_stitch(min_lat, min_lon, max_lat, max_lon, zoom)

    # 🔥 저장
    filename = f"{output_path}\\{layer_name}.png"
    image.save(filename)

    print(f"{filename} 저장 완료")
    time.sleep(1)
print("모든 파일 저장 완료")