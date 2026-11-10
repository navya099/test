import rasterio
import glob
import os
from rasterio.windows import Window
from collections import OrderedDict


class SrtmDEM30:
    def __init__(self, coords: list, dem_folder: str = r"D:\도면\DEM\stm30m", cache_size: int = 10):
        self.coords = coords
        self.dem_folder = dem_folder
        self.cache_size = cache_size

        # 1. 파일 경로만 수집 (Open은 나중에)
        self.dem_files = glob.glob(os.path.join(dem_folder, "n*_e*_1arc_v3*.tif"))

        # 2. 타일 인덱스 맵 생성 (Key: "N35E127", Value: file_path)
        # 파일명 파싱을 통해 O(1) 조회 가능하게 만듦
        self.tile_map = self._build_tile_map(self.dem_files)

        # 3. LRU 캐시 (최근 사용한 Dataset 객체 보관)
        self.dataset_cache = OrderedDict()

        self.min_lon = min(lon for lon, lat in self.coords)
        self.max_lon = max(lon for lon, lat in self.coords)
        self.min_lat = min(lat for lat, lon in self.coords)
        self.max_lat = max(lat for lat, lon in self.coords)

    def _build_tile_map(self, files):
        """파일명을 파싱하여 타일 좌표 맵 생성"""
        tile_map = {}
        for f in files:
            name = os.path.basename(f)
            try:
                # 예: n35_e127_1arc_v3.tif -> lat=35, lon=127
                lat = int(name[1:3])
                lon = int(name[5:8])
                tile_key = f"N{lat}E{lon}"
                tile_map[tile_key] = f
            except ValueError:
                continue
        return tile_map

    def _get_dataset(self, tile_key: str):
        """LRU 캐시를 사용하여 Dataset 객체 반환"""
        if tile_key in self.dataset_cache:
            # 캐시 히트 시 최근 사용으로 갱신
            self.dataset_cache.move_to_end(tile_key)
            return self.dataset_cache[tile_key]

        # 캐시 미스 시 파일 Open
        file_path = self.tile_map.get(tile_key)
        if not file_path:
            return None

        ds = rasterio.open(file_path)

        # 캐시 사이즈 초과 시 가장 오래된 객체 Close 및 제거
        if len(self.dataset_cache) >= self.cache_size:
            oldest_key, oldest_ds = self.dataset_cache.popitem(last=False)
            oldest_ds.close()

        self.dataset_cache[tile_key] = ds
        return ds

    def get_elevation(self, lon: float, lat: float) -> float:
        """단일 좌표의 표고 조회 (O(1) 탐색)"""
        # 1. 경도/위도로 타일 키 계산 (내림 처리)
        tile_lat = int(lat // 1)
        tile_lon = int(lon // 1)
        tile_key = f"N{tile_lat:02d}E{tile_lon:03d}"

        ds = self._get_dataset(tile_key)
        if not ds:
            return 0.0  # 데이터가 없는 해상/해외 영역

        # 2. 경계 내에 있는지 확인
        if ds.bounds.left <= lon <= ds.bounds.right and ds.bounds.bottom <= lat <= ds.bounds.top:
            row, col = ds.index(lon, lat)
            # 3. 데이터 읽기 (1x1)
            return float(ds.read(1, window=Window(col, row, 1, 1))[0, 0])

        return 0.0

    def get_elevations(self, coords=None) -> list:
        """여러 좌표의 표고 일괄 조회 (캐싱 효과 극대화)"""
        target_coords = coords if coords else self.coords
        elevations = []

        for lon, lat in target_coords:
            elevations.append(self.get_elevation(lon, lat))

        return elevations

    def close(self):
        """사용한 모든 Dataset 객체 닫기"""
        for ds in self.dataset_cache.values():
            ds.close()
        self.dataset_cache.clear()