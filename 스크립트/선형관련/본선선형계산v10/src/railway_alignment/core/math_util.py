import math

from shapely.geometry import LineString


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

def calculate_angles(line_string: LineString) -> list[float]:
    angles = []
    coords = line_string.coords
    for i in range(1, len(coords) - 1):
        v1 = (coords[i][0] - coords[i - 1][0], coords[i][1] - coords[i - 1][1])
        v2 = (coords[i + 1][0] - coords[i][0], coords[i + 1][1] - coords[i][1])
        angles.append(calculate_inner_angle(v1, v2))
    return angles

def calculate_inner_angle(v1: tuple, v2: tuple) -> float:
    a1 = math.atan2(v1[1], v1[0])
    a2 = math.atan2(v2[1], v2[0])
    diff = abs(a2 - a1)
    if diff > math.pi:
        diff = 2 * math.pi - diff
    return math.degrees(diff)

def find_direction(radius: float, h1: float, h2: float) -> int:
    if radius == 0:
        return 0
    return 1 if math.sin(math.radians(h2 - h1)) >= 0 else -1

def get_station_label(
    curve_type: str, station: float,
    sp: float, pc: float, cp: float, ps: float, ep: float,
    eps: float = 1e-6,
) -> str:
    checks = [
        (sp, "BC" if curve_type == "simplecurve" else "SP"),
        (pc, "BC" if curve_type == "simplecurve" else "PC"),
        (cp, "EC" if curve_type == "simplecurve" else "CP"),
        (ps, "EC" if curve_type == "simplecurve" else "PS"),
        (ep, "EP"),
    ]
    for target, label in checks:
        if abs(station - target) < eps:
            return label
    return ""


# ============================================================
# 측거/이정량
# ============================================================
def calculate_station_offset(
    sta: float, sp: float, pc: float, cp: float, ps: float, bp: float
) -> float:
    s, sp_i, pc_i, cp_i, ps_i, bp_i = map(int, (sta, sp, pc, cp, ps, bp))
    if s <= sp_i:
        return sta - bp
    if s < pc_i:
        return sta - sp
    if s <= cp_i:
        return sta - pc
    if s <= ps_i:
        return ps - sta
    return sta - ps

def format_station(sta: float) -> str:
    km = int(sta // 1000)
    meter = sta - km * 1000
    return f"{km}+{meter:06.2f}"

def format_bearing(angle: float) -> str:
    angle = angle % 360
    total_seconds = round(angle * 3600) % (360 * 3600)
    deg, rem = divmod(total_seconds, 3600)
    minute, second = divmod(rem, 60)
    return f'N {deg:03d}° {minute:02d}\' {second:02d}"'

# ============================================================
# 각도/거리 포맷
# ============================================================
def degrees_to_dms(degrees: float) -> str:
    """도분초 문자열 (부호 유지)"""
    sign = "-" if degrees < 0 else ""
    d = abs(degrees)
    deg = int(d)
    minutes = int((d - deg) * 60)
    seconds = (d - deg - minutes / 60) * 3600
    return f"{sign}{deg}도  {minutes}분  {seconds:.2f}초"