import random
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import math
import re

# 두 벡터 간 각도 계산
def calculate_angle(vec1, vec2):
    # 벡터의 내적 계산
    dot_product = vec1[0] * vec2[0] + vec1[1] * vec2[1] + vec1[2] * vec2[2]
    
    # 벡터의 크기 계산
    mag_vec1 = math.sqrt(vec1[0]**2 + vec1[1]**2 + vec1[2]**2)
    mag_vec2 = math.sqrt(vec2[0]**2 + vec2[1]**2 + vec2[2]**2)
    
    # 코사인 값 계산
    cos_theta = dot_product / (mag_vec1 * mag_vec2)
    
    # 각도 계산 (라디안 단위)
    angle_rad = math.acos(cos_theta)
    
    # 각도를 도 단위로 변환
    angle_deg = math.degrees(angle_rad)
    
    return angle_deg

# 두 점 간의 거리 계산
def calculate_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2)

# 점에서의 벡터를 계산하는 함수 (점 a의 이전 점과 이후 점을 사용)
def calculate_vector_at_point(polyline, point_idx):
    # 이전 점과 이후 점을 가져와 벡터 계산
    prev_point = polyline[point_idx - 1] if point_idx - 1 >= 0 else polyline[point_idx]
    next_point = polyline[point_idx + 1] if point_idx + 1 < len(polyline) else polyline[point_idx]
    
    # 벡터 계산 (next_point - prev_point)
    vewgt = (next_point[0] - prev_point[0], next_point[1] - prev_point[1], next_point[2] - prev_point[2])
    
    return vewgt

# 점 a와 폴리선에서 가장 가까운 점 찾기
def find_closest_point(polyline, point_a):
    closest_point = None
    min_distance = float('inf')
    closest_idx = -1
    
    for idx, point in enumerate(polyline):
        dist = calculate_distance(point, point_a)
        if dist < min_distance:
            min_distance = dist
            closest_point = point
            closest_idx = idx
    
    return closest_idx, closest_point

# 점 a, b와 벡터를 이용하여 각도를 계산하는 함수
def angle_between_points_and_vector(polyline, point_a, point_b):
    # 점 a와 폴리선에서 가장 가까운 점 찾기
    closest_idx, closest_point = find_closest_point(polyline, point_a)
    
    # 점 a에서의 벡터 계산
    vewgt = calculate_vector_at_point(polyline, closest_idx)
    
    # 점 a와 점 b를 잇는 벡터 계산
    vec_ab = (point_b[0] - closest_point[0], point_b[1] - closest_point[1], point_b[2] - closest_point[2])
    
    # 벡터와 선 간 각도 계산
    angle = calculate_angle(vewgt, vec_ab)
    return angle

def distribute_pole_spacing_flexible(start_km, end_km, spans=(45, 50, 55, 60)):
    """
    45, 50, 55, 60m 범위에서 전주 간격을 균형 있게 배분하여 전체 구간을 채우는 함수
    마지막 전주는 종점보다 약간 앞에 위치할 수도 있음.

    :param start_km: 시작점 (km 단위)
    :param end_km: 끝점 (km 단위)
    :param spans: 사용 가능한 전주 간격 리스트 (기본값: 45, 50, 55, 60)
    :return: 전주 간격 리스트, 전주 위치 리스트
    """
    start_m = int(start_km * 1000)  # km → m 변환
    end_m = int(end_km * 1000)
    
    positions = [start_m]
    selected_spans = []
    current_pos = start_m

    while current_pos < end_m:
        possible_spans = list(spans)  # 사용 가능한 간격 리스트 (45, 50, 55, 60)
        random.shuffle(possible_spans)  # 랜덤 배치

        for span in possible_spans:
            if current_pos + span > end_m:
                continue  # 종점을 넘어서면 다른 간격을 선택

            positions.append(current_pos + span)
            selected_spans.append(span)
            current_pos += span
            break  # 하나 선택하면 다음으로 이동

        # 더 이상 배치할 간격이 없으면 종료
        if current_pos + min(spans) > end_m:
            break

    return selected_spans, positions

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
        structure_list['bridge'].append((row['br_START_STA'], row['br_END_STA']))
    
    for _, row in df_tunnel.iterrows():
        structure_list['tunnel'].append((row['tn_START_STA'], row['tn_END_STA']))
    
    return structure_list

