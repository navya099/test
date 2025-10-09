import base64
from dataclasses import field, dataclass
import io
import folium
import json
import numpy as np
import math
import random

import pyproj
from shapely.geometry.linestring import LineString
from shapely.geometry.point import Point
from srtm30 import SrtmDEM30


# ===== Alignment 객체 =====
@dataclass
class Alignment:
    coords: list = field(default_factory=list)
    elevations: list = field(default_factory=list)
    grounds: list = field(default_factory=list)
    fls: list = field(default_factory=list)
    bridges: dict = field(default_factory=dict)  # key: segment idx, value: 튜플(start,end)
    tunnels: dict = field(default_factory=dict)
    cost: float = 0.0
    radius: list = field(default_factory=list)
    grades: list = field(default_factory=list)

    @property
    def length(self):
        return route_length(self.coords)

    @property
    def bridge_count(self):
        return len(self.bridges)

    @property
    def tunnel_count(self):
        return len(self.tunnels)

    @property
    def total_bridge_length(self):
        return sum([sum(haversine(self.coords[i], self.coords[i + 1]) for i in range(s, e))
                    for s, e in self.bridges.values()])

    @property
    def total_tunnel_length(self):
        return sum([sum(haversine(self.coords[i], self.coords[i + 1]) for i in range(s, e))
                    for s, e in self.tunnels.values()])

    @property
    def radius_count(self):
        return len(self.radius)

    @property
    def grades_count(self):
        return len(self.grades)

    @property
    def max_grade(self):
        return max(self.grades)

    @property
    def min_radius(self):
        return min(self.radius)


# ===== DEM 표고 샘플러 =====
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
    c = 2 * math.asin(math.sqrt(math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2))
    return R * c


def route_length(coords):
    return sum(haversine(coords[i], coords[i + 1]) for i in range(len(coords) - 1))


# start region 신설구간
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
    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
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
        return 1  # 시계방향
    elif cross > 0:
        return -1  # 반시계방향
    else:
        return 0  # 일직선


def calculate_O_PC_angle(v10, x10, direction):
    '''
    # Example usage
    v10 = 방위각1
    x10 = PC점의 점선각
    w13 = R
    '''
    if direction > 0:
        if v10 + x10 - 90 < 0:
            result = v10 + x10 - 90 + 360
        else:
            result = v10 + x10 - 90
    else:
        if v10 - x10 + 90 > 360:
            result = v10 - x10 + 90 - 360
        else:
            result = v10 - x10 + 90
    return result


class RandomLineStringCreator:
    """
    랜덤 LineString객체 생성 클래스
    Attributes:
        linestring: LineString
    """

    def __init__(self):
        self.linestring = None

    def generate_random_linestring(self, start: Point, end: Point, num_max_point: int = 100,
                                   min_distance: float = 3000, max_distance: float = 5000,
                                   min_end_distance: float = 2000):
        """
        랜덤 LineString객체 생성 메소드
        Arguments:
            start: 시작 점 Point
            end: 끝점 Point
            num_max_point: 생성할 점 갯수
            min_distance: 점 사이의 최소 거리
            max_distance: 점 사이의 최대 거리
            min_end_distance: 끝점과 마지막점의 최소거리
        """
        points = [start]
        while True:
            if len(points) >= num_max_point:  # 최댓수를 넘으면 종료
                break
            new_point = self._generate_random_point_near(points[-1], end, min_distance, max_distance)
            if new_point.distance(points[-1]) <= max_distance:  # 점과 마지막점의 거리가 점 사이의 최대 거리보다 작은경우
                points.append(new_point)
            if new_point.distance(end) <= min_end_distance:  # 점과 끝점의 거리가 끝점과 마지막점의 최소거리보다 작은경우
                break
        points.append(end)
        self.linestring = LineString(points)

    def _generate_random_point_near(self, point: Point, end: Point,
                                    min_distance: float,
                                    max_distance: float
                                    ):
        """
        private  메소드
        기준점에서 랜덤 점 생성 메소드
        Arguments:
            point: 기준 점 Point
            end: 끝점 Point
            min_distance: 점 사이의 최소 거리
            max_distance: 점 사이의 최대 거리
        Returns:
            Point
        """
        # 끝점 각도 계산
        angle_to_end = calculate_angle(point, end)
        while True:
            angle = random.uniform(angle_to_end - math.radians(90), angle_to_end + math.radians(90))
            distance = random.uniform(min_distance, max_distance)
            x = point.x + distance * math.cos(angle)
            y = point.y + distance * math.sin(angle)

            new_point = Point(x, y)

            # Check if the new point is in the direction of the end point
            if new_point.distance(end) < point.distance(end):
                return new_point


