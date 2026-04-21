from shapely import Point

class CoordinateProcessor:
    """좌표처리 클래스"""
    def __init__(self):
        self.coords = None

    def sample(self, read_coords):
        """좌표 샘플링"""
        xy_list = self.sampling_coords(read_coords, 2000)
        xyz_list = self.sampling_coords_with_z(read_coords, 2000)
        return xy_list, xyz_list

    def sampling_coords(self, coords: list, distance_m: int, base_interval_m: int = 25):
        """
        coords: [(x,y,z), ...] EPSG:5186 좌표 (미터 단위)
        distance_m: 샘플링 간격 (미터)
        base_interval_m: 원본 좌표 간격 (기본값 25m)
        """
        step = distance_m // base_interval_m  # 인덱스 간격 계산
        return [(x, y) for i, (x, y, z) in enumerate(coords) if i % step == 0]

    def sampling_coords_with_z(self, coords: list, distance_m: int, base_interval_m: int = 25):
        """
        coords: [(x,y,z), ...] EPSG:5186 좌표 (미터 단위)
        distance_m: 샘플링 간격 (미터)
        base_interval_m: 원본 좌표 간격 (기본값 25m)
        """
        step = distance_m // base_interval_m  # 인덱스 간격 계산
        return [(x, y, z) for i, (x, y, z) in enumerate(coords) if i % step == 0]

    def create_segments(self, xy_list, buffer_m: int):
        """구간 분할 설정"""
        segments = []
        for idx, (x, y) in enumerate(xy_list, start=1):

            point = Point(x, y)  # 샘플링된 점 자체를 중심점으로 사용
            buffered = point.buffer(buffer_m)  # 좌우 1km 버퍼
            segments.append(buffered.bounds)

        return segments

    @staticmethod
    def filter_coords_by_segment(coords, segment_bounds):
        """구간 bounding box 안에 포함되는 좌표만 추출"""
        minx, miny, maxx, maxy = segment_bounds
        return [(x, y, z) for (x, y, z) in coords if minx <= x <= maxx and miny <= y <= maxy]