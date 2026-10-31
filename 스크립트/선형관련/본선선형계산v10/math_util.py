import math


def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)


def calculate_destination_coordinates(
    x1: float, y1: float, bearing: float, distance: float
) -> tuple[float, float]:
    angle = math.radians(bearing)
    return x1 + distance * math.cos(angle), y1 + distance * math.sin(angle)


# ============================================================
# 기하 계산 유틸
# ============================================================
def calculate_bearing(x1: float, y1: float, x2: float, y2: float) -> float:
    """방위각 (수학각, -180~180)"""
    return math.degrees(math.atan2(y2 - y1, x2 - x1))


def calculate_bearing_n(x1: float, y1: float, x2: float, y2: float) -> float:
    """방위각 (북 기준 0~360)"""
    bearing = calculate_bearing(x1, y1, x2, y2)
    return bearing + 360 if bearing <= 0 else bearing



def degrees_to_dms2(degrees: float) -> str:
    """도분초 문자열 (기호 표기)"""
    sign = "-" if degrees < 0 else ""
    d = abs(degrees)
    deg = int(d)
    minutes = int((d - deg) * 60)
    seconds = (d - deg - minutes / 60) * 3600
    return f"{sign}{deg}° {minutes}' {seconds:.2f}\""

def format_distance(number: float, decimal_places: int = 2) -> str:
    """km+m 형식"""
    negative = number < 0
    num = abs(number)
    km = int(num) // 1000
    remainder = num % 1000
    formatted = f"{km:d}km{remainder:0{4 + decimal_places}.{decimal_places}f}"
    return f"-{formatted}" if negative else formatted