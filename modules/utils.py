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

