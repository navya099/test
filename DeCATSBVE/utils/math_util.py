import math
from functools import lru_cache

#전역변수
elevation_cache = {}
interpolation_cache = {}

@lru_cache(maxsize=None)
def calculate_bearing(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return math.degrees(math.atan2(dy, dx))

def calculate_curve_angle(polyline_with_sta, pos, next_pos, stagger1, stagger2 ,start=True):
    # 캐싱된 보간 사용
    point_a, P_A, vector_a = interpolate_cached(polyline_with_sta, pos)
    point_b, P_B, vector_b = interpolate_cached(polyline_with_sta, next_pos)

    if point_a and point_b:
        offset_point_a = calculate_offset_point(vector_a, point_a, stagger1)
        offset_point_b = calculate_offset_point(vector_b, point_b, stagger2)

        # bearing 계산 (캐싱 적용)
        a_b_angle = calculate_bearing(offset_point_a[0], offset_point_a[1],
                                      offset_point_b[0], offset_point_b[1])
        if start:
            return vector_a - a_b_angle
        else:
            return a_b_angle - vector_b

    return 0.0

# offset 좌표 반환
def calculate_offset_point(vector, point_a, offset_distance):
    if offset_distance > 0:  # 우측 오프셋
        vector -= 90
    else:
        vector += 90  # 좌측 오프셋
    offset_a_xy = calculate_destination_coordinates(point_a[0], point_a[1], vector, abs(offset_distance))
    return offset_a_xy

def interpolate_cached(polyline_with_sta, pos):


    if pos not in interpolation_cache:
        interpolation_cache[pos] = interpolate_coordinates(polyline_with_sta, pos)
    return interpolation_cache[pos]

def interpolate_coordinates(polyline, target_sta):
    """
    주어진 폴리선 데이터에서 특정 sta 값에 대한 좌표를 선형 보간하여 반환.

    :param polyline: [(sta, x, y, z), ...] 형식의 리스트
    :param target_sta: 찾고자 하는 sta 값
    :return: (x, y, z) 좌표 튜플
    """
    # 정렬된 리스트를 가정하고, 적절한 두 점을 찾아 선형 보간 수행
    for i in range(len(polyline) - 1):
        sta1, x1, y1, z1 = polyline[i]
        sta2, x2, y2, z2 = polyline[i + 1]
        v1 = calculate_bearing(x1, y1, x2, y2)
        # target_sta가 두 점 사이에 있는 경우 보간 수행
        if sta1 <= target_sta < sta2:
            t = abs(target_sta - sta1)
            x, y = calculate_destination_coordinates(x1, y1, v1, t)
            z = z1 + t * (z2 - z1)
            return (x, y, z), (x1, y1, z1), v1

    raise ValueError(f"target_sta {target_sta}가 polyline 범위({polyline[0][0]} ~ {polyline[-1][0]})를 벗어났습니다.")

def calculate_destination_coordinates(x1, y1, bearing, distance):
    # Calculate the destination coordinates given a starting point, bearing, and distance in Cartesian coordinates
    angle = math.radians(bearing)
    x2 = x1 + distance * math.cos(angle)
    y2 = y1 + distance * math.sin(angle)
    return x2, y2

def get_elevation_pos(pos, polyline_with_sta):
    if pos in elevation_cache:
        return elevation_cache[pos]

    # 범위 체크
    if pos < polyline_with_sta[0][0] or pos > polyline_with_sta[-1][0]:
        raise ValueError(f"pos {pos}가 polyline 범위({polyline_with_sta[0][0]} ~ {polyline_with_sta[-1][0]})를 벗어났습니다.")

    for i in range(len(polyline_with_sta) - 1):
        sta1, x1, y1, z1 = polyline_with_sta[i]
        sta2, x2, y2, z2 = polyline_with_sta[i + 1]
        L = sta2 - sta1
        L_new = pos - sta1

        if sta1 <= pos <= sta2:
            new_z = calculate_height_at_new_distance(z1, z2, L, L_new)
            elevation_cache[pos] = new_z
            return new_z

    raise ValueError(f"pos {pos}에 대한 고도 값을 찾을 수 없습니다.")

def calculate_height_at_new_distance(h1, h2, L, L_new):
    """주어진 거리 L에서의 높이 변화율을 기반으로 새로운 거리 L_new에서의 높이를 계산"""
    h3 = h1 + ((h2 - h1) / L) * L_new
    return h3

def calculate_slope(h1, h2, gauge):
    """주어진 높이 차이와 수평 거리를 바탕으로 기울기(각도) 계산"""
    slope = (h2 - h1) / gauge  # 기울기 값 (비율)
    return math.degrees(math.atan(slope))  # 아크탄젠트 적용 후 degree 변환

# 새로운 점 계산 함수
def return_new_point(x, y, L):
    A = (x, 0)  # A점 좌표
    B = (0, 0)  # 원점 B
    C = (0, y)  # C점 좌표
    theta = math.degrees(abs(math.atan(y / x)))
    D = calculate_destination_coordinates(A[0], A[1], theta, L)  # 이동한 D점 좌표
    E = B[0], B[1] + D[1]
    d1 = calculate_distance(D[0], D[1], E[0], E[1])
    d2 = calculate_distance(B[0], B[1], E[0], E[1])

    # 외적을 이용해 좌우 판별
    v_x, v_y = C[0] - B[0], C[1] - B[1]  # 선분 벡터
    w_x, w_y = A[0] - B[0], A[1] - B[1]  # 점에서 선분 시작점까지의 벡터
    cross = v_x * w_y - v_y * w_x  # 외적 계산
    sign = -1 if cross > 0 else 1

    return d1 * sign, d2

def calculate_distance(x1, y1, x2, y2):
    """두 점 (x1, y1)과 (x2, y2) 사이의 유클리드 거리 계산"""
    return math.hypot(x2 - x1, y2 - y1)  # math.sqrt((x2 - x1)**2 + (y2 - y1)**2)와 동일

def change_permile_to_degree(permile):
    """퍼밀 값을 도(degree)로 변환"""
    # 정수 또는 문자열이 들어오면 float으로 변환
    if not isinstance(permile, (int, float)):
        permile = float(permile)

    return math.degrees(math.atan(permile / 1000))  # 퍼밀을 비율로 변환 후 계산