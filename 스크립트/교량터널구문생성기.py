import random
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import math
import re


'''
교량 터널 엑셀 데이터를 이용해 bve 구조물 구문을 반환하는 코드
made by dger
2025.02.27 1600
#ver1
#초안작성

입력 : 엑셀 데이터(교량 터널)
''   A     B        C       D
1    B1    18830    1920    280

출력: 교량터널.TXT

'''
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

def isbridge_tunnel(sta, structure_list):
    """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
    for name, start, end in structure_list['bridge']:
        if start <= sta <= end:
            return '교량'
    
    for start, end in structure_list['tunnel']:
        if start <= sta <= end:
            return '터널'
    
    return '토공'

def get_block_index(current_track_position, block_interval = 25):
    """현재 트랙 위치를 블록 인덱스로 변환"""
    return math.floor(current_track_position / block_interval + 0.001) * block_interval



def open_excel_file():
    """파일 선택 대화 상자를 열고, 엑셀 파일 경로를 반환하는 함수"""
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김
    root.attributes("-topmost", True)
    file_path = filedialog.askopenfilename(
        title="엑셀 파일 선택",
        filetypes=[("Excel Files", "*.xlsx")]
    )
    
    return file_path

def get_obj_index(DESIGNSPEED, LINECOUNT):
    """
    설계 속도와 선로 개수에 따라 교량 및 터널의 객체 인덱스를 반환하는 함수
    param DESIGNSPEED: 설계 속도 (int)
    param LINECOUNT: 선로 개수 (int) (1: 단선, 2 이상: 복선)
    return: (교량 인덱스, 터널 인덱스) -> (idx_br, idx_tn)
    """
    # 오브젝트 딕셔너리 (교량, 터널)
    OBJECT_DICTIONARY = {
        150: {'토공': (62,21), '교량': (28, 33), '터널': (51, 22)},
        250: {'토공': (62,21), '교량': (28, 33), '터널': (51, 22)},
        350: {'토공': (9,1), '교량': (0, 81), '터널': (91, 80)}
    }

    # 유효한 설계 속도 확인
    if DESIGNSPEED not in OBJECT_DICTIONARY:
        raise ValueError(f"Invalid DESIGNSPEED: {DESIGNSPEED}. Valid values are {list(OBJECT_DICTIONARY.keys())}.")
    
    # 단선(1)일 경우 [0], 복선(2 이상)일 경우 [1] 반환
    idx_E = OBJECT_DICTIONARY[DESIGNSPEED]['토공'][0] if LINECOUNT == 1 else OBJECT_DICTIONARY[DESIGNSPEED]['토공'][1]
    idx_br = OBJECT_DICTIONARY[DESIGNSPEED]['교량'][0] if LINECOUNT == 1 else OBJECT_DICTIONARY[DESIGNSPEED]['교량'][1]
    idx_tn = OBJECT_DICTIONARY[DESIGNSPEED]['터널'][0] if LINECOUNT == 1 else OBJECT_DICTIONARY[DESIGNSPEED]['터널'][1]

    return idx_E, idx_br, idx_tn

def get_earthwork_embank_index(DESIGNSPEED, LINECOUNT):
    """
    설계 속도와 선로 개수에 따라 토공 압성토 객체 인덱스를 반환하는 함수
    param DESIGNSPEED: 설계 속도 (int)
    param LINECOUNT: 선로 개수 (int) (1: 단선, 2 이상: 복선)
    return: (교량 인덱스, 터널 인덱스) -> (idx_br, idx_tn)
    """
    # 오브젝트 딕셔너리 (교량, 터널)
    OBJECT_DICTIONARY = {
        150: {'토공압성토': (480,480), '터널시점갱문': (60, 77), '터널종점갱문': (61, 77)},
        250: {'토공압성토': (480,480), '터널시점갱문': (60, 77), '터널종점갱문': (61, 77)},
        350: {'토공압성토': (32,125), '터널시점갱문': (174, 174), '터널종점갱문': (174, 174)},
    }

    # 유효한 설계 속도 확인
    if DESIGNSPEED not in OBJECT_DICTIONARY:
        raise ValueError(f"Invalid DESIGNSPEED: {DESIGNSPEED}. Valid values are {list(OBJECT_DICTIONARY.keys())}.")
    
    # 단선(1)일 경우 [0], 복선(2 이상)일 경우 [1] 반환
    idx_E = OBJECT_DICTIONARY[DESIGNSPEED]['토공압성토'][0] if LINECOUNT == 1 else OBJECT_DICTIONARY[DESIGNSPEED]['토공압성토'][1]
    idx_br = OBJECT_DICTIONARY[DESIGNSPEED]['터널시점갱문'][0] if LINECOUNT == 1 else OBJECT_DICTIONARY[DESIGNSPEED]['터널시점갱문'][1]
    idx_tn = OBJECT_DICTIONARY[DESIGNSPEED]['터널종점갱문'][0] if LINECOUNT == 1 else OBJECT_DICTIONARY[DESIGNSPEED]['터널종점갱문'][1]

    return idx_E, idx_br, idx_tn

def create_network_data(structure_list, designspeed,line_count):
    result = []
    e_idx , br_idx,tn_idx = get_obj_index(designspeed, line_count)
    idx_E, idx_tns, idx_tne = get_earthwork_embank_index(designspeed, line_count)
    for name, start, end in structure_list['bridge']:
        start = get_block_index(start)
        end = get_block_index(end)
        br_start_data =''
        br_start_data += f',;{name}\n'#교량명
        br_start_data += f'{start}\n'#시작
        br_start_data += f'.wall 0;-1;{br_idx};\n' #교량
        br_start_data += f'.dikeend 0;\n' #토공
        br_start_data += f'.freeobj 0;{idx_E};0;0;180;\n' #압성토
        
        
        br_end_data = ''
        br_end_data += f'{end}\n'#끝
        br_end_data += f'.wallend 0;\n' #교량
        br_end_data += f'.dike 0;-1;{e_idx};\n' #토공
        br_end_data += f'.freeobj 0;{idx_E};\n' #압성토
        
        result.append(br_start_data)
        result.append(br_end_data)
    for name , start, end in structure_list['tunnel']:
        start = get_block_index(start)
        end = get_block_index(end)
        tn_start_data =''
        tn_start_data += f',;{name}\n'#터널명
        tn_start_data += f'{start}\n'#시작
        tn_start_data += f'.wall 0;-1;{tn_idx};\n' #터널
        tn_start_data += f'.dikeend 0;\n' #토공
        tn_start_data += f'.freeobj 0;{idx_tns};\n' #갱문
        
        
        tn_end_data = ''
        tn_end_data += f'{end}\n'#끝
        tn_end_data += f'.wallend 0;\n' #터널
        tn_end_data += f'.dike 0;-1;{e_idx};\n' #토공
        tn_end_data += f'.freeobj 0;{idx_tne};0;0;180;\n' #갱문


        
        result.append(tn_start_data)
        result.append(tn_end_data)
    return result

def create_txt(output_file, data):
    with open(output_file, 'w', encoding='utf-8') as file:
        for line in data:
            file.write(line + "\n")
# 실행
def load_structure_data():
    """구조물 데이터를 엑셀 파일에서 불러오는 함수"""
    openexcelfile = r'c:/temp/구조물.xlsx'
    if openexcelfile:
        return find_structure_section(openexcelfile)
    else:
        print("엑셀 파일을 선택하지 않았습니다.")
        return None
    
def get_designspeed():
    """사용자로부터 설계 속도를 입력받아 반환"""
    while True:
        try:
            DESIGNSPEED = int(input('프로젝트의 설계속도 입력 (150, 250, 350): '))
            if DESIGNSPEED not in (150, 250, 350):
                print('올바른 DESIGNSPEED 값을 입력하세요 (150, 250, 350)')
            else:
                return DESIGNSPEED
        except ValueError:
            print("숫자를 입력하세요.")

def get_linecount():
    """사용자로부터 단선 복선을 입력받아 반환"""
    while True:
        try:
            LINECOUNT = int(input('프로젝트의 선로갯수 입력 (1, 2): '))
            if LINECOUNT not in (1, 2):
                print('올바른 선로갯수 값을 입력하세요 (1, 2)')
            else:
                return LINECOUNT
        except ValueError:
            print("숫자를 입력하세요.")

def generate_bridge_data():
    """교량/터널 구문 데이터를 생성하고 반환"""
    design_speed = get_designspeed()
    line_count = get_linecount()
    structure_list = load_structure_data()

    result = create_network_data(structure_list, design_speed, line_count)
    return result

def main():
    result = generate_bridge_data()
    output_file = 'c:/temp/교량터널.txt'
    create_txt(output_file, result)
    print('구문 생성이 완료되었습니다.')

if __name__ == "__main__":
    main()