class LineStringProcessor:
    """
    LineString객체 처리용 클래스
    Attributes:
        linestring: LineString
        angles: LineString 내부 각도 리스트
    """

    def __init__(self, linestring: LineString):
        self.linestring = linestring
        self.angles: list[float] = []

    def process_linestring(self):
        """
        LineString객체 처리용 메소드
        각도 산출 후 조정 후 변경 LineString로 수정
        """
        self._calculate_angles()
        self._adjust_linestring()
        self._calculate_angles()

    def _adjust_linestring(self, tolerance: float = 60):
        """
        private 메소드
        LineString객체를 각도 조정
        Args:
            tolerance: 임계각도
        """
        new_points = [self.linestring.coords[0]]  # Start with the first point
        for i in range(1, len(self.linestring.coords) - 1):
            if self.angles[i - 1] <= tolerance:  # tolerance 임계값보다 작으면
                new_points.append(self.linestring.coords[i])
        new_points.append(self.linestring.coords[-1])  # End with the last point
        self.linestring = LineString(new_points)

    def _calculate_angles(self):
        """
        LineString 객체 내부 각도 계산 (간결한 버전, numpy 사용)
        """
        coords = np.array(self.linestring.coords)
        # 이전 벡터와 다음 벡터 계산
        vectors_prev = coords[1:-1] - coords[:-2]  # P[i] - P[i-1]
        vectors_next = coords[2:] - coords[1:-1]  # P[i+1] - P[i]

        # 벡터 길이 계산 (0인 경우 방지)
        norms_prev = np.linalg.norm(vectors_prev, axis=1)
        norms_next = np.linalg.norm(vectors_next, axis=1)
        valid = (norms_prev > 0) & (norms_next > 0)

        # 내적을 통한 각도 계산
        dot_products = np.einsum('ij,ij->i', vectors_prev[valid], vectors_next[valid])
        cos_angles = dot_products / (norms_prev[valid] * norms_next[valid])
        cos_angles = np.clip(cos_angles, -1.0, 1.0)  # 부동소수점 오차 방지
        angles = np.degrees(np.arccos(cos_angles))

        self.angles = angles.tolist()

    def create_joined_line_and_arc_linestirng(self,
                                              start_points: list[Point],
                                              end_points: list[Point],
                                              center_points: list[Point],
                                              direction_list: list[int]):
        """
        public 메소드
        선과 호를 이어서 새로운 linestring생성
        Args:
            start_points: 호의 시작 좌표 리스트
            end_points: 호의 끝 좌표 리스트
            center_points: 호의 중심 좌표 리스트
            direction_list: 각 호의 방향 리스트(1,0, -1)
        """
        # 호 리스트 생성
        acr1, acr2 = [], []
        for i in range(len(start_points)):
            x_arc, y_arc = draw_arc(direction_list[i], start_points[i], end_points[i], center_points[i])
            acr1.append(x_arc)
            acr2.append(y_arc)

        acr1 = [item for sublist in acr1 for item in sublist]
        acr2 = [item for sublist in acr2 for item in sublist]
        curve_coords = list(zip(acr1, acr2))
        combined_coords = [self.linestring.coords[0]] + curve_coords + [self.linestring.coords[-1]]
        new_linestring = LineString(combined_coords)

        self.linestring = new_linestring


@dataclass
class CurveSegment:
    bc_coord: Point
    ec_coord: Point
    center_coord: Point
    direction: int
    bc_sta: float
    ec_sta: float
    cl: float
    tl: float


