import math
import numpy as np
from curvedirection import CurveDirection

def get_block_index(number, interval):
    return int(math.floor(number / interval + 0.001))

def get_station_by_block_index(index, interval):
    return index * interval

def _to_xy(p):
    """완전 private: 다양한 타입을 (x, y) 튜플로 변환"""
    # AutoCAD Point2d
    if hasattr(p, "x") and hasattr(p, "y"):
        return p.x, p.y

    # tuple/list/np.array
    if isinstance(p, (tuple, list, np.ndarray)) and len(p) >= 2:
        return p[0], p[1]

    raise TypeError(f"Unsupported type {type(p)}")

def calculate_destination_coordinates(*args, bearing: float, distance: float):
    """
    점에서 각도와 거리로 이동한 좌표 반환
    Args:
        *args: 점 list,tuple,point
        bearing: 각도(라디안)
        distance: 거리

    Returns:
        tuple[float, float]
    """
    if len(args) == 1:
        x1, y1 = _to_xy(args[0])
    elif len(args) == 2:
        x1, y1 = float(args[0]), float(args[1])
    else:
        raise TypeError(f"Invalid arguments: {args}")

    x2 = x1 + distance * math.cos(bearing)
    y2 = y1 + distance * math.sin(bearing)
    return x2, y2

def calculate_bearing(*args):
    """
    두 점으로 각도 계산
    Args:
        *args: list,tuple,point ,...

    Returns:
        float
    """
    if len(args) == 2:
        p1, p2 = _to_xy(args[0]), _to_xy(args[1])
    elif len(args) == 4:
        p1 = (args[0], args[1])
        p2 = (args[2], args[3])
    else:
        raise TypeError(f"Invalid arguments: {args}")

    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.atan2(dy, dx)

def calculate_angle(center, point):
    """호 중심 기준 각도 계산 (0° = x축, 반시계 방향)
    Args:
        center: 중심점
        point: 구하는 점
    Returns:
        float
    """
    twopi = 2 * math.pi
    c = _to_xy(center)
    p = _to_xy(point)

    dx = p[0] - c[0]
    dy = p[1] - c[1]
    angle = math.atan2(dy, dx) % twopi
    return angle


def degrees_to_dms(degrees: float):
    """
    Converts decimal degrees to degrees, minutes, seconds.

    Args:
    degrees (float): Decimal degrees value.

    Returns:
    tuple: Degrees, minutes, seconds.
    """
    if degrees < 0:
        degrees = degrees * -1

    deg = int(degrees)
    minutes = int((degrees - deg) * 60)
    seconds = (degrees - deg - minutes / 60) * 3600

    return f"{deg}° {minutes}' {seconds:.2f}\""

def calculate_bulge(start_angle: float, end_angle: float, direction: CurveDirection) -> float:
    """
    곡선 BULGE를 계산하는 함수
    Args:
        start_angle: 시작 각도(라디안)
        end_angle: 끝 각도(라디안)
        direction: CurveDirection 객체
    Returns:
        bulge(float): bulge값
    """
    two_pi = math.pi * 2
    # Bulge 계산
    # LEFT: 반시계 +, RIGHT: 시계 -
    if direction == CurveDirection.LEFT:
        sweep = (end_angle - start_angle + two_pi) % two_pi
    else:
        sweep = (start_angle - end_angle + two_pi) % two_pi
        sweep = -sweep  # Bulge 정의상 음수

    # 항상 -π ~ π 범위로 보정
    if sweep > math.pi:
        sweep -= two_pi
    elif sweep < -math.pi:
        sweep += two_pi

    bulge = math.tan(sweep / 4)
    return bulge

def calculate_curve_center(bc_xy: any, ec_xy: any,
                           radius: float, direction: CurveDirection) -> tuple[float, float]:
    """
    BC, EC와 반지름 R이 주어졌을 때 원의 중심을 계산.
    (즉, BC와 EC에서 거리 R인 점들(두 교점) 중 direction에 맞는 쪽을 선택)
    bc_xy: 호 시작점
    ec_xy: 호 끝점
    radius: 반지름
    direction: 곡선 방향 CurveDirection
    return:
        tuple[float, float]
    """
    bc_xy = _to_xy(bc_xy)
    ec_xy = _to_xy(ec_xy)

    dx = ec_xy[0] - bc_xy[0]
    dy = ec_xy[1] - bc_xy[1]
    d = math.hypot(dx, dy)

    if d == 0:
        raise ValueError("BC and EC are identical points")
    # 두 점 사이 거리가 2R보다 크면 반지름 R로 두 점을 지나는 원이 없음
    if d > 2.0 * radius + 1e-9:
        raise ValueError("No circle with given radius passes through both BC and EC")

    # 중점
    mx = (bc_xy[0] + ec_xy[0]) / 2.0
    my = (bc_xy[1] + ec_xy[1]) / 2.0

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
    if direction == CurveDirection.RIGHT:
        chosen_x, chosen_y = (c1x, c1y) if d1 < 0 else (c2x, c2y)
    else:  # LEFT
        chosen_x, chosen_y = (c1x, c1y) if d1 > 0 else (c2x, c2y)

    return chosen_x, chosen_y

