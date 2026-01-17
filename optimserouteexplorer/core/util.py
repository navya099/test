# ===== DEM 표고 샘플러 =====
import pyproj
import random
from srtm30 import SrtmDEM30
import math
import numpy as np

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

def is_approximately_equal(a, b, tolerance=1e-5):
    return abs(a - b) < tolerance

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

class Vector2:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def rotate(self, cosine_of_angle, sine_of_angle):
        x_new = cosine_of_angle * self.x - sine_of_angle * self.y
        y_new = sine_of_angle * self.x + cosine_of_angle * self.y
        self.x, self.y = x_new, y_new

    def copy(self):
        return Vector2(self.x, self.y)

class Vector3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def copy(self):
        return Vector3(self.x, self.y, self.z)