import tkinter as tk
from tkinter import filedialog
from file_io.basedata_processor import find_structure_section, find_curve_section, find_pitch_section, read_polyline
import os
import pickle

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



def save_poles(poles, filename="poles.dat"):
    with open(filename, "wb") as f:
        pickle.dump(poles, f)

def load_poles(filename="poles.dat"):
    with open(filename, "rb") as f:
        return pickle.load(f)

def save_runner(runner, filename="runner.dat", version=1):
    state = {
        "version": version,
        "poledata": runner.poledata,
        "wire_data": runner.wire_data,
        "polyline_with_sta": runner.polyline_with_sta,
        "idxlib": runner.idxlib,
        "dataprocessor": runner.dataprocessor,
        "airjoint_list": runner.airjoint_list,
        "pitchlist": runner.pitchlist,
        "curvelist": runner.curvelist,
        "structure_list": runner.structure_list,
        "pole_processor": runner.pole_processor,
        "wire_processor": runner.wire_processor,
        "designspeed": runner.designspeed,
        "iscustommode": runner.iscustommode,
        "is_create_dxf": runner.is_create_dxf,
        "_cached_df": runner._cached_df,
        "wire_path_sub": runner.wire_path_sub,
        "wire_path_main": runner.wire_path_main,
        "polesaver_main": runner.polesaver_main,
        "polesaver_sub": runner.polesaver_sub,
        "pole_path_main": runner.pole_path_main,
        "pole_path_sub": runner.pole_path_sub,
        "track_mode": runner.track_mode,
        "track_direction": runner.track_direction,
        "offset_line_with_25": runner.offset_line_with_25,
        "track_distance": runner.track_distance
    }

    # None 체크 및 경고 출력
    for key, value in state.items():
        if value is None:
            print(f"[WARN] {key} 값이 None으로 저장됩니다. 기본값을 확인하세요.")

    with open(filename, "wb") as f:
        pickle.dump(state, f)

def load_runner(runner, filename="runner.dat"):
    with open(filename, "rb") as f:
        state = pickle.load(f)

    # None 체크 및 출력
    for key, value in state.items():
        if value is None:
            print(f"[WARN] {key} 값이 None입니다. 기본값으로 초기화하세요.")

    # 안전한 기본값 적용
    runner.poledata = state.get("poledata")
    runner.wire_data = state.get("wire_data")
    runner.polyline_with_sta = state.get("polyline_with_sta")
    runner.idxlib = state.get("idxlib")
    runner.dataprocessor = state.get("dataprocessor")
    runner.airjoint_list = state.get("airjoint_list")
    runner.pitchlist = state.get("pitchlist")
    runner.curvelist = state.get("curvelist")
    runner.structure_list = state.get("structure_list")
    runner.pole_processor = state.get("pole_processor")
    runner.wire_processor = state.get("wire_processor")

    runner.designspeed = state.get("designspeed", 0)
    runner.iscustommode = state.get("iscustommode", 0)
    runner.is_create_dxf = state.get("is_create_dxf", 0)
    runner._cached_df = state.get("_cached_df")

    runner.wire_path_sub = state.get("wire_path_sub")
    runner.wire_path_main = state.get("wire_path_main")
    runner.polesaver_main = state.get("polesaver_main")
    runner.polesaver_sub = state.get("polesaver_sub")
    runner.pole_path_main = state.get("pole_path_main")
    runner.pole_path_sub = state.get("pole_path_sub")
    runner.track_mode = state.get("track_mode", "single")
    runner.track_direction = state.get("track_direction", "mainL_subR")
    runner.offset_line_with_25 = state.get("offset_line_with_25")
    runner.track_distance = state.get("track_distance", 4.3)
