import math

from vector2 import Vector2


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
    dx = point.x - center.x
    dy = point.y - center.y
    angle = math.degrees(math.atan2(dy, dx)) % 360
    return angle