class CurveAdjuster:
    """
    LineString 기반 곡선(IP, BC, EC, EP) 반경 조정 및 배치 관리 클래스
    """

    def __init__(self, linestring, angles: list[float], radius_list: list[float]):
        self.linestring = linestring
        self.angles = angles
        self.radius_list = radius_list
        self.segments: list[CurveSegment] = []

    def main_loop(self, min_arc_to_arc_distance: float = 2000, max_iterations: int = 200, min_radius: float = 600):
        """
        곡선 반경 반복 조정
        """
        for j in range(max_iterations):
            self.segments = self._calculate_segments()
            ep_sta = self.cal_ep_sta()

            overlaps = self._check_overlaps(min_arc_to_arc_distance, ep_sta, min_radius)

            if not any(overlaps):
                print(f'루프 {j}회차 종료: 곡선 조정 완료')
                break
        else:
            print(f'루프 {max_iterations}회차 종료: 곡선반경 조정 실패')

    def _calculate_segments(self) -> list[CurveSegment]:
        """
        각 IP 단위로 CurveSegment 계산
        """
        segments: list[CurveSegment] = []
        tl_list, cl_list = [], []

        for i in range(len(self.linestring.coords) - 2):
            ia = math.radians(self.angles[i])
            cl = self.radius_list[i] * ia
            tl = self.radius_list[i] * math.tan(ia / 2)
            tl_list.append(tl)
            cl_list.append(cl)

            bp_coord = self.linestring.coords[i]
            ip_coord = self.linestring.coords[i + 1]
            ep_coord = self.linestring.coords[i + 2]

            bp_ip_bearing = calculate_bearing(*bp_coord, *ip_coord)
            ip_ep_bearing = calculate_bearing(*ip_coord, *ep_coord)
            bp_ip_distance = calculate_distance(*bp_coord, *ip_coord)

            # IP_STA 계산
            ip_sta = bp_ip_distance if i == 0 else segments[i - 1].ec_sta + bp_ip_distance - tl_list[i - 1]

            bc_coord = calculate_destination_coordinates(*ip_coord, bp_ip_bearing, -tl)
            ec_coord = calculate_destination_coordinates(*ip_coord, ip_ep_bearing, tl)
            direction = find_direction(bp_coord, ip_coord, ep_coord)

            center_coord = self.calculate_curve_center(Point(bc_coord), Point(ec_coord), self.radius_list[i], direction)

            segments.append(CurveSegment(
                bc_coord=Point(bc_coord),
                ec_coord=Point(ec_coord),
                center_coord=Point(center_coord),
                direction=direction,
                bc_sta=ip_sta - tl,
                ec_sta=ip_sta - tl + cl,
                cl=cl,
                tl=tl
            ))

        return segments

    def cal_ep_sta(self) -> float:
        """
        마지막 EP_STA 계산
        """
        last_segment = self.segments[-1]
        ep_coord = self.linestring.coords[-1]
        ec_ep_dist = calculate_distance(last_segment.ec_coord.x, last_segment.ec_coord.y, *ep_coord)
        return last_segment.ec_sta + ec_ep_dist

    def _check_overlaps(self, min_distance: float, ep_sta: float, min_radius: float) -> list[bool]:
        """
        각 segment의 BC-EC 거리 및 마지막 EP 체크, 필요시 radius 조정
        """
        overlaps = []
        n = len(self.segments)

        for i, seg in enumerate(self.segments):
            # 다음 BC까지 거리 계산
            if i < n - 1:
                bc_to_next_bc = self.segments[i + 1].bc_sta - seg.ec_sta
            else:
                bc_to_next_bc = ep_sta - seg.ec_sta

            # 거리 미만이면 radius 조정
            if i == 0 and seg.bc_sta < min_distance:
                self.radius_list[0] = self.adjust_radius(0, min_radius=min_radius)
                overlaps.append(True)
            elif bc_to_next_bc < min_distance:
                max_idx = self._find_max_radius_index(i)
                self.radius_list[max_idx] = self.adjust_radius(max_idx, min_radius=min_radius)
                overlaps.append(True)
            else:
                overlaps.append(False)

        # 마지막 IP-EP 체크
        if not is_approximately_equal(
                calculate_bearing(self.segments[-1].ec_coord.x, self.segments[-1].ec_coord.y,
                                  *self.linestring.coords[-1]),
                calculate_bearing(self.segments[-1].ec_coord.x, self.segments[-1].ec_coord.y,
                                  *self.linestring.coords[-1])
        ):
            self.radius_list[-1] = self.adjust_radius(-1, min_radius=min_radius)
            overlaps[-1] = True

        return overlaps

    def adjust_radius(self, index: int, decrement: int = 500, min_radius: float = 600) -> float:
        """
        radius 조정
        """
        self.radius_list[index] = max(self.radius_list[index] - decrement, min_radius)
        return self.radius_list[index]

    def _find_max_radius_index(self, i: int) -> int:
        """
        현재와 주변 segment 중 최대 radius index 반환
        """
        n = len(self.radius_list)
        idx_list = [i]
        if i > 0:
            idx_list.append(i - 1)
        if i < n - 1:
            idx_list.append(i + 1)
        max_idx = max(idx_list, key=lambda idx: self.radius_list[idx])
        return max_idx

    def calculate_curve_center(self, bc_xy: Point, ec_xy: Point,
                               radius: float, direction) -> Point:
        """
        BC, EC와 반지름 R이 주어졌을 때 원의 중심을 계산.
        (즉, BC와 EC에서 거리 R인 점들(두 교점) 중 direction에 맞는 쪽을 선택)
        """
        dx = ec_xy.x - bc_xy.x
        dy = ec_xy.y - bc_xy.y
        d = math.hypot(dx, dy)

        if d == 0:
            raise ValueError("BC and EC are identical points")
        # 두 점 사이 거리가 2R보다 크면 반지름 R로 두 점을 지나는 원이 없음
        if d > 2.0 * radius + 1e-9:
            raise ValueError("No circle with given radius passes through both BC and EC")

        # 중점
        mx = (bc_xy.x + ec_xy.x) / 2.0
        my = (bc_xy.y + ec_xy.y) / 2.0

        # 반(현) 길이와 높이(h)
        a = d / 2.0
        h = math.sqrt(max(0.0, radius * radius - a * a))

        # chord의 단위 수직벡터 (두 교점은 중점 ± h * (ux,uy))
        ux = -dy / d
        uy = dx / d

        c1x = mx + ux * h
        c1y = my + uy * h
        c2x = mx - ux * h
        c2y = my - uy * h

        # 각 후보에 대해 BC→EC의 중심각(끝-시작)을 계산하여 부호로 좌/우 판별
        def signed_delta_theta(cx, cy):
            phi0 = math.atan2(bc_xy.y - cy, bc_xy.x - cx)
            phi1 = math.atan2(ec_xy.y - cy, ec_xy.x - cx)
            # 정상화된 중심각 (-pi..pi)
            return math.atan2(math.sin(phi1 - phi0), math.cos(phi1 - phi0))

        d1 = signed_delta_theta(c1x, c1y)
        d2 = signed_delta_theta(c2x, c2y)

        # 방향에 맞게 선택: RIGHT -> 중심각이 음수(시계, 우회전)인 후보 선택
        if direction == 1:
            chosen_x, chosen_y = (c1x, c1y) if d1 < 0 else (c2x, c2y)
        else:  # LEFT
            chosen_x, chosen_y = (c1x, c1y) if d1 > 0 else (c2x, c2y)

        return Point(chosen_x, chosen_y)


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


