import random
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import math
import re

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
    for start, end in structure_list['bridge']:
        if start <= sta <= end:
            return '교량'
    
    for start, end in structure_list['tunnel']:
        if start <= sta <= end:
            return '터널'
    
    return '토공'


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

def create_transmisson_data(structure_list):
    result = []
    for name, start, end in structure_list['bridge']:
        br_start_data = f'{start},.FREEOBJ 0;237;,.FREEOBJ 0;237;6.58;,.FREEOBJ 0;239;,.FREEOBJ 0;240;,.RAILEND 100;,.RAILEND 101;'
        br_end_data = f'{end},.FREEOBJ 0;237;0;0;180;,.FREEOBJ 0;237;-6.58;0;180;,.FREEOBJ 0;241;,.FREEOBJ 0;242;,.RAIL 100;0;0;76;,.RAIL 101;0;0;77;'
        result.append(br_start_data)
        result.append(br_end_data)
    for name ,start, end in structure_list['tunnel']:
        tn_start_data = f'{start},.FREEOBJ 0;238;,.FREEOBJ 0;238;6.41;,.RAILEND 100;,.RAILEND 101;'
        tn_end_data = f'{end},.FREEOBJ 0;238;-6.58;0;180;,.FREEOBJ 0;238;0;0;180;,.RAIL 100;0;0;76;,.RAIL 101;0;0;77;'
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
    openexcelfile = open_excel_file()
    if openexcelfile:
        return find_structure_section(openexcelfile)
    else:
        print("엑셀 파일을 선택하지 않았습니다.")
        return None

def main():
    """전체 작업을 관리하는 메인 함수"""
    # 구조물 정보 로드
    structure_list = load_structure_data()
    if structure_list:
        print("구조물 정보가 성공적으로 로드되었습니다.")

    #구문생성
    result = create_transmisson_data(structure_list)

    #txt저장
    output_file = 'c:/temp/통신.txt'
    create_txt(output_file, result)
    # 최종 출력
    print('구문 생성이 완료되었습니다.')
# 실행
if __name__ == "__main__":
    main()

