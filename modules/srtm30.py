import rasterio
import glob
from rasterio.windows import Window

class SrtmDEM30:
    def __init__(self, coords: list):
        self.selected_files = []
        self.max_lat = 0.0
        self.min_lat = 0.0
        self.max_lon = 0.0
        self.min_lon = 0.0
        self.dem_folder = r"D:\도면\DEM\stm30m"
        self.dem_files = glob.glob(self.dem_folder + r"\n*_e*_1arc_v3*.tif")
        self.coords = coords
        self._init()

    #초기화 메소드
    def _init(self):
        """초기화 메소드"""
        self._find_boundary()
        self._set_selected_files()

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
        datasets = [rasterio.open(f) for f in self.dem_files]
        for lon, lat in self.coords:
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

    def get_elevation(self, lon, lat):
        """단일 표고 반환용 API"""
        datasets = [rasterio.open(f) for f in self.dem_files]
        ele = 0
        for ds in datasets:
            if ds.bounds.left <= lon <= ds.bounds.right and ds.bounds.bottom <= lat <= ds.bounds.top:
                row, col = ds.index(lon, lat)
                ele = float(ds.read(1, window=Window(col, row, 1, 1))[0, 0])
                break
        for ds in datasets:
            ds.close()
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
        print(f"선택된 DEM 타일 수: {len(selected_files)}")
        self.selected_files = selected_files
        if not selected_files:
            raise ValueError("KML 범위에 맞는 DEM 파일을 찾을 수 없습니다.")