# end region

def generate_longitudinal(num_points=100, min_distance=600, gl=None, chain=40):
    if gl is None:
        gl = []
    profile = generate_random_profile(num_points, min_distance, gl, chain)
    fixed_profile = check_and_adjust_elevation(profile)
    elevations = generate_station_elv(fixed_profile, gl)
    return [elevation for station, elevation in elevations], fixed_profile


def generate_station_elv(fl, gl):
    """
    계획고 지점(points) 사이를 spline 지반고를 따라 샘플링하여 선형 보간
    Args:
        fl: 계획고 주요지점 (예: [[0,110],[500,120],...])
        gl: 지반고 (예: [[0,100],[100,102],[200,103],...])
    Returns:
        station_elv: [[station, elevation], ...]
    """
    fl_stations = [s for s, _ in fl]
    fl_elevations = [e for _, e in fl]

    station_elv = []
    for sta, elev in gl:
        current_fl = np.interp(sta, fl_stations, fl_elevations)
        station_elv.append([sta, current_fl])

    return station_elv


def generate_random_profile(num_points, min_distance, gl, chain=40):
    """
    spline 기반 경로에서도 사용 가능하도록
    station 값이 정확히 일치하지 않아도 선형보간으로 지반고를 추정합니다.
    """
    # gl을 분리
    gl_stations = [s for s, _ in gl]
    gl_elevations = [e for _, e in gl]

    # 초기 설정
    start_station, start_elevation = gl[0]
    end_station, end_elevation = gl[-1]
    points = [[start_station, start_elevation + 10]]

    current_station = start_station
    current_elevation = start_elevation + 10

    for i in range(num_points - 1):
        distance_to_next = chain * math.ceil(random.uniform(min_distance, min_distance * 2) / chain)

        if current_station + distance_to_next >= end_station:
            break

        next_station = current_station + distance_to_next

        # 🔹 지반고를 선형보간으로 추정
        next_elevation = np.interp(next_station, gl_stations, gl_elevations) + 10

        current_station = next_station
        current_elevation = next_elevation
        points.append([current_station, current_elevation])

    points.append([end_station, end_elevation + 10])
    return points


