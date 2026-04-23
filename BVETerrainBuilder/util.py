import numpy as np

def interpolate_z(orig_tri, p_2d):
    """원래 삼각형 평면 위의 (x, y)에 대응하는 정밀한 Z값을 계산"""
    p1, p2, p3 = orig_tri
    # 평면의 법선 벡터 (Normal Vector)
    v1 = p2 - p1
    v2 = p3 - p1
    n = np.cross(v1, v2)
    # 평면 방정식: a(x-x1) + b(y-y1) + c(z-z1) = 0
    # z = z1 - (a(x-x1) + b(y-y1)) / c
    if abs(n[2]) < 1e-9: return p1[2]  # 수직 평면 예외 처리
    z = p1[2] - (n[0] * (p_2d[0] - p1[0]) + n[1] * (p_2d[1] - p1[1])) / n[2]
    return z

def get_stations(all_coords, partitial_coords):
    """all_coords에서 partitial_coords 길이의 측점리스트 얻기"""
    stations = []
    for coord in partitial_coords:
        # 전체 all_coords에서 현재 partitial_coords 인덱스를 찾음
        idx = all_coords.index(coord)
        station = idx * 25  # 25m 간격
        stations.append(station)
    return stations

def get_earthwork_sections(seg_coords, stations, structure_list):
    """토공구간 섹션 반환 함수
    \n입력 예시
    seg_coords = [A,B,C,D,E,F]\n
    stations = [0,25,50,75,100,125]\n
    structure_list에 stations 50~75가 교량이라고 정의되어 있다면:\n
    \n출력:
        [\n{"name":"토공구간_2", "coords":[A,B]},{"name":"토공구간_last", "coords":[E,F]}\n]
    """

    sections = []
    current_section = []
    current_indices = []

    for i, (coord, station) in enumerate(zip(seg_coords, stations)):
        if is_bridge_tunnel(station, structure_list):
            if current_section:
                sections.append({
                    "name": f"토공구간_{i}",
                    "coords": current_section,
                    "indices": current_indices
                })
                current_section = []
                current_indices = []
        else:
            current_section.append(coord)
            current_indices.append(i)

    if current_section:
        sections.append({
            "name": "토공구간_last",
            "coords": current_section,
            "indices": current_indices
        })

    return sections



def is_bridge_tunnel(sta, structure_list):
    """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
    for name, start, end in structure_list['bridge']:
        if start <= sta <= end:
            return True

    for name, start, end in structure_list['tunnel']:
        if start <= sta <= end:
            return True

    return False

