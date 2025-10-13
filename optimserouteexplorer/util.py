# ===== DEM 표고 샘플러 =====
import pyproj
import random
from srtm30 import SrtmDEM30
import math
import numpy as np

def sample_elevations(route_coords):
    lonlat_list = [(b, a) for a, b in route_coords]
    dem = SrtmDEM30(lonlat_list)
    return dem.get_elevations()

# ===== 유틸 =====
def haversine(a, b):
    R = 6371000

    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    c = 2 * math.asin(math.sqrt(math.sin(dlat / 2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon / 2)**2))
    return R * c

def route_length(coords):
    return sum(haversine(coords[i], coords[i+1]) for i in range(len(coords)-1))

#start region 신설구간
def calculate_angle(p1, p2):
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    return math.atan2(dy, dx)

def calculate_bearing(x1, y1, x2, y2):
    # Calculate the bearing (direction) between two points in Cartesian coordinates
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.degrees(math.atan2(dy, dx))
    return bearing

def calculate_distance(x1, y1, x2, y2):
    # Calculate the distance between two points in Cartesian coordinates
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    distance_x = abs(x2 - x1)
    distance_y = abs(y2 - y1)
    return distance

def calculate_destination_coordinates(x1, y1, bearing, distance):
    # Calculate the destination coordinates given a starting point, bearing, and distance in Cartesian coordinates
    angle = math.radians(bearing)
    x2 = x1 + distance * math.cos(angle)
    y2 = y1 + distance * math.sin(angle)
    return x2, y2

def find_direction(start_point, end_point, center_point):
    """
    세 점(시작점, 끝점, 원의 중심점)으로 방향(시계/반시계)을 판정
    Args:
        start_point: (x1, y1)
        end_point: (x2, y2)
        center_point: (xc, yc)
    Returns:
        1  → 시계방향
        -1 → 반시계방향
        0  → 일직선 또는 오류
    """

    x1, y1 = start_point
    x2, y2 = end_point
    xc, yc = center_point

    # 벡터 계산 (중심 → 시작, 중심 → 끝)
    v1x = x1 - xc
    v1y = y1 - yc
    v2x = x2 - xc
    v2y = y2 - yc

    # 외적 계산
    cross = v1x * v2y - v1y * v2x

    # 내적 (혹시 필요 시)
    dot = v1x * v2x + v1y * v2y

    # 반경이 거의 0이거나 동일점일 때 안전처리
    if abs(v1x) < 1e-9 and abs(v1y) < 1e-9:
        return 0
    if abs(v2x) < 1e-9 and abs(v2y) < 1e-9:
        return 0

    # cross 부호로 회전방향 결정
    if cross < 0:
        return 1   # 시계방향
    elif cross > 0:
        return -1  # 반시계방향
    else:
        return 0   # 일직선

def is_approximately_equal(a, b, tolerance=1e-5):
    return abs(a - b) < tolerance

def draw_arc(direction: int, start_point, end_point, center_point, num_points=100):
    """
    중심점과 시작/끝점, 방향에 따라 '작은 원호' 좌표 생성
    direction: 1=시계, 0=반시계
    start_point, end_point, center_point: shapely Point 또는 (x, y)
    """
    def unpack_point(pt):
        if hasattr(pt, "coords"):
            return pt.coords[0]
        return pt

    x_start, y_start = unpack_point(start_point)
    x_end, y_end = unpack_point(end_point)
    x_center, y_center = unpack_point(center_point)

    # 시작/끝 각도 계산 (라디안)

    start_angle = np.arctan2(y_start - y_center, x_start - x_center)
    end_angle = np.arctan2(y_end - y_center, x_end - x_center)

    # 방향 판정 (벡터 외적)
    v1 = np.array([x_start - x_center, y_start - y_center])
    v2 = np.array([x_end - x_center, y_end - y_center])
    cross = np.cross(v1, v2)

    # 반시계방향(positive cross)일 때 direction=0, 시계=1로 가정
    if direction == 1:  # 시계 방향
        if cross > 0:
            end_angle -= 2 * np.pi
    else:  # 반시계 방향
        if cross < 0:
            end_angle += 2 * np.pi

    # 각도 보정: 항상 작은 원호만 그리도록
    delta = end_angle - start_angle
    if abs(delta) > np.pi:
        # 너무 긴 호면 반대로 회전
        if direction == 1:
            end_angle += 2 * np.pi
        else:
            end_angle -= 2 * np.pi

    # 각도 배열 생성
    angles = np.linspace(start_angle, end_angle, num_points)
    radius = np.hypot(x_start - x_center, y_start - y_center)

    # 좌표 계산
    x_arc = x_center + radius * np.cos(angles)
    y_arc = y_center + radius * np.sin(angles)

    return x_arc, y_arc

def calc_pl2xy(longlat):
    (long, lat) = longlat
    p1_type = pyproj.CRS.from_epsg(4326)
    p2_type = pyproj.CRS.from_epsg(5186)
    transformer = pyproj.Transformer.from_crs(p1_type, p2_type, always_xy=True)
    x, y = transformer.transform(long, lat)

    return x, y  # [m]

def calc_pl2xy_array(coords_array):
    transformed_coords = []

    # Define CRS
    p1_type = pyproj.CRS.from_epsg(5186)  # TM
    p2_type = pyproj.CRS.from_epsg(4326)  # 위도

    # Create transformer
    transformer = pyproj.Transformer.from_crs(p1_type, p2_type, always_xy=True)

    # Iterate over each coordinate tuple in the array
    for coords in coords_array:
        # Unpack array into x and y coordinates
        x, y = coords[0], coords[1]

        # Transform coordinates
        x, y = transformer.transform(x, y)

        # Append transformed coordinates to the result array
        transformed_coords.append((x, y))
    return transformed_coords  # [m]

def adjust_radius_by_angle(ia, min_radius: int = 3100, max_radius: int = 20000):
    # 교각이 작을수록 반경을 크게, 교각이 클수록 반경을 작게 설정
    while 1:
        if ia < 3:
            new_radius = get_random_radius(min_radius * 2, max_radius)  # 교각이 1도일 때 반경을 크게
        else:
            new_radius = get_random_radius(min_radius, int(max_radius / 2))  # 교각이 30도 이상일 때 반경을 작게

        if new_radius > 0:
            break

    return new_radius


def get_random_radius(min_radius, max_radius):
    # min_radius와 max_radius 사이의 가장 작은 1000의 배수 구하기
    start = (min_radius + 1000) // 1000 * 1000
    end = (max_radius // 1000) * 1000

    if start > end:
        raise ValueError("min_radius와 max_radius 사이에 유효한 1000의 배수가 없습니다.")

    # start와 end 사이의 1000의 배수 목록 생성
    multiples_of_1000 = list(range(start, end + 1000, 1000))

    # 랜덤하게 선택

    return random.choice(multiples_of_1000)