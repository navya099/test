from functools import lru_cache

import pandas as pd
import pyproj
import math

def read_coordinates(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    coordinates = []
    for line in lines:
        parts = line.strip().split(',')
        if len(parts) == 3:
            x = float(parts[0].strip())
            y = float(parts[1].strip())
            z = float(parts[2].strip())
            coordinates.append((x,y, z))
        elif len(parts) == 4:
            station = float(parts[0].strip())
            x = float(parts[1].strip())
            y = float(parts[2].strip())
            z = float(parts[3].strip())
            coordinates.append((station, x, y, z))
    return coordinates

def parse_structure(filepath):
    structure_list = {'bridge': [], 'tunnel': []}

    df_bridge = pd.read_excel(filepath, sheet_name='교량', header=None)
    df_tunnel = pd.read_excel(filepath, sheet_name='터널', header=None)

    df_bridge.columns = ['br_NAME', 'br_START_STA', 'br_END_STA', 'br_LENGTH']
    df_tunnel.columns = ['tn_NAME', 'tn_START_STA', 'tn_END_STA', 'tn_LENGTH']

    for _, row in df_bridge.iterrows():
        structure_list['bridge'].append((row['br_NAME'], row['br_START_STA'], row['br_END_STA']))
    for _, row in df_tunnel.iterrows():
        structure_list['tunnel'].append((row['tn_NAME'], row['tn_START_STA'], row['tn_END_STA']))
    return structure_list

@lru_cache(maxsize=8)
def _get_transformer(src: int, target: int):
    """Transformer 객체 캐싱 - 매 호출마다 재생성 방지"""
    return pyproj.Transformer.from_crs(src, target, always_xy=True)

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
    transformer = _get_transformer(src, target)  # ✅ 캐시에서 꺼냄

    # 단일 좌표
    if isinstance(coords[0], (int, float)):
        return transformer.transform(coords[0], coords[1])

    # ✅ 배치 변환 - 루프 없이 한번에 처리
    xs, ys = zip(*coords)
    result_xs, result_ys = transformer.transform(xs, ys)
    return list(zip(result_xs, result_ys))

def horizontal_distance(p1, p2):

    return math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)

def create_segment(xy_coord, buffer_x: int, buffer_y: int):
    """
    구간 분할 설정 (직사각형 범위)
    buffer_x: 노선 횡방향(또는 X축) 확장 거리
    buffer_y: 노선 진행방향(또는 Y축) 확장 거리
    """
    x, y = xy_coord
    minx = x - buffer_x
    miny = y - buffer_y
    maxx = x + buffer_x
    maxy = y + buffer_y

    return minx, miny, maxx, maxy