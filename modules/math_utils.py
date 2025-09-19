import math

from point2d import Point2d
from vector2 import Vector2
from curvedirection import CurveDirection

def get_block_index(number, interval):
    return int(math.floor(number / interval + 0.001))

def get_station_by_block_index(index, interval):
    return index * interval

def calculate_coordinates(x1,y1,bearing,distance):
    """
    1점에서 각도로 거리만큼 이동한 점의 좌표 계산
    Args:
        x1:
        y1:
        bearing:
        distance:

    Returns:
        x2,y2
    """
    x2 = x1 + distance * math.cos(bearing)
    y2 = y1 + distance * math.sin(bearing)
    return x2,y2

def calculate_bearing(x1, y1, x2, y2):
    """
    두 점의 각도 계산
    Args:
        x1:
        y1:
        x2:
        y2:

    Returns:
        bearing
    """
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.atan2(dy, dx)
    return bearing

def calculate_bearing_civil_coord(x1, y1, x2, y2):
    """
    두 점의 각도계산(토목좌표)
    Args:
        x1:
        y1:
        x2:
        y2:

    Returns:
        bearing
    """
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.degrees(math.atan2(dx, dy))
    if bearing < 0:
        bearing = 360 + bearing
    return bearing

def angle_from_center(center: Vector2, point: Vector2):
    """호 중심 기준 각도 계산 (0° = x축, 반시계 방향)"""
    twopi = 2 * math.pi
    dx = point.x - center.x
    dy = point.y - center.y
    angle = math.atan2(dy, dx) % twopi
    return angle


def degrees_to_dms(degrees):
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

def calculate_curve_center(bc_xy: Vector2, ec_xy: Vector2,
                           radius: float, direction: CurveDirection) -> Vector2:
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
    if direction == CurveDirection.RIGHT:
        chosen_x, chosen_y = (c1x, c1y) if d1 < 0 else (c2x, c2y)
    else:  # LEFT
        chosen_x, chosen_y = (c1x, c1y) if d1 > 0 else (c2x, c2y)

    return Vector2(x=chosen_x, y=chosen_y)

def calculate_curve_geometry(radius, cl) -> tuple:
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

def calculate_distance(p1: Vector2, p2: Vector2) -> float:
    # Calculate the distance between two points in Cartesian coordinates
    distance = math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
    return distance

def calculate_midpoint(p1: Point2d, p2: Point2d) -> Point2d:
    """
    두 점의 중점을 계산합니다.

    Args:
        p1 (Point2d): 첫 번째 점
        p2 (Point2d): 두 번째 점

    Returns:
        Point2d: 중점 좌표
    """
    return Point2d(
        (p1.x + p2.x) / 2.0,
        (p1.y + p2.y) / 2.0,
    )

def calculate_pass_through_point(start: Point2d, end: Point2d, through_point: Point2d) -> Point2d:
    """
    두 점을 이루는 직선에서 임의의 통과점을 넣으면 통과점 2를 반환
    Args:
        start:
        end:
        through_point:

    Returns:

    """