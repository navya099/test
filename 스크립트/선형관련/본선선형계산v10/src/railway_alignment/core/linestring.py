from shapely.geometry import LineString
import math

def create_linestring(alignment: list[list[float]]) -> LineString:
    return LineString([(p[0], p[1]) for p in alignment])


def generate_integers(start: float, end: float, inc: int) -> list[int]:
    """start~end 사이 inc 배수 정수 리스트 (음수/역방향 지원)"""
    if inc <= 0:
        raise ValueError(f"증분은 양수여야 합니다: {inc}")
    if start > end:
        start, end = end, start
    start_rounded = math.ceil(start / inc) * inc
    end_rounded = math.floor(end / inc) * inc
    return list(range(int(start_rounded), int(end_rounded) + inc, inc))