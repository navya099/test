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


def calculate_curve_center(bc, ec, radius: float, direction: CurveDirection) -> tuple[float, float]:
    """
    두 점(BC, EC)과 반지름, 방향(1=RIGHT, 0=LEFT)으로 원의 중심 좌표 계산.
    """
    bc = _to_xy(bc)
    ec = _to_xy(ec)
    dx = ec[0] - bc[0]
    dy = ec[1] - bc[1]
    d = math.hypot(dx, dy)

    if d == 0 or d > 2 * radius:
        raise ValueError("Invalid BC/EC distance for given radius")

    # 중점
    mx = (bc[0] + ec[0]) / 2
    my = (bc[1] + ec[1]) / 2

    # chord의 수직거리 h
    h = math.sqrt(radius ** 2 - (d / 2) ** 2)

    # 단위 수직벡터
    ux = -dy / d
    uy = dx / d

    # 방향 선택 (1=RIGHT, 0=LEFT)
    sign = -1 if direction == CurveDirection.RIGHT else 1

    # 중심 좌표 계산
    cx = mx + sign * ux * h
    cy = my + sign * uy * h

    return cx, cy

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
def calculate_offset_point(direction: float, point_a, offset_distance: float):
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
    offset_a_xy = calculate_destination_coordinates(point_a, bearing=direction, distance=offset_distance)
    return offset_a_xy


def find_curve_direction(bp, ip, ep) -> CurveDirection:
    """
    세 점 (BP, IP, EP)으로 방향(좌/우)을 판별
    - 좌표계 종류(데카르트, TM, 경위도 등)에 무관
    """
    ax, ay = _to_xy(bp)
    bx, by = _to_xy(ip)
    cx, cy = _to_xy(ep)

    # 벡터 AB, BC
    abx, aby = bx - ax, by - ay
    bcx, bcy = cx - bx, cy - by

    # 외적
    cross = abx * bcy - aby * bcx

    # 판정
    if abs(cross) < 1e-9:
        return CurveDirection.NULL
    elif cross > 0:
        return CurveDirection.LEFT   # 반시계
    else:
        return CurveDirection.RIGHT  # 시계

def draw_arc(direction: CurveDirection, start_point, end_point, center_point, num_points=100):
    """중심점과 시작/끝점, 방향에 따라 항상 '작은 원호'를 생성"""
    x_start, y_start = _to_xy(start_point)
    x_end, y_end = _to_xy(end_point)
    x_center, y_center = _to_xy(center_point)

    start_angle = math.atan2(y_start - y_center, x_start - x_center)
    end_angle = math.atan2(y_end - y_center, x_end - x_center)

    # 기본 각도차
    delta = end_angle - start_angle

    # ① 방향에 따라 올바른 회전 방향 조정
    if direction == CurveDirection.RIGHT and delta > 0:
        delta -= 2 * math.pi
    elif direction == CurveDirection.LEFT and delta < 0:
        delta += 2 * math.pi

    # ② 항상 작은 원호만 되도록 각도 범위 보정
    if delta > math.pi:
        delta -= 2 * math.pi
    elif delta < -math.pi:
        delta += 2 * math.pi

    end_angle = start_angle + delta

    # ③ 좌표 생성
    angles = np.linspace(start_angle, end_angle, num_points)
    radius = math.hypot(x_start - x_center, y_start - y_center)
    x_arc = x_center + radius * np.cos(angles)
    y_arc = y_center + radius * np.sin(angles)

    return x_arc, y_arc