def check_and_adjust_elevation(profile):
    adjusted_profile = []
    for i, (station, elevation) in enumerate(profile):
        rand_el = random.uniform(0, 20)

        if i > 0:
            prev_station, prev_elevation = adjusted_profile[-1]
            if abs(elevation - prev_elevation) > 20:
                elevation = prev_elevation + (rand_el if elevation > prev_elevation else -rand_el)
        adjusted_profile.append([station, elevation])

    return adjusted_profile


# ===== 종단 + 구조물 + 비용 평가 =====
def evaluate_longitudinal(coords, elevs, ground):
    dz = np.array(elevs) - np.array(ground)
    ds = np.array([haversine(coords[i], coords[i + 1]) for i in range(len(coords) - 1)])
    slope = np.abs(dz[:-1] / (ds + 1e-9))
    mean_slope = np.mean(slope)

    bridges, tunnels = {}, {}
    start_idx = 0
    while start_idx < len(dz) - 1:
        current_sign = np.sign(dz[start_idx])
        end_idx = start_idx
        while end_idx < len(dz) - 1 and np.sign(dz[end_idx]) == current_sign:
            end_idx += 1
        segment_len = ds[start_idx:end_idx].sum()
        segment_height = np.max(np.abs(dz[start_idx:end_idx]))
        if current_sign > 0 and segment_height >= 15 and segment_len >= 100:
            bridges[start_idx] = (start_idx, end_idx)
        elif current_sign < 0 and segment_height >= 15 and segment_len >= 100:
            tunnels[start_idx] = (start_idx, end_idx)
        start_idx = end_idx

    # 각 구간 길이 합산
    total_bridge_length = sum([sum(ds[s:e]) for s, e in bridges.values()])
    total_tunnel_length = sum([sum(ds[s:e]) for s, e in tunnels.values()])

    cutfill_cost = np.sum(np.abs(dz) * 20.0)
    cost = route_length(
        coords) + 200 * mean_slope + 500 * total_tunnel_length + 300 * total_bridge_length + 0.01 * cutfill_cost

    return cost, bridges, tunnels


# ===== 후보 생성 및 평가 =====
def generate_and_rank(start, end, n_candidates=30, chain=40):
    alignments = []

    for i in range(n_candidates):
        print(f"현재 회차: {i + 1}")

        start_tm = calc_pl2xy((start[1], start[0]))
        end_tm = calc_pl2xy((end[1], end[0]))

        random_linestring_creator = RandomLineStringCreator()
        random_linestring_creator.generate_random_linestring(Point(start_tm), Point(end_tm))

        linestring = random_linestring_creator.linestring
        linestringprocessor = LineStringProcessor(linestring)
        linestringprocessor.process_linestring()
        linestring = linestringprocessor.linestring

        angles = linestringprocessor.angles
        radius_list = [adjust_radius_by_angle(angle, 3100, 20000) for angle in angles]

        curveadjustor = CurveAdjuster(linestring, angles, radius_list)
        curveadjustor.main_loop()
        curvelist = curveadjustor.segments

        start_points = [curve.bc_coord for curve in curvelist]
        end_points = [curve.ec_coord for curve in curvelist]
        center_points = [curve.center_coord for curve in curvelist]
        direction_list = [curve.direction for curve in curvelist]

        linestringprocessor.create_joined_line_and_arc_linestirng(
            start_points=start_points,
            end_points=end_points,
            center_points=center_points,
            direction_list=direction_list
        )
        coords = list(linestringprocessor.linestring.coords)
        coords = calc_pl2xy_array(coords)
        coords = [(y, x) for x, y in coords]
        ground_elevs = sample_elevations(coords)

        # 누적 거리(km) 계산
        distances = [0]
        for i in range(1, len(coords)):
            distances.append(distances[-1] + haversine(coords[i - 1], coords[i]) / 1000)  # km 단위

        gl = [(sta, ele) for sta, ele in zip(distances, ground_elevs)]
        min_distance = 1000
        max_vip = int(gl[-1][0] / min_distance)
        design_elevs, profile = generate_longitudinal(
            num_points=max_vip,
            min_distance=min_distance,
            gl=gl,
            chain=chain)

        cost, bridges, tunnels = evaluate_longitudinal(coords, design_elevs, ground_elevs)

        alignment = Alignment(
            coords=coords,
            elevations=design_elevs,
            grounds=ground_elevs,
            bridges=bridges,
            tunnels=tunnels,
            cost=cost,
            fls=profile
        )
        alignments.append(alignment)
    # 비용 기준 정렬
    alignments.sort(key=lambda x: x.cost)
    print("종료")
    return alignments


