import random
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import math
import re

def distribute_pole_spacing_flexible(start_km, end_km, spans):
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
        possible_spans = list(spans)  #
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

def isbridge_tunnel(sta, structure_list):
    """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
    for name, start, end in structure_list['bridge']:
        if start <= sta <= end:
            return '교량'
    
    for name, start, end in structure_list['tunnel']:
        if start <= sta <= end:
            return '터널'
    
    return '토공'

def save_to_txt(positions, structure_list, filename="pole_positions.txt"):
    """ 신호 위치 데이터를 .txt 파일로 저장하는 함수 """
    
    # 각 구간별 폴타입 및 인덱스 정의
    pole_data = {
        '교량': {'signal_type': '5현시_교량용', 'index': 44, 'x-offset' : -2.675},
        '터널': {'signal_type': '5현시_터널용', 'index': 62, 'x-offset' : -2.54},
        '토공': {'signal_type': '5현시_토공용', 'index': 44, 'x-offset' : -2.675}
    }
    
    device_data = {
    'LEU': (46, ),
    '자동폐색유니트': (47 ,),
    '발리스': (45, )
    }

    # 파일에 데이터 작성
    with open(filename, "w", encoding="utf-8") as f:
        for i, pos in enumerate(positions):
            structure_type = isbridge_tunnel(pos, structure_list)  # 현재 위치의 구조물 확인

            # 각 구간에 맞는 폴타입 및 장치 선택
            signal_data = pole_data.get(structure_type)  # 기본값은 '토공'
            signal_type = signal_data['signal_type']
            signal_index = signal_data['index']
            x_offset = signal_data['x-offset']
            
            if i != 0:
                # 데이터 작성
                f.write('\n,;폐색신호기\n')
                f.write(',;하선\n')
                f.write(f'{pos},.freeobj 0;{signal_index};{x_offset};;,;{signal_type}\n')
                
                f.write(',;상선\n')
                if structure_type == '터널':
                    f.write(f'{pos},.freeobj 0;{signal_index};3;0;180;,;{signal_type}\n')
                else:
                    f.write(f'{pos + 10},.freeobj 0;{signal_index};{x_offset};0;180;,;{signal_type}\n')
                
                if structure_type != '터널':
                    f.write(',;발리스\n')
                    f.write(f'{pos - 20},.freeobj 0;{device_data["발리스"][0]};0;;,;\n')
                    f.write(f'{pos - 17},.freeobj 0;{device_data["발리스"][0]};0;;,;\n')
                    
                    f.write(',;LEU\n')
                    f.write(f'{pos - 14},.freeobj 0;{device_data["LEU"][0]};0;0.3;,;\n')

                    f.write(',;자동폐색유니트\n')
                    f.write(f'{pos - 13},.freeobj 0;{device_data["자동폐색유니트"][0]};0;;,;\n')
                
def open_excel_file():
    """파일 선택 대화 상자를 열고, 엑셀 파일 경로를 반환하는 함수"""
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김
    file_path = filedialog.askopenfilename(
        title="엑셀 파일 선택",
        filetypes=[("Excel Files", "*.xlsx")]
    )
    
    return file_path
           
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

def save_signal_data(pole_positions, structure_list, save_filename):
    """전주 데이터를 텍스트 파일로 저장하는 함수"""
    save_to_txt(pole_positions, structure_list, save_filename)
    print(f"✅ 신호 데이터가 {save_filename} 파일로 저장되었습니다!")

def main():
    """전체 작업을 관리하는 메인 함수"""
    # 파일 읽기 및 데이터 처리
    # 랜덤 범위로 간격을 생성 (1200~1800 사이의 랜덤 값)
    block_length = [random.randint(1200, 1800) for _ in range(4)]
    data = read_file()
    last_block = find_last_block(data)
    start_km = 0
    end_km = last_block // 1000
    spans, pole_positions = distribute_pole_spacing_flexible(start_km, end_km, block_length)

    # 구조물 정보 로드
    structure_list = load_structure_data()
    if structure_list:
        print("구조물 정보가 성공적으로 로드되었습니다.")

    # 데이터 저장
    save_signal_data(pole_positions, structure_list)
    
    # 최종 출력
    print(f"신호기 개수: {len(pole_positions)}")
    print(f'폐색간격 최소:{min(block_length)},최대: {max(block_length)}')
# 실행
if __name__ == "__main__":
    main()

