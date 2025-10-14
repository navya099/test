import pyproj

def convert_coordinates(coords, src: int, target: int):
    """
    좌표 변환 (단일 또는 리스트/튜플)

    Args:
        coords: (x, y) 또는 [(x1, y1), (x2, y2), ...]
        src: 소스 EPSG
        target: 타겟 EPSG
    Returns:
        tuple 또는 list[tuple]
    """
    transformer = pyproj.Transformer.from_crs(src, target, always_xy=True)

    # 단일 좌표
    if isinstance(coords[0], (int, float)):
        x, y = coords
        return transformer.transform(x, y)

    # 여러 좌표
    return [transformer.transform(x, y) for x, y in coords]
