import pandas as pd

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

def parse_curve(filepath):
    df_curve = pd.read_csv(filepath, sep=",", header=None, names=['sta', 'radius', 'cant'])
    return [(row['sta'], row['radius'], row['cant']) for _, row in df_curve.iterrows()]


def parse_pitch(filepath):
    df_pitch = pd.read_csv(filepath, sep=",", header=None, names=['sta', 'pitch'])
    return [(row['sta'], row['pitch']) for _, row in df_pitch.iterrows()]


def parse_polyline(filepath):
    points = []
    with open(filepath, 'r') as file:
        for line in file:
            x, y, z = map(float, line.strip().split(','))
            points.append((x, y, z))
    return points

def safe_loader(loader_func, file_path, fail_msg):
    """파일 로드 공통 처리 함수"""
    try:
        if not file_path:
            raise FileNotFoundError("파일 경로가 지정되지 않았습니다.")
        data = loader_func(file_path)
        if not data:
            raise ValueError(f"{fail_msg}: 데이터가 비어 있습니다.")
        return data
    except Exception as e:
        raise RuntimeError(f"{fail_msg}: {e}")