def visualize_routes_with_button(alignments, start, end, top_n=5, map_file="candidate_routes.html"):
    center = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2]
    m = folium.Map(location=center, zoom_start=7)
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'darkred', 'cadetblue']

    # Chart.js용 canvas
    chart_div = """
    <canvas id="profile_canvas" style="width:100%; height:300px;"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
window.profileChart = null;

function showProfile(planElevs, groundElevs, distances){
    // canvas와 실제 픽셀 크기 조정
    var canvas = document.getElementById('profile_canvas');
    canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    canvas.height = canvas.offsetHeight * window.devicePixelRatio;

    var ctx = canvas.getContext('2d');

    if(window.profileChart) window.profileChart.destroy();

    var planData = planElevs.map(([sta, elev]) => ({ x: sta, y: elev }));
    var groundData = groundElevs.map((e,i)=>({x: distances[i], y: e}));

    window.profileChart = new Chart(ctx,{
        type:'line',
        data:{datasets:[
            {label:'Plan', data:planData, borderColor:'red', fill:false},
            {label:'Ground', data:groundData, borderColor:'blue', fill:false}
        ]},
        options:{
            responsive:false,
            maintainAspectRatio:false,
            plugins:{legend:{display:true}},
            scales:{
                x:{
                    type:'linear',
                    position:'bottom',
                    title:{display:true, text:'Distance (km)'}
                },
                y:{
                    title:{display:true, text:'Elevation (m)'}
                }
            }
        }
    });
}
</script>

    """

    m.get_root().html.add_child(folium.Element(chart_div))

    for idx, alignment in enumerate(alignments[:top_n]):
        color = colors[idx % len(colors)]

        # elevations
        plan_elevs = [(sta / 1000, fl) for sta, fl in alignment.fls]
        ground_elevs = alignment.grounds

        # 누적 거리(km) 계산
        distances = [0]
        for i in range(1, len(alignment.coords)):
            distances.append(distances[-1] + haversine(alignment.coords[i - 1], alignment.coords[i]) / 1000)  # km 단위

        plan_json = json.dumps(plan_elevs)
        ground_json = json.dumps(ground_elevs)
        dist_json = json.dumps(distances)

        # 팝업 HTML
        popup_html = f"""
        ID: {idx} <br>
        Length:{alignment.length:.2f}
        Cost: {alignment.cost:.1f} <br>
        Bridge: {alignment.total_bridge_length:.1f}m <br>
        Tunnel: {alignment.total_tunnel_length:.1f}m <br>
        <button onclick='showProfile({plan_json}, {ground_json}, {dist_json})'>View Profile</button>
        """
        polyline = folium.PolyLine(
            locations=alignment.coords,
            color=color,
            weight=5,
            opacity=0.7,
        )
        polyline.add_child(folium.Popup(popup_html, max_width=300))
        polyline.add_to(m)

    folium.Marker(location=start, popup="Start", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(location=end, popup="End", icon=folium.Icon(color='red')).add_to(m)

    m.save(map_file)
    print(f"지도 시각화 파일({map_file})이 생성되었습니다.")


# 종단 그래프를 base64 이미지로 변환
def plot_profile_to_base64(elevs, gound):
    from matplotlib import pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 2))
    ax.plot(elevs, color='red')
    ax.set_xlabel("Distance")
    ax.set_ylabel("Elevation")
    ax.grid(True)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return img_base64


# ===== 실행 예시 =====
if __name__ == "__main__":
    start = (37.594240, 127.130699)
    end = (37.264456, 127.442329)
    alignments = generate_and_rank(start, end, n_candidates=30)

    for i, a in enumerate(alignments[:10]):
        print(
            f"ID:{i} Length:{a.length:.1f} Cost:{a.cost:.1f} Bridge:{a.total_bridge_length:.1f} Tunnel:{a.total_tunnel_length:.1f}")

    visualize_routes_with_button(alignments, start, end, top_n=10)
