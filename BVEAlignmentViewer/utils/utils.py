import uuid

def remove_duplicate_radius(data: list[list[str]]) -> list[tuple[int, float, float]]:
    """
    radius 리스트에서 연속된 중복값을 제거하는 함수.

    Args:
        data (list[list[str]]): 곡선데이터 리스트 [station, radius, cant]

    Returns:
        list[tuple[int, float, float]]: 중복 제거된 리스트 [station, radius, cant]
    """
    filtered_data = []
    previous_radius = None

    for row in data:
        try:
            station, radius, cant = float(row[0]), float(row[1]), float(row[2])
            station = int(station)
        except (ValueError, IndexError):
            print(f"잘못된 데이터 형식: {row}")
            continue

        if radius != previous_radius:
            filtered_data.append((station, radius, cant))
            previous_radius = radius

    return filtered_data

def try_parse_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def try_parse_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def format_distance(number):
    negative = False
    if number < 0:
        negative = True
        number = abs(number)

    km = int(number) // 1000
    remainder = "{:.2f}".format(number % 1000)
    formatted_distance = "{:d}km{:06.2f}".format(km, float(remainder))

    if negative:
        formatted_distance = "-" + formatted_distance

    return formatted_distance

def generate_entity_id() -> int:
    """8자리 수준의 고유 ID 생성"""
    return uuid.uuid4().int & 0xFFFFFFFF  # 하위 32비트만 사용
