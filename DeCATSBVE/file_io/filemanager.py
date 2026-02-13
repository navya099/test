import tkinter as tk
from tkinter import filedialog
from file_io.basedata_processor import find_structure_section, find_curve_section, find_pitch_section, read_polyline
import os
def read_file():
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김
    file_path = filedialog.askopenfilename(defaultextension=".txt",
                                           filetypes=[("txt files", "curve_info.txt"), ("All files", "*.*")])

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

def open_excel_file():
    """파일 선택 대화 상자를 열고, 엑셀 파일 경로를 반환하는 함수"""
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김
    file_path = filedialog.askopenfilename(
        title="엑셀 파일 선택",
        filetypes=[("Excel Files", "*.xlsx")]
    )

    return file_path

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


def load_pitch_data():
    """곡선 데이터를 텍스트 파일에서 불러오는 함수"""
    txt_filepath = 'c:/temp/pitch_info.txt'
    if txt_filepath:
        return find_pitch_section(txt_filepath)
    else:
        print("지정한 파일을 찾을 수 없습니다.")
        return None

def load_coordinates():
    """BVE 좌표 데이터를 텍스트 파일에서 불러오는 함수"""
    coord_filepath = 'c:/temp/bve_coordinates.txt'
    return read_polyline(coord_filepath)

def write_to_file(filename, lines):
    """리스트 데이터를 파일에 저장하는 함수"""
    try:
        # 디렉토리 자동 생성
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(lines)  # 리스트 데이터를 한 번에 파일에 작성

        print(f"✅ 파일 저장 완료: {filename}")
    except Exception as e:
        print(f"⚠️ 파일 저장 중 오류 발생: {e}")
