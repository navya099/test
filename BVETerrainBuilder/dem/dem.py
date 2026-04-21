from coordinate_utils import convert_coordinates
from srtm30 import SrtmDEM30
from rasterio.merge import merge

class DEMProcessor:
    """DEM 처리 클래스"""
    def __init__(self, coords):
        self.strm = SrtmDEM30(coords)

    def close(self):
        """DEM 닫기"""
        self.strm.close()

    def extract_by_segments(self, segments):
        """전체 세그먼트 처리"""
        results = []
        for idx, segment in enumerate(segments, start=1):
            mosaic, out_transform = self.extract_segment(segment)
            if mosaic is None:
                print(f"Segment {idx}: DEM 없음, 건너뜀")
                continue
            results.append((idx, mosaic, out_transform))
        return results

    def extract_segment(self, segment):
        """세그먼트별 DEM 추출"""
        minx, miny, maxx, maxy = segment
        bounds_4326 = convert_coordinates([(minx, miny), (maxx, maxy)], 5186, 4326)
        minx, miny = bounds_4326[0]
        maxx, maxy = bounds_4326[1]

        datasets = self.strm.selected_datasets
        if not datasets:
            return None, None
        mosaic, out_transform = merge(datasets, bounds=(minx, miny, maxx, maxy))
        return mosaic, out_transform