def find_curve_section(txt_filepath='curveinfo.txt'):
    """txt 파일을 읽고 곧바로 측점(sta)과 곡선반경(radius) 정보를 반환하는 함수"""
    
    curve_list = []

    # 텍스트 파일(.txt) 읽기
    df_curve = pd.read_csv(txt_filepath, sep=",", header=None, names=['sta', 'radius'])

    # 곡선 구간 정보 저장
    for _, row in df_curve.iterrows():
        curve_list.append((row['sta'], row['radius']))
    
    return curve_list


def isbridge_tunnel(sta, structure_list):
    """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
    for start, end in structure_list['bridge']:
        if start <= sta <= end:
            return '교량'
    
    for start, end in structure_list['tunnel']:
        if start <= sta <= end:
            return '터널'
    
    return '토공'



def round_to_nearest_25(value):
    """주어진 값을 12.5 기준으로 25의 배수로 반올림"""
    return round(value / 25) * 25

def iscurve(cur_sta, curve_list):
    """sta가 곡선 구간에 해당하는지 구분하는 함수"""
    rounded_sta = round_to_nearest_25(cur_sta)  # 25 단위로 반올림
    
    for sta, R in curve_list:
        if rounded_sta == sta:
            if R == 0:
                return '직선', None  # 반경이 0이면 직선
            return '곡선', R  # 반경이 존재하면 곡선

    return '직선', None  # 목록에 없으면 기본적으로 직선 처리


def save_to_txt(positions, structure_list, filename="pole_positions.txt"):
    """ 전주 위치 데이터를 .txt 파일로 저장하는 함수 """
    
    # 각 구간별 폴타입 및 브래킷 정의
    pole_data = {
        '교량': {'I_type': 512, 'O_type': 529, 'I_bracket': 'Cako250_OpG3.5-I', 'O_bracket': 'Cako250_OpG3.5-O'},
        '터널': {'I_type': 1023, 'O_type': 980, 'I_bracket': 'Cako250-Tn-I', 'O_bracket': 'Cako250-Tn-O'},
        '토공': {'I_type': 508, 'O_type': 510, 'I_bracket': 'Cako250_OpG3.0-I', 'O_bracket': 'Cako250_OpG3.0-O'}
    }
    
    # 파일 경로 설정
    filename = "C:/TEMP/" + filename

    # 파일에 데이터 작성
    with open(filename, "w", encoding="utf-8") as f:
        for i, pos in enumerate(positions):
            sta_type = isbridge_tunnel(pos, structure_list)  # 현재 위치의 구간 확인
            # 각 구간에 맞는 폴타입 및 브래킷 선택
            station_data = pole_data.get(sta_type, pole_data['토공'])  # 기본값은 '토공'
            I_type_current, O_type_current = station_data['I_type'], station_data['O_type']
            I_bracket_current, O_bracket_current = station_data['I_bracket'], station_data['O_bracket']

            # 홀수/짝수에 맞는 타이핑
            if i % 2 == 1:
                f.write(f"{pos},.freeobj 0;{I_type_current};,;{I_bracket_current}\n")
            else:
                f.write(f"{pos},.freeobj 0;{O_type_current};,;{O_bracket_current}\n")


def open_excel_file():
    """파일 선택 대화 상자를 열고, 엑셀 파일 경로를 반환하는 함수"""
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김
    file_path = filedialog.askopenfilename(
        title="엑셀 파일 선택",
        filetypes=[("Excel Files", "*.xlsx")]
    )
    
    return file_path

def save_to_WIRE(positions, spans, structure_list, curve_list,polyline,filename="wire.txt"):
    """ 전주 위치에 wire를 배치하는 함수 """
    span = 0
    filename = "C:/TEMP/" + filename
    # sta 값을 자동 추가하여 새로운 리스트 생성
    polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]
    
    with open(filename, "w", encoding="utf-8") as f:
        for i in range(len(positions) - 1):  # 마지막 전주는 제외
            
            pos = positions[i]#현재 전주위치
            next_pos = positions[i + 1]#다음 전주위치
            
            currentspan = next_pos - pos  # 다음 전주와의 거리 계산
            current_structure = isbridge_tunnel(pos, structure_list)#현재 위치의 구조물
            next_structure = isbridge_tunnel(next_pos, structure_list)# 다음 위치의 구조물
            current_curve ,R = iscurve(pos, curve_list) # 현재 위치의 곡선 확인
            next_curve ,next_R = iscurve(next_pos, curve_list) # 다음 위치의 곡선 확인
            current_sta = round_to_nearest_25(pos)#전주위치의 25반올림(bve block에 맞게 조정)
            
            if R and R is not None and R < 0:
                R *= -1
            
            # 적절한 wire index 선택
            span_data = {
                45: (484, "경간 45m", 1236, 1241),
                50: (478, "경간 50m", 1237, 1242),
                55: (485, "경간 55m", 1238, 1243),
                60: (479, "경간 60m", 1239, 1244),
            }
            obj_index, comment, AF_wire, FPW_wire = span_data.get(currentspan, span_data[60])  # 기본값 60m

            angle_rad = 0.4 / currentspan #0.2는 편위
            angle = math.degrees(angle_rad)

            # 구조물에 맞게 위치 조정
            offset = 0
            if current_structure == '교량':
                offset = -0.706
                
            # 다음 구조물에 따라 와이어 각도 조정
            wire_angle = 0
            if current_structure == '교량' and next_structure == '토공':
                wire_angle = -offset / currentspan
            elif current_structure == '토공':
                if next_structure == '교량':
                    wire_angle = offset / currentspan
                elif next_structure == '터널':
                    wire_angle = 1 / currentspan
            elif current_structure == '터널' and next_structure == '토공':
                wire_angle = -1 / currentspan
            
            wire_angle = math.degrees(wire_angle)
            
            #곡선반경에 맞게 각도저장
            if current_curve == '곡선':
                
                point_a = interpolate_coordinates(polyline_with_sta, pos)
                point_b = interpolate_coordinates(polyline_with_sta, next_pos)

                if point_a and point_b:
                    angle = angle_between_points_and_vector(polyline, point_a, point_b)
                
                
            # 홀수/짝수에 따라 출력 (중복 코드 제거)
            sign = -1 if i % 2 == 1 else 1
            lateral_offset = sign * 0.2 #편위
            adjusted_angle = sign * angle
            
            f.write(f"{pos},.freeobj 0;{obj_index};{lateral_offset};;{adjusted_angle};,;{comment}\n")
            f.write(f"{pos},.freeobj 0;{AF_wire};{offset};;{wire_angle};,;급전선\n")
            f.write(f"{pos},.freeobj 0;{FPW_wire};{offset};;{wire_angle};,;FPW\n")
            
def interpolate_coordinates(polyline, target_sta):
    """
    주어진 폴리선 데이터에서 특정 sta 값에 대한 좌표를 선형 보간하여 반환.
    
    :param polyline: [(sta, x, y, z), ...] 형식의 리스트
    :param target_sta: 찾고자 하는 sta 값
    :return: (x, y, z) 좌표 튜플
    """
    # 정렬된 리스트를 가정하고, 적절한 두 점을 찾아 선형 보간 수행
    for i in range(len(polyline) - 1):
        sta1, x1, y1, z1 = polyline[i]
        sta2, x2, y2, z2 = polyline[i + 1]
        
        # target_sta가 두 점 사이에 있는 경우 보간 수행
        if sta1 <= target_sta <= sta2:
            t = (target_sta - sta1) / (sta2 - sta1)
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            z = z1 + t * (z2 - z1)
            return (x, y, z)
    
    return None  # 범위를 벗어난 sta 값에 대한 처리

# 폴리선 좌표 읽기
def read_polyline(file_path):
    points = []
    with open(file_path, 'r') as file:
        for line in file:
            # 쉼표로 구분된 값을 읽어서 float로 변환
            x, y, z = map(float, line.strip().split(','))
            points.append((x, y, z))
    return points

def find_last_block(data):
    last_block = None  # None으로 초기화하여 값이 없을 때 오류 방지
    
    for line in data:
        if isinstance(line, str):  # 문자열인지 확인
            match = re.search(r'(\d+),', line)
            if match:
                last_block = int(match.group(1))  # 정수 변환하여 저장
    
    return last_block  # 마지막 블록 값 반환

def read_file():
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김
    file_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("txt files", "curve_info.txt"), ("All files", "*.*")])
    
    if not file_path:
        print("파일을 선택하지 않았습니다.")
        return []
    
    print('현재 파일:', file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.read().splitlines()  # 줄바꿈 기준으로 리스트 생성
    except UnicodeDecodeError:
        print('현재 파일은 UTF-8 인코딩이 아닙니다. EUC-KR로 시도합니다.')
        try:
            with open(file_path, 'r', encoding='euc-kr') as file:
                lines = file.read().splitlines()
        except UnicodeDecodeError:
            print('현재 파일은 EUC-KR 인코딩이 아닙니다. 파일을 읽을 수 없습니다.')
            return []
    
    return lines

# 실행
def load_structure_data():
    """구조물 데이터를 엑셀 파일에서 불러오는 함수"""
    openexcelfile = open_excel_file()
    if openexcelfile:
        return find_structure_section(openexcelfile)
    else:
        print("엑셀 파일을 선택하지 않았습니다.")
        return None

def load_curve_data():
    """곡선 데이터를 텍스트 파일에서 불러오는 함수"""
    txt_filepath = 'c:/temp/curve_info.txt'
    if txt_filepath:
        return find_curve_section(txt_filepath)
    else:
        print("지정한 파일을 찾을 수 없습니다.")
        return None

def load_coordinates():
    """BVE 좌표 데이터를 텍스트 파일에서 불러오는 함수"""
    coord_filepath = 'c:/temp/bve_coordinates.txt'
    return read_polyline(coord_filepath)

def save_pole_data(pole_positions, structure_list):
    """전주 데이터를 텍스트 파일로 저장하는 함수"""
    save_to_txt(pole_positions, structure_list, filename="전주.txt")
    print(f"✅ 전주 데이터가 'C:/TEMP/전주.txt' 파일로 저장되었습니다!")

def save_wire_data(pole_positions, spans, structure_list, curvelist, polyline):
    """전차선 데이터를 텍스트 파일로 저장하는 함수"""
    save_to_WIRE(pole_positions, spans, structure_list, curvelist, polyline, filename="전차선.txt")
    print(f"✅ 전차선 데이터가 'C:/TEMP/전차선.txt' 파일로 저장되었습니다!")

def main():
    """전체 작업을 관리하는 메인 함수"""
    # 파일 읽기 및 데이터 처리
    data = read_file()
    last_block = find_last_block(data)
    start_km = 0
    end_km = last_block // 1000
    spans, pole_positions = distribute_pole_spacing_flexible(start_km, end_km)

    # 구조물 정보 로드
    structure_list = load_structure_data()
    if structure_list:
        print("구조물 정보가 성공적으로 로드되었습니다.")

    # 곡선 정보 로드
    curvelist = load_curve_data()
    if curvelist:
        print("곡선 정보가 성공적으로 로드되었습니다.")
    
    # BVE 좌표 로드
    polyline = load_coordinates()

    # 데이터 저장
    save_pole_data(pole_positions, structure_list)
    save_wire_data(pole_positions, spans, structure_list, curvelist, polyline)

    # 최종 출력
    print(f"전주 개수: {len(pole_positions)}")
    print(f"마지막 전주 위치: {pole_positions[-1]}m (종점: {int(end_km * 1000)}m)")

# 실행
if __name__ == "__main__":
    main()