def calculate_simple_curve_geometry(radius: float, cl: float) -> tuple:
    """
    R과 CL로 단곡선 제원 계산
    Args:
        radius: 곡선반경
        cl: 곡선장
    Returns:
        tuple: r, ia, tl, m, sl
    """
    # 곡선 제원 계산
    r = abs(radius)  # 곡선반경
    ia = cl / r  # 교각
    tl = r * math.tan(ia / 2)  # 접선장
    m = r * (1 - math.cos(ia / 2))  # 중앙종거
    sl = r * (1 / math.cos(ia / 2) - 1)  # 외거

    return r, ia, tl, m, sl

def calculate_distance(*args) -> float:
    """
    두 점 사이 거리 계산.
    지원 타입:
        - tuple/list/np.array: (x, y)
        - Shapely Point: .x, .y
        - Vector2: .x, .y
        - 두 개 float: x1, y1, x2, y2
    """
    if len(args) == 2:
        p1, p2 = _to_xy(args[0]), _to_xy(args[1])
    elif len(args) == 4:
        p1, p2 = (args[0], args[1]), (args[2], args[3])
    else:
        raise TypeError(f"Invalid arguments {args}")

    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.hypot(dx, dy)


def calculate_midpoint(p1, p2) -> tuple[float, float]:
    """
    두 점의 중점을 계산합니다.

    Args:
        p1 : 첫 번째 점
        p2 : 두 번째 점

    Returns:
        tuple[float, float]
    """
    p1 = _to_xy(p1)
    p2 = _to_xy(p2)

    return (p1[0] + p2[0]) / 2.0,(p1[1] + p2[1]) / 2.0


#offset 좌표 반환
def calculate_offset_point_by_direction(direction: float, point_a, offset_distance: float):
    """
    점에서 오프셋한 점 반환
    Args:
        direction: 방향각도 rad
        point_a: 점
        offset_distance: 오프셋 거리

    Returns:
        tuple[float, float]
    """

    if offset_distance > 0:#우측 오프셋
        direction -= math.pi /2
    else:
        direction += math.pi / 2 #좌측 오프셋
    offset_a_xy = calculate_offset_coordinates(point_a, bearing=direction, distance=offset_distance)
    return offset_a_xy


def find_curve_direction(start_point, end_point, center_point) -> CurveDirection:
    """
    세 점(시작점, 끝점, 원의 중심점)으로 방향(시계/반시계)을 판정
    Args:
        start_point: 시작점
        end_point: 끝점
        center_point: 원 중심점
    Returns:
        CurveDirection
    """
    #내부호출
    start_point = _to_xy(start_point)
    end_point = _to_xy(end_point)
    center_point = _to_xy(center_point)

    # 벡터 계산 (중심 → 시작, 중심 → 끝)
    v1x = start_point[0] - center_point[0]
    v1y = start_point[1] - center_point[1]
    v2x = end_point[0] - center_point[0]
    v2y = end_point[1] - center_point[1]

    # 외적 계산
    cross = v1x * v2y - v1y * v2x

    # 내적 (혹시 필요 시)
    dot = v1x * v2x + v1y * v2y

    # 반경이 거의 0이거나 동일점일 때 안전처리
    if abs(v1x) < 1e-9 and abs(v1y) < 1e-9:
        return CurveDirection.NULL
    if abs(v2x) < 1e-9 and abs(v2y) < 1e-9:
        return CurveDirection.NULL

    # cross 부호로 회전방향 결정
    if cross < 0:
        return CurveDirection.RIGHT   # 시계방향
    elif cross > 0:
        return CurveDirection.LEFT  # 반시계방향
    else:
        return CurveDirection.NULL   # 일직선

def draw_arc(direction: CurveDirection, start_point, end_point, center_point, num_points=100):
    """중심점과 시작/끝점, 방향에 따라 작은 원호 좌표 생성"""
    x_start, y_start = _to_xy(start_point)
    x_end, y_end = _to_xy(end_point)
    x_center, y_center = _to_xy(center_point)

    start_angle = math.atan2(y_start - y_center, x_start - x_center)
    end_angle = math.atan2(y_end - y_center, x_end - x_center)

    # 방향 판정 (벡터 외적)
    cross = (x_start - x_center) * (y_end - y_center) - (y_start - y_center) * (x_end - x_center)

    if direction == CurveDirection.RIGHT and cross > 0:
        end_angle -= 2 * math.pi
    elif direction == CurveDirection.LEFT and cross < 0:
        end_angle += 2 * math.pi

    angles = np.linspace(start_angle, end_angle, num_points)
    radius = math.hypot(x_start - x_center, y_start - y_center)

    x_arc = x_center + radius * np.cos(angles)
    y_arc = y_center + radius * np.sin(angles)

    return x_arc, y_arc