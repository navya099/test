import random
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import math

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
    I_type = 508  # cako250_OpG3.0-I
    O_type = 510  # cako250_OpG3.0-O
    I_type_br = 512  # cako250_OpG3.5-I
    O_type_br = 529  # cako250_OpG3.5-O
    I_type_tn = 1023 # cako250-Tn-I
    O_type_tn = 980  # cako250-Tn-I
    I_bracket = 'Cako250_OpG3.0-I'
    O_bracket = 'Cako250_OpG3.0-O'
    I_bracket_br = 'Cako250_OpG3.5-I'
    O_bracket_br = 'Cako250_OpG3.5-O'
    I_bracket_tn = 'Cako250-Tn-I'
    O_bracket_tn = 'Cako250-Tn-O'

     
    filename = "C:/TEMP/" + filename
    with open(filename, "w", encoding="utf-8") as f:
        for i, pos in enumerate(positions):
            sta_type = isbridge_tunnel(pos, structure_list)  # 현재 위치의 구간 확인
            
            if sta_type == '교량':
                I_type_current, O_type_current = I_type_br, O_type_br
                I_bracket_current, O_bracket_current = I_bracket_br, O_bracket_br
            elif sta_type == '터널':
                I_type_current, O_type_current = I_type_tn, O_type_tn
                I_bracket_current, O_bracket_current = I_bracket_tn, O_bracket_tn
            else:  # 토공 구간
                I_type_current, O_type_current = I_type, O_type
                I_bracket_current, O_bracket_current = I_bracket, O_bracket
            
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

def save_to_WIRE(positions, spans, structure_list, curve_list, filename="wire.txt"):
    """ 전주 위치에 wire를 배치하는 함수 """
    span = 0
    filename = "C:/TEMP/" + filename
    with open(filename, "w", encoding="utf-8") as f:
        for i in range(len(positions) - 1):  # 마지막 전주는 제외
            
            pos = positions[i]
            next_pos = positions[i + 1]
            
            currentspan = next_pos - pos  # 다음 전주와의 거리 계산
            sta_type = isbridge_tunnel(pos, structure_list)  # 현재 위치의 구간 확인
            CURVE_TYPE ,R = iscurve(pos, curve_list) # 현재 위치의 곡선 확인
            sta = round_to_nearest_25(pos)
            
            if R and R is not None:
                if R < 0:
                    R *= -1
                point_list = print_point_coordinates(25,R,sta,num_arcs=10)
                angle_list = print_point_angles(point_list)
                C_x, C_y, _ = compute_point_coordinates(25, R, sta, next_pos)
                angle_c = calculate_bearing(0, 0, C_x, C_y)
                FINALE = angle_c - angle_list[0]
                
            CURVE_TYPE ,R = iscurve(pos, curve_list) # 현재 위치의 곡선 확인    
            # 적절한 wire index 선택
            if currentspan == 45:
                span = currentspan
                obj_index = 484
                comment = '경간 45m'
                span = currentspan
                AF_wire = 1236
                FPW_wire = 1241
            elif currentspan == 50:
                obj_index = 478
                comment = '경간 50m'
                span = currentspan
                AF_wire = 1237
                FPW_wire = 1242
            elif currentspan == 55:
                obj_index = 485
                comment = '경간 55m'
                span = currentspan
                AF_wire = 1238
                FPW_wire = 1243
            else:
                obj_index = 479
                comment = '경간 60m'
                span = 60
                AF_wire = 1239
                FPW_wire = 1244

            angle_rad = 0.4 / span #0.2는 편위
            angle = math.degrees(angle_rad)

            #구조물에 맞게 위치조정
            if sta_type == '교량':
                offset = -0.71
            elif sta_type == '터널':
                offset = 0
            else:  # 토공 구간
                offset = 0

            #곡선반경에 맞게 각도저장
            if CURVE_TYPE == '곡선':
                angle = FINALE
            # 홀수/짝수에 맞는 위치 지정
            if i % 2 == 1:
                f.write(f'{pos},;{comment}\n')
                # 곡선일 경우 angle을 음수로, 아니면 그대로 사용
                if CURVE_TYPE == '곡선':
                    if R <0:
                        f.write(f".freeobj 0;{obj_index};-0.2;;{-angle};,;전차선\n")
                    else:
                        f.write(f".freeobj 0;{obj_index};-0.2;;{angle};,;전차선\n")
                else:
                    f.write(f".freeobj 0;{obj_index};-0.2;;{angle};,;전차선\n")
                f.write(f".freeobj 0;{AF_wire};{offset};,;급전선\n")
                f.write(f".freeobj 0;{FPW_wire};{offset};,;FPW\n")
            else:
                f.write(f'{pos},;{comment}\n')
                if CURVE_TYPE == '곡선':
                    if R <0:
                        f.write(f".freeobj 0;{obj_index};0.2;;{-angle};,;전차선\n")
                    else:
                        f.write(f".freeobj 0;{obj_index};0.2;;{angle};,;전차선\n")
                else:
                    f.write(f".freeobj 0;{obj_index};0.2;;{-angle};,;전차선\n")
                f.write(f".freeobj 0;{AF_wire};{offset};,;급전선\n")
                f.write(f".freeobj 0;{FPW_wire};{offset};,;FPW\n")



def compute_point_coordinates(cl, r, sta, number):
    distance = number - sta  # 시작점에서 이동한 거리
    theta = (distance / cl) * 2 * math.asin(cl / (2 * r))
    x = r * math.sin(theta)
    y = r * (1 - math.cos(theta))
    return x, y, theta

def calculate_bearing(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.degrees(math.atan2(dy, dx))
    return bearing

def print_point_coordinates(cl,R,sta,num_arcs=10): 
    point_list = []
    for i in range(num_arcs):
        x, y, _ = compute_point_coordinates(cl, R, sta, sta + i * cl)
        point_list.append((x, y))  # 수정된 부분
    return point_list

def print_point_angles(point_list):
    angle_list = []
    for i in range(len(point_list) - 1):  # 마지막 인덱스를 초과하지 않도록 수정
        x1 = point_list[i][0]
        y1 = point_list[i][1]
        x2 = point_list[i + 1][0]
        y2 = point_list[i + 1][1]
        angle = calculate_bearing(x1, y1, x2, y2)
        angle_list.append(angle)
    return angle_list


# 실행
start_km = 0
end_km = 3
spans, pole_positions = distribute_pole_spacing_flexible(start_km, end_km)

# 구조물 정보 파일 경로 지정
openexcelfile = open_excel_file()
# 선택된 파일로 구조물 정보 가져오기
if openexcelfile:
    structure_list = find_structure_section(openexcelfile)
    print("구조물 정보가 성공적으로 로드되었습니다.")
else:
    print("엑셀 파일을 선택하지 않았습니다.")

txt_filepath = 'c:/temp/curve_info.txt'


if txt_filepath:
    curvelist = find_curve_section(txt_filepath)
    print("곡선 정보가 성공적으로 로드되었습니다.")
else:
    print("지정한 파일을 찾을 수 없습니다.")

save_to_txt(pole_positions, structure_list, filename="전주.txt")

print(f"전주 개수: {len(pole_positions)}")
print(f"마지막 전주 위치: {pole_positions[-1]}m (종점: {int(end_km * 1000)}m)")
print(f"✅ 전주 데이터가 'C:/TEMP/전주.txt' 파일로 저장되었습니다!")
save_to_WIRE(pole_positions, spans, structure_list,curvelist, filename="전차선.txt")
print(f"✅ 전차선 데이터가 'C:/TEMP/전차선.txt' 파일로 저장되었습니다!")
