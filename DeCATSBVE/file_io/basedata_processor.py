import pandas as pd

def find_structure_section(filepath):
    """xlsx 파일을 읽고 교량과 터널 정보를 반환하는 함수"""
    structure_list = {'bridge': [], 'tunnel': []}

    # xlsx 파일 읽기
    df_bridge = pd.read_excel(filepath, sheet_name='교량', header=None)
    df_tunnel = pd.read_excel(filepath, sheet_name='터널', header=None)

    # 열 개수 확인
    print(df_tunnel.shape)  # (행 개수, 열 개수)
    print(df_tunnel.head())  # 데이터 확인

    # 첫 번째 행을 열 제목으로 설정
    df_bridge.columns = ['br_NAME', 'br_START_STA', 'br_END_STA', 'br_LENGTH']
    df_tunnel.columns = ['tn_NAME', 'tn_START_STA', 'tn_END_STA', 'tn_LENGTH']

    # 교량 구간과 터널 구간 정보
    for _, row in df_bridge.iterrows():
        structure_list['bridge'].append((row['br_NAME'], row['br_START_STA'], row['br_END_STA']))

    for _, row in df_tunnel.iterrows():
        structure_list['tunnel'].append((row['tn_NAME'], row['tn_START_STA'], row['tn_END_STA']))

    return structure_list

def find_curve_section(txt_filepath='curveinfo.txt'):
    """txt 파일을 읽고 곧바로 측점(sta)과 곡선반경(radius) 정보를 반환하는 함수"""

    curve_list = []

    # 텍스트 파일(.txt) 읽기
    df_curve = pd.read_csv(txt_filepath, sep=",", header=None, names=['sta', 'radius', 'cant'])

    # 곡선 구간 정보 저장
    for _, row in df_curve.iterrows():
        curve_list.append((row['sta'], row['radius'], row['cant']))

    return curve_list


def find_pitch_section(txt_filepath='pitchinfo.txt'):
    """txt 파일을 읽고 곧바로 측점(sta)과 기울기(pitch) 정보를 반환하는 함수"""

    curve_list = []

    # 텍스트 파일(.txt) 읽기
    df_curve = pd.read_csv(txt_filepath, sep=",", header=None, names=['sta', 'radius'])

    # 곡선 구간 정보 저장
    for _, row in df_curve.iterrows():
        curve_list.append((row['sta'], row['radius']))

    return curve_list

def read_polyline(file_path):
    points = []
    with open(file_path, 'r') as file:
        for line in file:
            # 쉼표로 구분된 값을 읽어서 float로 변환
            x, y, z = map(float, line.strip().split(','))
            points.append((x, y, z))
    return points