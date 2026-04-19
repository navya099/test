import math
import requests
import os

# 위도/경도를 타일 좌표로 변환
def lonlat_to_tile(lon, lat, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return x, y

# 타일 다운로드
def download_tile(z, x, y, folder="tiles"):
    url = f"http://xdworld.vworld.kr:8080/2d/Satellite/service/{z}/{x}/{y}.jpeg"
    os.makedirs(folder, exist_ok=True)
    path = f"{folder}/tile_{z}_{x}_{y}.jpg"
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(path, "wb") as f:
            f.write(r.content)
        print("Saved:", path)
        return path
    else:
        print("Failed:", url, r.status_code)
        return None

# 범위 내 모든 타일 다운로드
def download_tiles_for_bounds(min_lon, min_lat, max_lon, max_lat, zoom, folder="tiles"):
    x_min, y_max = lonlat_to_tile(min_lon, min_lat, zoom)
    x_max, y_min = lonlat_to_tile(max_lon, max_lat, zoom)

    tile_paths = []
    for x in range(x_min, x_max+1):
        for y in range(y_min, y_max+1):
            path = download_tile(zoom, x, y, folder)
            if path:
                tile_paths.append(path)
    return tile_paths


from PIL import Image
import os


def merge_tiles(tile_paths, output_path="merged.jpg"):
    # 타일 크기 (VWorld도 256x256 픽셀)
    tile_size = 256

    # 파일명에서 x,y 추출
    coords = []
    for path in tile_paths:
        fname = os.path.basename(path)
        parts = fname.replace(".jpg", "").split("_")
        z, x, y = int(parts[1]), int(parts[2]), int(parts[3])
        coords.append((x, y, path))

    # x,y 범위 확인
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    cols = max_x - min_x + 1
    rows = max_y - min_y + 1

    # 새 이미지 생성
    merged = Image.new("RGB", (cols * tile_size, rows * tile_size))

    # 타일 붙이기
    for x, y, path in coords:
        img = Image.open(path)
        px = (x - min_x) * tile_size
        py = (y - min_y) * tile_size
        merged.paste(img, (px, py))

    merged.save(output_path)
    print("병합 완료:", output_path)
    return output_path



# ✅ 테스트 실행 (예: 인천광역시 주변 2km × 2km 범위)
min_lon, min_lat = 126.70, 37.45
max_lon, max_lat = 126.72, 37.47
zoom = 17
folder = r"c:\temp\tiles"

downloaded = download_tiles_for_bounds(min_lon, min_lat, max_lon, max_lat, zoom, folder)
print("총 다운로드 개수:", len(downloaded))

# 병합 실행
merged_file = merge_tiles(downloaded, output_path=r"c:\temp\tiles\merged.jpg")