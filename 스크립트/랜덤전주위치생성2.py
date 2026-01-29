import random
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import math
import re
import numpy as np
from enum import Enum
from shapely.geometry import Point, LineString
import ezdxf  # Import ezdxf for saving to DXF
import chardet
import logging

'''
ver 2025.03.27
- 복선/단선 구분 기능 추가 (작업 중)
- 단선 전주 좌/우 구분 추가 (WIP)
- 클래스 구조 리팩토링 (WIP)
- 코드 구조 개선 (WIP)
- 일부 클래스 GUI화 진행 중 (WIP)

🔧 수정 내용:
- BaseFileHandler: read_file_content 메소드의 반환값을 self → None으로 변경
- TxTFileHandler: read_file_content 메소드에서 file_data를 줄 단위 리스트로 변환하는 과정 수정
  (중복된 splitlines() 호출 제거, 부모 메서드 호출 후 처리)

'''

# 로깅 설정
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AirJoint(Enum):
    START = "에어조인트 시작점 (1호주)"
    POINT_2 = "에어조인트 (2호주)"
    MIDDLE = "에어조인트 중간주 (3호주)"
    POINT_4 = "에어조인트 (4호주)"
    END = "에어조인트 끝점 (5호주)"


class PolePositionManager:
    def __init__(self, mode, start_km, end_km, txtfile_handler=None):
        self.txtfile_handler = TxTFileHandler()
        self.mode = mode
        self.start_km = start_km
        self.end_km = end_km
        self.pole_positions = []
        self.airjoint_list = []
        self.post_number_lst = []
        self.posttype_list = []
        self.total_data_list = []

    def generate_positions(self):
        if self.mode == 1:
            self.pole_positions = distribute_pole_spacing_flexible(self.start_km, self.end_km)
            self.airjoint_list = define_airjoint_section(self.pole_positions)
            self.post_number_lst = generate_postnumbers(self.pole_positions)
        else:
            # Load from file
            messagebox.showinfo('파일 선택', '사용자 정의 전주파일을 선택해주세요')

            self.load_pole_positions_from_file()
            logger.info('사용자 정의 전주파일이 입력되었습니다.')

    def load_pole_positions_from_file(self) -> None:
        """txt 파일을 읽고 곧바로 '측점', '전주번호', '타입', '에어조인트' 정보를 반환하는 함수"""

        data_list = []
        positions = []
        post_number_list = []
        type_list = []
        airjoint_list = []

        # 텍스트 파일(.txt) 읽기
        self.txtfile_handler.select_file("미리 정의된 전주 파일 선택", [("txt files", "*.txt"), ("All files", "*.*")])
        txt_filepath = self.txtfile_handler.get_filepath()

        df_curve = pd.read_csv(txt_filepath, sep=",", header=0, names=['측점', '전주번호', '타입', '에어조인트'])

        # 곡선 구간 정보 저장
        self.total_data_list = df_curve.to_records(index=False).tolist()
        self.pole_positions = df_curve['측점'].tolist()
        self.post_number_lst = list(zip(df_curve['측점'], df_curve['전주번호']))
        self.posttype_list = list(zip(df_curve['측점'], df_curve['타입']))
        self.airjoint_list = [(row['측점'], row['에어조인트']) for _, row in df_curve.iterrows() if row['에어조인트'] != '일반개소']

    # GET 메소드 추가
    def get_all_pole_data(self):
        """전주 관련 모든 데이터를 반환"""
        return {
            "pole_positions": self.pole_positions,
            "airjoint_list": self.airjoint_list,
            "post_number_lst": self.post_number_lst,
            "posttype_list": self.posttype_list,
            "total_data_list": self.total_data_list,
        }

    def get_pole_positions(self):
        return self.pole_positions

    def get_airjoint_list(self):
        return self.airjoint_list

    def get_post_number_lst(self):
        return self.post_number_lst

    def get_post_type_list(self):
        return self.posttype_list

    def get_total_data_list(self):
        return self.total_data_list


class BaseFileHandler:
    """파일 처리를 위한 기본 클래스 (공통 기능 포함)"""

    def __init__(self):
        self.filepath = None
        self.filename = None
        self.file_data = None

    def select_file(self, title: str, file_types: list[tuple[str, str]]):
        """공통 파일 선택 메서드"""
        logger.debug(f"{title} 파일 선택 창을 엽니다.")
        root = tk.Tk()
        root.withdraw()  # Tkinter 창 숨기기
        file_path = filedialog.askopenfilename(title=title, filetypes=file_types)

        if file_path:
            self.filepath = file_path
            self.filename = os.path.basename(file_path)  # 파일명 추출
            logger.info(f"파일이 선택되었습니다: {self.filename}")
        else:
            logger.warning("파일을 선택하지 않았습니다.")

    def get_filepath(self):
        """파일 경로 반환"""
        return self.filepath

    def get_filename(self):
        """파일 이름 반환"""
        return self.filename

    def get_file_extension(self):
        """파일 확장자 반환"""
        if not self.filepath:
            logger.warning("파일 경로가 설정되지 않았습니다.")
            return None
        return os.path.splitext(self.filepath)[-1].lower()

    def get_file_size(self):
        """파일 크기 반환 (바이트 단위)"""
        if not self.filepath:
            logger.warning("파일 경로가 설정되지 않았습니다.")
            return None
        return os.path.getsize(self.filepath)

    def get_creation_time(self):
        """파일의 생성 날짜 반환"""
        if not self.filepath:
            logger.warning("파일 경로가 설정되지 않았습니다.")
            return None
        creation_time = os.path.getctime(self.filepath)
        return datetime.fromtimestamp(creation_time)

    def get_modification_time(self):
        """파일의 마지막 수정 날짜 반환"""
        if not self.filepath:
            logger.warning("파일 경로가 설정되지 않았습니다.")
            return None
        modification_time = os.path.getmtime(self.filepath)
        return datetime.fromtimestamp(modification_time)

    def read_file_content(self, encoding='utf-8'):
        """파일 내용 읽기"""
        if not self.filepath:
            logger.warning("파일 경로가 설정되지 않았습니다.")
            return None
        try:
            with open(self.filepath, 'r', encoding=encoding) as file:
                self.file_data = file.read()  # 파일 내용 읽기
            logger.info(f"파일 {self.filepath} 읽기 완료.")
        except Exception as e:
            logger.error(f"파일 읽기 중 오류 발생: {e}", exc_info=True)
            return None

    def get_data(self):
        #  파일 내용 반환
        return self.file_data

    def write_to_file(self, data):
        """파일에 데이터 쓰기"""
        if not self.filepath:
            logger.warning("파일 경로가 설정되지 않았습니다.")
            return False
        try:
            with open(self.filepath, 'w', encoding='utf-8') as file:
                file.write(data)
            logger.info(f"파일에 데이터가 성공적으로 저장되었습니다.")
            return True
        except Exception as e:
            logger.error(f"파일 쓰기 중 오류 발생: {e}", exc_info=True)
            return False

    def file_exists(self):
        """파일 존재 여부 확인"""
        if not self.filepath:
            logger.warning("파일 경로가 설정되지 않았습니다.")
            return False
        return os.path.exists(self.filepath)

    def delete_file(self):
        """파일 삭제"""
        if not self.filepath:
            logger.warning("파일 경로가 설정되지 않았습니다.")
            return False
        try:
            os.remove(self.filepath)
            logger.info(f"파일이 성공적으로 삭제되었습니다: {self.filepath}")
            return True
        except Exception as e:
            logger.error(f"파일 삭제 중 오류 발생: {e}", exc_info=True)
            return False


class TxTFileHandler(BaseFileHandler):
    """
    TxTFileHandler 클래스는 BaseFileHandler클래스를 상속받아 텍스트 파일을 처리하는 기능을 제공합니다.
    이 클래스는 파일을 선택하고, 인코딩을 자동으로 감지한 후 파일을 읽거나,
    특정 구간 데이터를 찾아 반환하는 메소드를 포함합니다.
    """

    def __init__(self):
        """TxTFileHandler 객체를 초기화합니다."""
        super().__init__()
        self.file_data = None  # 텍스트 리스트

        logger.debug("TxTFileHandler 객체가 초기화되었습니다.")

    def process_file(self):
        """파일을 선택하고 읽고 인코딩을 감지하여 데이터를 반환하는 통합 프로세스"""
        logger.info("파일 선택을 시작합니다.")
        super().select_file("TXT 파일 선택", [("Text files", "*.txt"), ("All files", "*.*")])  # 파일 선택후 filepath저장

        if not self.filepath:
            logger.warning("파일을 선택하지 않았습니다.")
            return []  # 파일을 선택하지 않은 경우
        try:
            encoding = self.detect_encoding(self.filepath)
            logger.info(f"인코딩 감지: {encoding}")

            self.read_file_content(encoding)  # 파일 읽기
            super().get_data()
        except Exception as e:
            logger.error(f"파일 처리 중 오류 발생: {e}", exc_info=True)
            return []

    def process_info(self, columns=None, delimiter=',', include_cant=False):
        """txt 파일을 읽고 선택적 열(column) 데이터를 반환하는 함수"""
        super().select_file("TXT 파일 선택", [("Text files", "*.txt"), ("All files", "*.*")])

        if columns is None:
            # 기본적인 columns 이름 설정
            if include_cant:
                columns = ['sta', 'radius', 'cant']
            else:
                columns = ['sta', 'radius']

        curve_list = []

        # 텍스트 파일(.txt) 읽기
        try:
            df_curve = pd.read_csv(self.filepath, sep=delimiter, header=None, names=columns)
        except Exception as e:
            logger.error(f"파일 읽는 중 오류 발생: {e}", exc_info=True)
            return []

        # 데이터 처리
        for _, row in df_curve.iterrows():
            curve_data = tuple(row[col] for col in columns)
            curve_list.append(curve_data)

        return curve_list

    def read_file_content(self, encoding='utf-8'):
        """파일을 실제로 읽고 데이터를 처리하는 메소드(부모 메소드오버라이딩"""
        super().read_file_content()

        if self.file_data is not None:
            self.file_data = self.file_data.splitlines()  # 줄 단위로 리스트 생성

            logger.info(f"파일 {self.filepath} 읽기 완료.")
        else:
            logger.warning("파일을 읽을 수 없습니다.")
            return []

    @staticmethod
    def detect_encoding(file_path):
        """파일의 인코딩을 자동 감지하는 함수"""
        logger.debug(f"파일 {file_path}의 인코딩을 감지합니다.")
        try:
            with open(file_path, "rb") as f:
                raw_data = f.read()
                detected = chardet.detect(raw_data)
                encoding = detected["encoding"]
                if encoding is None:
                    logger.error("파일 인코딩을 감지할 수 없습니다.")
                    return None
                logger.info(f"감지된 인코딩: {encoding}")
                return encoding
        except Exception as e:
            logger.error(f"인코딩 감지 중 오류 발생: {e}")
            return None

    @staticmethod
    def get_column_count(lst):
        """파일에서 최대 열 갯수를 추출하는 함수"""
        max_columns = 0
        for line in lst:
            try:
                parts = line.split(',')
                max_columns = max(max_columns, len(parts))
            except Exception as e:
                logger.error(f"오류 발생: {e}")
        logger.info(f"최대 열 갯수: {max_columns}")
        return max_columns


class PolylineHandler(TxTFileHandler):
    def __init__(self):
        super().__init__()
        self.points = None

    def load_polyline(self):
        super().select_file("bve좌표 파일 선택", [("txt files", "*.txt"), ("All files", "*.*")])

    def convert_txt_to_polyline(self):
        """3D 좌표를 읽어오는 메소드"""
        # 파일을 처리하여 데이터를 가져옵니다.
        self.load_polyline()
        super().read_file_content()

        data = self.file_data
        points = []
        for line in data:
            # 쉼표로 구분된 값을 읽어서 float로 변환
            try:
                x, y, z = map(float, line.strip().split(','))
                points.append((x, y, z))
            except ValueError:
                logger.warning(f"잘못된 형식의 데이터가 발견되었습니다: {line.strip()}")

        self.points = points

    def get_polyline(self):
        """읽어온 3D 좌표를 반환하는 메소드"""
        return self.points


class ExcelFileHandler(BaseFileHandler):
    """
    ExcelFileHandler 클래스는 BaseFileHandler 클래스를 상속받아 엑셀 파일을 처리하는 기능을 제공합니다.
    이 클래스는 파일을 선택하고, 파일을 읽거나, 특정 구간 데이터를 찾아 반환하는 메소드를 포함합니다.
    """

    def __init__(self):
        super().__init__()
        self.excel_BRIDGE_Data = None
        self.excel_TUNNEL_Data = None
        logger.debug("ExcelFileHandler 객체가 초기화되었습니다.")

    def load_excel(self):
        """엑셀 파일을 선택하는 메소드"""
        super().select_file("엑셀 파일 선택", [("EXCEL files", "*.xlsx"), ("All files", "*.*")])

    def read_excel(self):
        """엑셀 파일을 읽는 메소드"""
        if not self.filepath:
            logger.warning("엑셀 파일 경로가 설정되지 않았습니다.")
            return None

        try:
            # xlsx 파일 읽기
            self.excel_BRIDGE_Data = pd.read_excel(self.filepath, sheet_name='교량', header=0)  # 첫 번째 행을 헤더로 사용
            self.excel_TUNNEL_Data = pd.read_excel(self.filepath, sheet_name='터널', header=0)
            logger.info("엑셀 파일이 성공적으로 읽혔습니다.")
        except FileNotFoundError:
            logger.error(f"엑셀 파일을 찾을 수 없습니다: {self.filepath}")
            return None
        except ValueError as e:
            logger.error(f"엑셀 파일 처리 중 오류가 발생했습니다: {e}")
            return None
        except Exception as e:
            logger.error(f"알 수 없는 오류 발생: {e}", exc_info=True)
            return None

    def process_structure_data(self):
        """교량과 터널 구간 정보를 처리하는 메소드"""
        self.load_excel()
        self.read_excel()

        if self.excel_BRIDGE_Data is None or self.excel_TUNNEL_Data is None:
            logger.warning("엑셀 데이터가 로드되지 않았습니다.")
            return None

        structure_dic = {'bridge': [], 'tunnel': []}

        # 첫 번째 행을 열 제목으로 설정
        self.excel_BRIDGE_Data.columns = ['br_NAME', 'br_START_STA', 'br_END_STA', 'br_LENGTH']
        self.excel_TUNNEL_Data.columns = ['tn_NAME', 'tn_START_STA', 'tn_END_STA', 'tn_LENGTH']

        try:
            # 교량 구간과 터널 구간 정보
            for _, row in self.excel_BRIDGE_Data.iterrows():
                structure_dic['bridge'].append((row['br_START_STA'], row['br_END_STA']))

            for _, row in self.excel_TUNNEL_Data.iterrows():
                structure_dic['tunnel'].append((row['tn_START_STA'], row['tn_END_STA']))

            logger.info("교량과 터널 정보가 성공적으로 처리되었습니다.")
        except Exception as e:
            logger.error(f"구조 데이터 처리 중 오류 발생: {e}", exc_info=True)
            return None

        return structure_dic


class Structure:
    def __init__(self, name, start, end, length):
        self.name = name
        self.start = start
        self.end = end
        self.length = length

    def create_Structure(self):
        pass


class Bridge(Structure):
    """교량 정보를 저장하는 클래스"""
    super().__init__('a', 'b', 'c', 'd')


class MainProcess:
    def __init__(self, params):
        self.params = params
        self.pole_data = DATA(params)
        self.processor = PoleDataProcessor(self.pole_data)

    def run(self):
        pole_data_lines = self.processor.process_pole_data()
        poledata_filename = '전주.txt'
        buffered_write(poledata_filename, pole_data_lines)


# GUI 구현
class PoleDataGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("전주 처리 프로그램")
        self.geometry("400x400")

        # 설계속도 선택 (150, 250, 350)
        self.design_speed_label = tk.Label(self, text="설계속도:")
        self.design_speed_label.pack(pady=5)

        self.design_speed_values = ['150', '250', '350']
        self.design_speed_var = tk.StringVar()

        self.design_speed_combobox = ttk.Combobox(
            self, textvariable=self.design_speed_var, values=self.design_speed_values, state="readonly"
        )
        self.design_speed_combobox.pack(pady=5)

        # 기본값 설정 (첫 번째 값)
        self.design_speed_combobox.current(0)  # 기본값을 150으로 설정

        # 프로그램 모드 (1: 랜덤, 2: 기존)
        self.select_mode_label = tk.Label(self, text="모드 선택:")
        self.select_mode_label.pack(pady=5)

        self.select_mode_var = tk.IntVar(value=1)
        self.mode_random = ttk.Radiobutton(self, text="랜덤 (1)", variable=self.select_mode_var, value=1)
        self.mode_existing = ttk.Radiobutton(self, text="기존 (2)", variable=self.select_mode_var, value=2)
        self.mode_random.pack()
        self.mode_existing.pack()

        # 선로 수 (1 or 2)
        self.line_count_label = tk.Label(self, text="선로 수:")
        self.line_count_label.pack(pady=5)

        self.line_count_var = tk.IntVar(value=1)
        self.line_count_single = ttk.Radiobutton(self, text="1 (단선)", variable=self.line_count_var, value=1)
        self.line_count_double = ttk.Radiobutton(self, text="2 (복선)", variable=self.line_count_var, value=2)
        self.line_count_single.pack()
        self.line_count_double.pack()

        # 선로중심간격 (숫자만 입력 가능)
        self.line_offset_label = tk.Label(self, text="선로중심간격:")
        self.line_offset_label.pack(pady=5)

        self.line_offset_var = tk.StringVar()
        self.line_offset_entry = tk.Entry(self, textvariable=self.line_offset_var, validate="key")
        self.line_offset_entry.pack(pady=5)

        # 폴 방향 (-1 or 1)
        self.pole_direction_label = tk.Label(self, text="폴 방향:")
        self.pole_direction_label.pack(pady=5)

        self.pole_direction_var = tk.IntVar(value=1)
        self.pole_direction_left = ttk.Radiobutton(self, text="-1 (좌측)", variable=self.pole_direction_var, value=-1)
        self.pole_direction_right = ttk.Radiobutton(self, text="1 (우측)", variable=self.pole_direction_var, value=1)
        self.pole_direction_left.pack()
        self.pole_direction_right.pack()

        # 실행 버튼
        self.run_button = tk.Button(self, text="실행", command=self.run_program)
        self.run_button.pack(pady=20)

    def run_program(self):
        try:
            # 사용자 입력값 가져오기
            design_speed = int(self.design_speed_var.get())
            select_mode = int(self.select_mode_var.get())
            line_count = int(self.line_count_var.get())
            line_offset = float(self.line_offset_var.get())
            pole_direction = int(self.pole_direction_var.get())

            logger.info(f"사용자 입력값 확인:")
            logger.info(f"design_speed = {design_speed}")
            logger.info(f"select_mode = {select_mode}")
            logger.info(f"line_count = {line_count}")
            logger.info(f"line_offset = {line_offset}")
            logger.info(f"pole_direction = {pole_direction}")

            # 파일 및 데이터 로드
            txtfile_handler = TxTFileHandler()
            curvelist_handler = TxTFileHandler()
            pitchlist_handler = TxTFileHandler()
            structure_list_handler = ExcelFileHandler()

            polyline_handler = PolylineHandler()

            structure_list = structure_list_handler.process_structure_data()
            messagebox.showinfo('txt파일 선택', 'curve_info파일을 선택해주세요')
            curvelist = curvelist_handler.process_info(include_cant=True)  # curve_info
            messagebox.showinfo('txt파일 선택', 'pitch_info파일을 선택해주세요')
            pitchlist = pitchlist_handler.process_info()

            messagebox.showinfo('txt파일 선택', 'bve 좌표 파일을 선택해주세요.')
            polyline_handler.convert_txt_to_polyline()
            polyline = polyline_handler.get_data()

            curve_info_file_path = curvelist_handler.get_filepath()
            curve_info_content = curvelist_handler.read_file_content()
            curve_info_list = curvelist_handler.get_data()

            last_block = find_last_block(curve_info_list)
            # 폴 포지션 관리 클래스
            pole_position_manager = PolePositionManager(select_mode, 0, last_block // 1000, txtfile_handler)
            pole_position_manager.generate_positions()
            pole_data = pole_position_manager.get_all_pole_data()

            pole_positions = pole_data["pole_positions"]
            airjoint_list = pole_data["airjoint_list"]
            pole_type_list = pole_data["posttype_list"]
            pole_number_list = pole_data["post_number_lst"]

            logger.info('찾은 마지막 블럭 : {last_block}')
            # 데이터 저장 및 전주 처리
            params = create_dic(pole_positions, structure_list, curvelist, pitchlist,
                                design_speed, airjoint_list, polyline, pole_type_list, pole_number_list)
            main_process = MainProcess(params)
            main_process.run()

            messagebox.showinfo("성공", "전주 처리 완료!")
        except Exception as e:
            messagebox.showerror("오류", f"문제가 발생했습니다: {e}")
            logger.error(f"파일 및 데이터 로드 중 오류 발생: {e}", exc_info=True)


def find_last_block(data):
    last_block = None  # None으로 초기화하여 값이 없을 때 오류 방지

    for line in data:
        if isinstance(line, str):  # 문자열인지 확인
            match = re.search(r'(\d+),', line)
            if match:
                last_block = int(match.group(1))  # 정수 변환하여 저장

    return last_block  # 마지막 블록 값 반환


def create_new_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()

    return doc, msp


def crate_pegging_plan_mast_and_bracket(doc, msp, polyline, positions, structure_list, curve_list, pitchlist,
                                        airjoint_list):
    post_number_lst = generate_postnumbers(positions)
    polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]

    # 전주 데이터 구성
    pole_data = format_pole_data(DESIGNSPEED)

    for i in range(len(positions) - 1):
        pos, next_pos = positions[i], positions[i + 1]
        currentspan = next_pos - pos  # 현재 경간
        current_structure = isbridge_tunnel(pos, structure_list)  # 현재 구조물
        current_curve, R, c = iscurve(pos, curve_list)  # 현재 곡선
        current_slope, pitch = isslope(pos, pitchlist)  # 현재 구배
        current_airjoint = check_isairjoint(pos, airjoint_list)  # 현재 에어조인트
        post_number = find_post_number(post_number_lst, pos)  # 전주번호
        gauge = get_pole_gauge(DESIGNSPEED, current_structure)  # 구조물 offset
        _, mast_name = get_mast_type(DESIGNSPEED, current_structure)
        # 해당 구조물에 대한 전주 데이터 가져오기 (없으면 '토공' 기본값 사용)
        station_data = pole_data.get(current_structure, pole_data.get('토공', {}))

        # '교량' 같은 구간일 경우, 곡선 여부에 따라 데이터 선택
        if isinstance(station_data, dict) and '직선' in station_data:
            station_data = station_data.get('곡선' if current_curve == '곡선' else '직선', {})

        # 필요한 데이터 추출 (기본값 설정)
        I_type = station_data.get('I_type', '기본_I_type')
        O_type = station_data.get('O_type', '기본_O_type')
        I_bracket = station_data.get('I_bracket', '기본_I_bracket')
        O_bracket = station_data.get('O_bracket', '기본_O_bracket')

        # 홀수/짝수에 맞는 전주 데이터 생성
        pole_type = I_type if i % 2 == 1 else O_type
        bracket_type = I_bracket if i % 2 == 1 else O_bracket

        # 전주 좌표 반환
        pos_coord, vector_pos = return_pos_coord(polyline_with_sta, pos)  # 전주 측점 좌표와 벡터
        # offset 적용 좌표
        pos_coord_with_offset = calculate_offset_point(vector_pos, pos_coord, gauge)
        char_height = 3 * H_scale

        if current_airjoint:
            """에어조인트 각 구간별 브래킷 추가"""
            if current_airjoint == AirJoint.START.value:
                # 브래킷텍스트
                msp.add_mtext(f"{post_number}\n{pos}\n{bracket_type}\n{mast_name}",
                              dxfattribs={'insert': pos_coord_with_offset, 'char_height': char_height, 'layer': '브래킷',
                                          'color': 6})
                msp.add_line(pos_coord, pos_coord_with_offset, dxfattribs={'layer': '브래킷', 'color': 6})
            elif current_airjoint == AirJoint.POINT_2.value:
                first_bracetl_pos = pos - 0.5
                second_brakcet_pos = pos + 0.5

                first_bracetl_coord, first_bracetl_vector = return_pos_coord(polyline_with_sta,
                                                                             first_bracetl_pos)  # 전주 측점 좌표와 벡터
                second_bracetl_coord, second_bracetl_vector = return_pos_coord(polyline_with_sta,
                                                                               second_brakcet_pos)  # 전주 측점 좌표와 벡터

                first_bracetl_coord_with_offset = calculate_offset_point(first_bracetl_vector, first_bracetl_coord,
                                                                         gauge)
                second_bracetl_coord_with_offset = calculate_offset_point(second_bracetl_vector, second_bracetl_coord,
                                                                          gauge)
                # 브래킷 텍스트
                msp.add_mtext(f"{post_number}\n{pos}\nF(S), AJ-I\n{mast_name}",
                              dxfattribs={'insert': pos_coord_with_offset, 'char_height': char_height, 'layer': '브래킷',
                                          'color': 6})

                msp.add_line(first_bracetl_coord, first_bracetl_coord_with_offset,
                             dxfattribs={'layer': '브래킷', 'color': 6})
                msp.add_line(second_bracetl_coord, second_bracetl_coord_with_offset,
                             dxfattribs={'layer': '브래킷', 'color': 6})

            elif current_airjoint == AirJoint.MIDDLE.value:
                # MIDDLE 구간 처리
                first_bracetl_pos = pos - 0.8
                second_brakcet_pos = pos + 0.8

                first_bracetl_coord, first_bracetl_vector = return_pos_coord(polyline_with_sta,
                                                                             first_bracetl_pos)  # 전주 측점 좌표와 벡터
                second_bracetl_coord, second_bracetl_vector = return_pos_coord(polyline_with_sta,
                                                                               second_brakcet_pos)  # 전주 측점 좌표와 벡터

                first_bracetl_coord_with_offset = calculate_offset_point(first_bracetl_vector, first_bracetl_coord,
                                                                         gauge)
                second_bracetl_coord_with_offset = calculate_offset_point(second_bracetl_vector, second_bracetl_coord,
                                                                          gauge)

                # 브래킷 텍스트
                msp.add_mtext(f"{post_number}\n{pos}\nAJ-O, AJ-O\n{mast_name}",
                              dxfattribs={'insert': pos_coord_with_offset, 'char_height': char_height, 'layer': '브래킷',
                                          'color': 6})

                msp.add_line(first_bracetl_coord, first_bracetl_coord_with_offset,
                             dxfattribs={'layer': '브래킷', 'color': 6})
                msp.add_line(second_bracetl_coord, second_bracetl_coord_with_offset,
                             dxfattribs={'layer': '브래킷', 'color': 6})

            elif current_airjoint == AirJoint.POINT_4.value:
                first_bracetl_pos = pos - 0.5
                second_brakcet_pos = pos + 0.5

                first_bracetl_coord, first_bracetl_vector = return_pos_coord(polyline_with_sta,
                                                                             first_bracetl_pos)  # 전주 측점 좌표와 벡터
                second_bracetl_coord, second_bracetl_vector = return_pos_coord(polyline_with_sta,
                                                                               second_brakcet_pos)  # 전주 측점 좌표와 벡터

                first_bracetl_coord_with_offset = calculate_offset_point(first_bracetl_vector, first_bracetl_coord,
                                                                         gauge)
                second_bracetl_coord_with_offset = calculate_offset_point(second_bracetl_vector, second_bracetl_coord,
                                                                          gauge)

                msp.add_line(first_bracetl_coord, first_bracetl_coord_with_offset,
                             dxfattribs={'layer': '브래킷', 'color': 6})
                msp.add_line(second_bracetl_coord, second_bracetl_coord_with_offset,
                             dxfattribs={'layer': '브래킷', 'color': 6})

                # 브래킷 텍스트
                msp.add_mtext(f"{post_number}\n{pos}\nAJ-O, F(L)\n{mast_name}",
                              dxfattribs={'insert': pos_coord_with_offset, 'char_height': char_height, 'layer': '브래킷',
                                          'color': 6})

            elif current_airjoint == AirJoint.END.value:
                # 브래킷텍스트
                msp.add_mtext(f"{post_number}\n{pos}\n{bracket_type}\n{mast_name}",
                              dxfattribs={'insert': pos_coord_with_offset, 'char_height': char_height, 'layer': '브래킷',
                                          'color': 6})
                # 브래킷
                msp.add_line(pos_coord, pos_coord_with_offset, dxfattribs={'layer': '브래킷', 'color': 6})
        else:
            # 브래킷
            msp.add_line(pos_coord, pos_coord_with_offset, dxfattribs={'layer': '브래킷', 'color': 6})
            # 브래킷텍스트
            msp.add_mtext(f"{post_number}\n{pos}\n{bracket_type}\n{mast_name}",
                          dxfattribs={'insert': pos_coord_with_offset, 'char_height': char_height, 'layer': '브래킷',
                                      'color': 6})

        # 전주번호
        # msp.add_text(post_number, dxfattribs={'insert':pos_coord_with_offset, 'height': 3, 'layer': '전주번호', 'color' : 4})
        # 전주
        msp.add_circle(pos_coord_with_offset, radius=1.5 * H_scale, dxfattribs={'layer': '전주', 'color': 4})

    # 선형 플롯
    polyline_points = [(point[1], point[2]) for point in polyline_with_sta]
    msp.add_lwpolyline(polyline_points, close=False, dxfattribs={'layer': '선형', 'color': 1})

    return doc, msp


def crate_pegging_plan_wire(doc, msp, polyline, positions, structure_list, curve_list, pitchlist, airjoint_list):
    post_number_lst = generate_postnumbers(positions)
    polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]

    # 전주 데이터 구성
    pole_data = format_pole_data(DESIGNSPEED)

    x, y = get_bracket_coordinates(DESIGNSPEED, 'AJ형_시점')
    x1, y1 = get_bracket_coordinates(DESIGNSPEED, 'F형_시점')
    x2, y2 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간1')
    x3, y3 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간2')
    x4, y4 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_끝')
    x5, y5 = get_bracket_coordinates(DESIGNSPEED, 'F형_끝')

    for i in range(len(positions) - 1):
        pos, next_pos = positions[i], positions[i + 1]
        currentspan = next_pos - pos  # 현재 경간
        current_structure = isbridge_tunnel(pos, structure_list)  # 현재 구조물
        next_structure = isbridge_tunnel(next_pos, structure_list)
        current_curve, R, c = iscurve(pos, curve_list)  # 현재 곡선
        current_slope, pitch = isslope(pos, pitchlist)  # 현재 구배
        current_airjoint = check_isairjoint(pos, airjoint_list)  # 현재 에어조인트
        post_number = find_post_number(post_number_lst, pos)  # 전주번호
        gauge = get_pole_gauge(DESIGNSPEED, current_structure)  # 구조물 offset
        next_gauge = get_pole_gauge(DESIGNSPEED, next_structure)  # 다음 구조물 offset
        _, mast_name = get_mast_type(DESIGNSPEED, current_structure)  # 전주형식
        # 해당 구조물에 대한 전주 데이터 가져오기 (없으면 '토공' 기본값 사용)
        station_data = pole_data.get(current_structure, pole_data.get('토공', {}))

        # '교량' 같은 구간일 경우, 곡선 여부에 따라 데이터 선택
        if isinstance(station_data, dict) and '직선' in station_data:
            station_data = station_data.get('곡선' if current_curve == '곡선' else '직선', {})

        # 필요한 데이터 추출 (기본값 설정)
        I_type = station_data.get('I_type', '기본_I_type')
        O_type = station_data.get('O_type', '기본_O_type')
        I_bracket = station_data.get('I_bracket', '기본_I_bracket')
        O_bracket = station_data.get('O_bracket', '기본_O_bracket')

        # 홀수/짝수에 맞는 전주 데이터 생성
        pole_type = I_type if i % 2 == 1 else O_type
        bracket_type = I_bracket if i % 2 == 1 else O_bracket

        # 편위와 직선구간 각도
        current_stagger, _ = get_lateral_offset_and_angle(i, currentspan)
        next_stagger, _ = get_lateral_offset_and_angle(i + 1, currentspan)

        # 전주 좌표 반환
        pos_coord, vector_pos = return_pos_coord(polyline_with_sta, pos)  # 전주 측점 좌표와 벡터
        next_coord, next_vector = return_pos_coord(polyline_with_sta, next_pos)  # 전주 측점 좌표와 벡터

        # 전선 시점 좌표
        wire_coord = calculate_offset_point(vector_pos, pos_coord, current_stagger)
        next_wire_coord = calculate_offset_point(next_vector, next_coord, next_stagger)

        if current_airjoint:
            """에어조인트 각 구간별 브래킷 추가"""
            if current_airjoint == AirJoint.START.value:
                # 무효선
                inactive_wire_start_coord = calculate_offset_point(vector_pos, pos_coord, gauge)
                inactive_wire_end_coord = calculate_offset_point(next_vector, next_coord, x1)
                msp.add_line(inactive_wire_start_coord, inactive_wire_end_coord,
                             dxfattribs={'layer': '전차선', 'color': 3})

                # 본선
                wire_end_coord = calculate_offset_point(next_vector, next_coord, x)
                msp.add_line(wire_coord, wire_end_coord, dxfattribs={'layer': '전차선', 'color': 3})
            elif current_airjoint == AirJoint.POINT_2.value:
                # 무효선
                inactive_wire_start_coord = calculate_offset_point(vector_pos, pos_coord, x1)
                inactive_wire_end_coord = calculate_offset_point(next_vector, next_coord, x2)
                msp.add_line(inactive_wire_start_coord, inactive_wire_end_coord,
                             dxfattribs={'layer': '전차선', 'color': 3})

                # 본선
                wire_start_coord = calculate_offset_point(vector_pos, pos_coord, x)
                wire_end_coord = calculate_offset_point(next_vector, next_coord, x3)
                msp.add_line(wire_start_coord, wire_end_coord, dxfattribs={'layer': '전차선', 'color': 3})

            elif current_airjoint == AirJoint.MIDDLE.value:
                # 무효선
                inactive_wire_start_coord = calculate_offset_point(vector_pos, pos_coord, x2)
                inactive_wire_end_coord = calculate_offset_point(next_vector, next_coord, x4)
                msp.add_line(inactive_wire_start_coord, inactive_wire_end_coord,
                             dxfattribs={'layer': '전차선', 'color': 3})

                # 본선
                wire_start_coord = calculate_offset_point(vector_pos, pos_coord, x3)
                wire_end_coord = calculate_offset_point(next_vector, next_coord, x5)
                msp.add_line(wire_start_coord, wire_end_coord, dxfattribs={'layer': '전차선', 'color': 3})

            elif current_airjoint == AirJoint.POINT_4.value:
                # 무효선
                inactive_wire_start_coord = calculate_offset_point(vector_pos, pos_coord, x5)
                inactive_wire_end_coord = calculate_offset_point(next_vector, next_coord, next_gauge)
                msp.add_line(inactive_wire_start_coord, inactive_wire_end_coord,
                             dxfattribs={'layer': '전차선', 'color': 3})

                # 본선
                wire_start_coord = calculate_offset_point(vector_pos, pos_coord, x4)
                wire_end_coord = calculate_offset_point(next_vector, next_coord, next_stagger)
                msp.add_line(wire_start_coord, wire_end_coord, dxfattribs={'layer': '전차선', 'color': 3})
            elif current_airjoint == AirJoint.END.value:
                msp.add_line(wire_coord, next_wire_coord, dxfattribs={'layer': '전차선', 'color': 3})
        else:
            msp.add_line(wire_coord, next_wire_coord, dxfattribs={'layer': '전차선', 'color': 3})
    return doc, msp


def draw_feeder_wire_plan(msp, pos_coord, end_pos, current_structure, next_structure):
    pass


def create_pegging_profile_mast_and_bracket(doc, msp, polyline, positions, structure_list, curve_list, pitchlist,
                                            airjoint_list):
    post_number_lst = generate_postnumbers(positions)
    polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]

    # 전주 데이터 구성
    pole_data = format_pole_data(DESIGNSPEED)

    char_height = 3 * H_scale
    for i in range(len(positions) - 1):
        pos, next_pos = positions[i], positions[i + 1]
        currentspan = next_pos - pos  # 현재 경간
        current_structure = isbridge_tunnel(pos, structure_list)  # 현재 구조물
        next_structure = isbridge_tunnel(next_pos, structure_list)  # 다음 구조물
        current_curve, R, c = iscurve(pos, curve_list)  # 현재 곡선
        current_slope, pitch = isslope(pos, pitchlist)  # 현재 구배
        current_airjoint = check_isairjoint(pos, airjoint_list)  # 현재 에어조인트
        current_pos_z = get_elevation_pos(pos, polyline_with_sta)  # 현재 전주의 z값
        next_pos_z = get_elevation_pos(next_pos, polyline_with_sta)  # 다음 전주의 z값
        post_number = find_post_number(post_number_lst, pos)  # 전주번호
        gauge = get_pole_gauge(DESIGNSPEED, current_structure)  # 구조물 offset
        _, mast_name = get_mast_type(DESIGNSPEED, current_structure)
        _, _, current_system_height, current_contact_height = get_contact_wire_and_massanger_wire_info(DESIGNSPEED,
                                                                                                       current_structure,
                                                                                                       currentspan)
        _, _, next_system_height, next_contact_height = get_contact_wire_and_massanger_wire_info(DESIGNSPEED,
                                                                                                 next_structure,
                                                                                                 currentspan)
        _, _, h1, h2, _, _ = initialrize_tenstion_device(pos, gauge, currentspan, current_contact_height,
                                                         current_system_height)
        h1 = h1 * V_scale
        h2 = h2 * V_scale

        # 스케일 적용된 높이
        # 스케일 적용된 높이 변환 (리스트 활용)
        current_system_height, current_contact_height, next_system_height, next_contact_height = [
            height * V_scale for height in
            (current_system_height, current_contact_height, next_system_height, next_contact_height)
        ]

        # 해당 구조물에 대한 전주 데이터 가져오기 (없으면 '토공' 기본값 사용)
        station_data = pole_data.get(current_structure, pole_data.get('토공', {}))

        # '교량' 같은 구간일 경우, 곡선 여부에 따라 데이터 선택
        if isinstance(station_data, dict) and '직선' in station_data:
            station_data = station_data.get('곡선' if current_curve == '곡선' else '직선', {})

        # 필요한 데이터 추출 (기본값 설정)
        I_type = station_data.get('I_type', '기본_I_type')
        O_type = station_data.get('O_type', '기본_O_type')
        I_bracket = station_data.get('I_bracket', '기본_I_bracket')
        O_bracket = station_data.get('O_bracket', '기본_O_bracket')

        # 홀수/짝수에 맞는 전주 데이터 생성
        pole_type = I_type if i % 2 == 1 else O_type
        bracket_type = I_bracket if i % 2 == 1 else O_bracket

        # 전주 좌표 반환
        pos_coord = pos, current_pos_z * V_scale  # 현재 전주 측점 좌표
        next_pos_coord = next_pos, next_pos_z * V_scale  # 다음 전주 측점 좌표

        # offset 적용 좌표
        # h1 전차선
        # h2 조가선

        if current_airjoint:
            """에어조인트 각 구간별 브래킷 추가"""
            if current_airjoint == AirJoint.START.value:
                # 브래킷텍스트
                msp.add_mtext(f"{post_number}\n{pos}\n{bracket_type}\n{mast_name}",
                              dxfattribs={'insert': pos_coord, 'char_height': char_height, 'layer': '브래킷', 'color': 6})
                # 브래킷

                draw_bracket_at_profile(msp, pos_coord, current_structure)
            elif current_airjoint == AirJoint.POINT_2.value:
                # 브래킷 텍스트 추가
                msp.add_mtext(f"{post_number}\n{pos}\n'F(S),AJ-I\n{mast_name}",
                              dxfattribs={'insert': pos_coord, 'char_height': char_height, 'layer': '브래킷', 'color': 6})

                # 브래킷1 (좌측으로 0.5 이동)
                draw_bracket_at_profile(msp, (pos_coord[0] - 0.5, pos_coord[1]), current_structure)

                # 브래킷2 (우측으로 0.5 이동)
                draw_bracket_at_profile(msp, (pos_coord[0] + 0.5, pos_coord[1]), current_structure)
                # 평행틀
                draw_spreader(msp, (pos_coord[0] - 0.5, pos_coord[1]))
                draw_spreader(msp, (pos_coord[0] + 0.5, pos_coord[1]))

            elif current_airjoint == AirJoint.MIDDLE.value:
                # 브래킷텍스트
                msp.add_mtext(f"{post_number}\n{pos}\n'AJ-O,AJ-O\n{mast_name}",
                              dxfattribs={'insert': pos_coord, 'char_height': char_height, 'layer': '브래킷', 'color': 6})
                # 브래킷1 (좌측으로 0.5 이동)
                draw_bracket_at_profile(msp, (pos_coord[0] - 0.8, pos_coord[1]), current_structure)

                # 브래킷2 (우측으로 0.5 이동)
                draw_bracket_at_profile(msp, (pos_coord[0] + 0.8, pos_coord[1]), current_structure)

                # 평행틀
                draw_spreader(msp, (pos_coord[0] - 0.8, pos_coord[1]))
                draw_spreader(msp, (pos_coord[0] + 0.8, pos_coord[1]))

            elif current_airjoint == AirJoint.POINT_4.value:
                # 브래킷텍스트
                msp.add_mtext(f"{post_number}\n{pos}\n'AJ-O,F(L)\n{mast_name}",
                              dxfattribs={'insert': pos_coord, 'char_height': char_height, 'layer': '브래킷', 'color': 6})
                # 브래킷1 (좌측으로 0.5 이동)
                draw_bracket_at_profile(msp, (pos_coord[0] - 0.5, pos_coord[1]), current_structure)

                # 브래킷2 (우측으로 0.5 이동)
                draw_bracket_at_profile(msp, (pos_coord[0] + 0.5, pos_coord[1]), current_structure)

                # 평행틀
                draw_spreader(msp, (pos_coord[0] - 0.5, pos_coord[1]))
                draw_spreader(msp, (pos_coord[0] + 0.5, pos_coord[1]))

            elif current_airjoint == AirJoint.END.value:
                # 브래킷
                draw_bracket_at_profile(msp, pos_coord, current_structure)
                # 브래킷텍스트
                msp.add_mtext(f"{post_number}\n{pos}\n{bracket_type}\n{mast_name}",
                              dxfattribs={'insert': pos_coord, 'char_height': char_height, 'layer': '브래킷', 'color': 6})
            # 전주
            else:
                print('an error accumnent in line e')
        else:
            # 브래킷
            draw_bracket_at_profile(msp, pos_coord, current_structure)
            # 브래킷텍스트
            msp.add_mtext(f"{post_number}\n{pos}\n{bracket_type}\n{mast_name}",
                          dxfattribs={'insert': pos_coord, 'char_height': char_height, 'layer': '브래킷', 'color': 6})
        # 전주
        draw_mast_for_profile(msp, mast_name, pos_coord, current_structure)
    # 종단선형
    draw_profile_alignmnet(msp, polyline_with_sta)

    return doc, msp


def create_pegging_profile_wire(doc, msp, polyline, positions, structure_list, curve_list, pitchlist,
                                airjoint_list):
    post_number_lst = generate_postnumbers(positions)
    polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]

    # 전주 데이터 구성
    pole_data = format_pole_data(DESIGNSPEED)

    char_height = 3 * H_scale
    for i in range(len(positions) - 1):
        pos, next_pos = positions[i], positions[i + 1]
        currentspan = next_pos - pos  # 현재 경간
        current_structure = isbridge_tunnel(pos, structure_list)  # 현재 구조물
        next_structure = isbridge_tunnel(next_pos, structure_list)  # 다음 구조물
        current_curve, R, c = iscurve(pos, curve_list)  # 현재 곡선
        current_slope, pitch = isslope(pos, pitchlist)  # 현재 구배
        current_airjoint = check_isairjoint(pos, airjoint_list)  # 현재 에어조인트
        current_pos_z = get_elevation_pos(pos, polyline_with_sta)  # 현재 전주의 z값
        next_pos_z = get_elevation_pos(next_pos, polyline_with_sta)  # 다음 전주의 z값
        post_number = find_post_number(post_number_lst, pos)  # 전주번호
        gauge = get_pole_gauge(DESIGNSPEED, current_structure)  # 구조물 offset
        _, mast_name = get_mast_type(DESIGNSPEED, current_structure)
        _, _, current_system_height, current_contact_height = get_contact_wire_and_massanger_wire_info(DESIGNSPEED,
                                                                                                       current_structure,
                                                                                                       currentspan)
        _, _, next_system_height, next_contact_height = get_contact_wire_and_massanger_wire_info(DESIGNSPEED,
                                                                                                 next_structure,
                                                                                                 currentspan)
        _, _, h1, h2, _, _ = initialrize_tenstion_device(pos, gauge, currentspan, current_contact_height,
                                                         current_system_height)
        h1 = h1 * V_scale
        h2 = h2 * V_scale

        # 스케일 적용된 높이
        # 스케일 적용된 높이 변환 (리스트 활용)
        current_system_height, current_contact_height, next_system_height, next_contact_height = [
            height * V_scale for height in
            (current_system_height, current_contact_height, next_system_height, next_contact_height)
        ]

        # 해당 구조물에 대한 전주 데이터 가져오기 (없으면 '토공' 기본값 사용)
        station_data = pole_data.get(current_structure, pole_data.get('토공', {}))

        # '교량' 같은 구간일 경우, 곡선 여부에 따라 데이터 선택
        if isinstance(station_data, dict) and '직선' in station_data:
            station_data = station_data.get('곡선' if current_curve == '곡선' else '직선', {})

        # 필요한 데이터 추출 (기본값 설정)
        I_type = station_data.get('I_type', '기본_I_type')
        O_type = station_data.get('O_type', '기본_O_type')
        I_bracket = station_data.get('I_bracket', '기본_I_bracket')
        O_bracket = station_data.get('O_bracket', '기본_O_bracket')

        # 홀수/짝수에 맞는 전주 데이터 생성
        pole_type = I_type if i % 2 == 1 else O_type
        bracket_type = I_bracket if i % 2 == 1 else O_bracket

        # 전주 좌표 반환
        pos_coord = pos, current_pos_z * V_scale  # 현재 전주 측점 좌표
        next_pos_coord = next_pos, next_pos_z * V_scale  # 다음 전주 측점 좌표

        # offset 적용 좌표
        # h1 전차선
        # h2 조가선

        if current_airjoint:
            """에어조인트 각 구간별 브래킷 추가"""
            if current_airjoint == AirJoint.START.value:

                # 무효선 좌표 계산
                y_offset = get_airjoint_xy(DESIGNSPEED, 'F형_시점')[1] * V_scale

                contact_start = (pos_coord[0], pos_coord[1] + h1)
                contact_end = (next_pos_coord[0], next_pos_coord[1] + next_contact_height + y_offset)

                massanger_start = (pos_coord[0], pos_coord[1] + h2)
                massanger_end = (next_pos_coord[0], next_pos_coord[1] + next_contact_height + next_system_height)

                # 무효선 그리기
                draw_msp_line(msp, contact_start, contact_end, layer_name='전차선', color=1)
                draw_msp_line(msp, massanger_start, massanger_end, layer_name='조가선', color=1)

                # 본선 그리기
                draw_contact_and_massanger_wire(msp, pos_coord, next_pos_coord, current_system_height,
                                                current_contact_height, next_system_height, next_contact_height)

            elif current_airjoint == AirJoint.POINT_2.value:
                # 무효선-하강
                # 무효선 좌표 계산
                y_offset = get_airjoint_xy(DESIGNSPEED, 'F형_시점')[1] * V_scale

                contact_start = (pos_coord[0], pos_coord[1] + current_contact_height + y_offset)
                contact_end = (next_pos_coord[0], next_pos_coord[1] + next_contact_height)

                massanger_start = (pos_coord[0], pos_coord[1] + current_contact_height + current_system_height)
                massanger_end = (next_pos_coord[0], next_pos_coord[1] + next_contact_height + next_system_height)

                # 무효선 그리기
                draw_msp_line(msp, contact_start, contact_end, layer_name='전차선', color=1)
                draw_msp_line(msp, massanger_start, massanger_end, layer_name='조가선', color=1)
                # 본선
                # 본선 그리기
                draw_contact_and_massanger_wire(msp, pos_coord, next_pos_coord, current_system_height,
                                                current_contact_height, next_system_height, next_contact_height)
            elif current_airjoint == AirJoint.MIDDLE.value:
                # 무효선 그리기
                draw_contact_and_massanger_wire(msp, pos_coord, next_pos_coord, current_system_height,
                                                current_contact_height, next_system_height, next_contact_height)

                y_offset = get_airjoint_xy(DESIGNSPEED, 'F형_시점')[1] * V_scale

                # 본선 상승
                contact_start = (pos_coord[0], pos_coord[1] + current_contact_height)
                contact_end = (next_pos_coord[0], next_pos_coord[1] + next_contact_height + y_offset)

                massanger_start = (pos_coord[0], pos_coord[1] + current_contact_height + current_system_height)
                massanger_end = (next_pos_coord[0], next_pos_coord[1] + next_contact_height + next_system_height)
                # 본선 그리기
                draw_msp_line(msp, contact_start, contact_end, layer_name='전차선', color=1)
                draw_msp_line(msp, massanger_start, massanger_end, layer_name='조가선', color=1)

            elif current_airjoint == AirJoint.POINT_4.value:
                y_offset = get_airjoint_xy(DESIGNSPEED, 'F형_시점')[1] * V_scale

                # 본선 상승
                contact_start = (pos_coord[0], pos_coord[1] + current_contact_height + y_offset)
                contact_end = (next_pos_coord[0], next_pos_coord[1] + h1)

                massanger_start = (pos_coord[0], pos_coord[1] + current_contact_height + current_system_height)
                massanger_end = (next_pos_coord[0], next_pos_coord[1] + h2)
                # 본선 그리기
                draw_msp_line(msp, contact_start, contact_end, layer_name='전차선', color=1)
                draw_msp_line(msp, massanger_start, massanger_end, layer_name='조가선', color=1)

                # 무효선
                draw_contact_and_massanger_wire(msp, pos_coord, next_pos_coord, current_system_height,
                                                current_contact_height, next_system_height, next_contact_height)
            else:
                # 본선
                draw_contact_and_massanger_wire(msp, pos_coord, next_pos_coord, current_system_height,
                                                current_contact_height, next_system_height, next_contact_height)
        else:
            # 전차선
            draw_contact_and_massanger_wire(msp, pos_coord, next_pos_coord, current_system_height,
                                            current_contact_height, next_system_height, next_contact_height)
        # 급전선
        draw_feeder_wire(msp, pos_coord, next_pos_coord, current_structure, next_structure)
        # 보호선
        draw_protect_wire(msp, pos_coord, next_pos_coord, current_structure, next_structure)

    return doc, msp


def get_airjoint_xy(DESIGNSPEED, content):
    return get_bracket_coordinates(DESIGNSPEED, content)


def draw_msp_rectangle(msp, origin, width, height, layer_name='0', color=0):
    p1 = (origin[0] + width / 2, origin[1] + height / 2)  # 오른쪽 위
    p2 = (p1[0] - width, p1[1])  # 왼쪽 위
    p3 = (p2[0], p2[1] - height)  # 왼쪽 아래
    p4 = (p1[0], p3[1])  # 오른쪽 아래

    # 사각형 그리기
    msp.add_lwpolyline([p1, p2, p3, p4, p1], dxfattribs={'layer': layer_name, 'color': color})


def draw_msp_line(msp, start_point, end_point, layer_name='0', color=0):
    msp.add_line(start_point, end_point, dxfattribs={'layer': layer_name, 'color': color})

    return msp


def draw_contact_and_massanger_wire(msp, start_pos, end_pos, system_height, contact_height, next_system_height,
                                    next_contact_height):
    """전차선 및 조가선 그리기"""
    # 전차선(컨택트 와이어) 시작과 끝 좌표 계산
    contact_wire_start_coord = (start_pos[0], start_pos[1] + contact_height)
    contact_wire_end_coord = (end_pos[0], end_pos[1] + next_contact_height)

    # 조가선(메신저 와이어) 시작과 끝 좌표 계산
    massanger_wire_start_coord = (contact_wire_start_coord[0], contact_wire_start_coord[1] + system_height)
    massanger_wire_end_coord = (contact_wire_end_coord[0], contact_wire_end_coord[1] + next_system_height)

    # Bulge 값 계산 (2H / L)
    chord_length = end_pos[0] - start_pos[0]  # 현의 길이
    sagitta = random.uniform(0, 0.5)  # 0 ~ 0.5 사이의 랜덤 Sagitta 값
    bulge = (2 * sagitta) / chord_length if chord_length != 0 else 0  # Bulge 값 계산

    # 전차선 추가
    msp.add_line(contact_wire_start_coord, contact_wire_end_coord, dxfattribs={'layer': '전차선', 'color': 3})

    # 조가선(메신저 와이어) 추가 (Bulge 적용)
    msp.add_lwpolyline(
        [(massanger_wire_start_coord[0], massanger_wire_start_coord[1], bulge),
         (massanger_wire_end_coord[0], massanger_wire_end_coord[1], 0)],
        format="xyb",  # x, y, bulge 형태로 추가
        close=False,
        dxfattribs={'layer': '조가선', 'color': 3}
    )

    return msp


def draw_feeder_wire(msp, start_pos, end_pos, current_structure, next_structure):
    """급전선(Feeder Wire) 그리기"""
    # 구조물별 급전선 높이 사전 정의
    feeder_wire_height_dict = {'토공': 7.23, '교량': 7.23, '터널': 5.48}

    # 현재 및 다음 구조물 높이 가져오기 (기본값: 토공)
    feeder_wire_start_height = feeder_wire_height_dict.get(current_structure, feeder_wire_height_dict['토공']) * V_scale
    feeder_wire_end_height = feeder_wire_height_dict.get(next_structure, feeder_wire_height_dict['토공']) * V_scale

    # 급전선 좌표 계산
    start_x, start_y = start_pos
    end_x, end_y = end_pos
    feeder_wire_start_coord = (start_x, start_y + feeder_wire_start_height)
    feeder_wire_end_coord = (end_x, end_y + feeder_wire_end_height)

    # Bulge 값 계산 (2H / L)
    chord_length = end_x - start_x  # 현의 길이
    sagitta = random.uniform(0, 0.8)  # 0 ~ 0.8 사이의 랜덤 Sagitta 값
    bulge = (2 * sagitta / chord_length) if chord_length != 0 else 0

    # DXF 폴리라인 추가
    msp.add_lwpolyline(
        [(start_x, feeder_wire_start_coord[1], bulge),
         (end_x, feeder_wire_end_coord[1], 0)],
        format="xyb",  # x, y, bulge 형태
        close=False,
        dxfattribs={'layer': '급전선', 'color': 2}
    )

    return msp


def draw_protect_wire(msp, start_pos, end_pos, current_structure, next_structure):
    # 보호선 높이 사전 정의
    wire_height_dict = {'토공': 4.887, '교량': 4.887, '터널': 5.56}

    # 구조물에 따른 보호선 높이 가져오기 (기본값 '토공')
    start_height = wire_height_dict.get(current_structure, wire_height_dict['토공']) * V_scale
    end_height = wire_height_dict.get(next_structure, wire_height_dict['토공']) * V_scale

    # 보호선 좌표 계산
    start_coord = (start_pos[0], start_pos[1] + start_height)
    end_coord = (end_pos[0], end_pos[1] + end_height)

    # Bulge 값 계산 (Sagitta 공식 적용)
    span_length = end_pos[0] - start_pos[0]
    sagitta = random.uniform(0, 0.8)  # 0~0.8 범위에서 랜덤 Sagitta 값
    bulge = 0 if span_length == 0 else (2 * sagitta) / span_length

    # 보호선 그리기
    msp.add_lwpolyline(
        [(start_coord[0], start_coord[1], bulge),
         (end_coord[0], end_coord[1], 0)],
        format="xyb",  # x, y, bulge 형태
        close=False,
        dxfattribs={'layer': '보호선', 'color': 11}
    )

    return msp


def draw_bracket_at_profile(msp, insert_point, current_structure):
    """가동 브래킷 종단면도 그리기"""
    # 파이프 치수 사전 정의
    tube_dimension_dict = {
        '토공': (6.3, 0.714, 0.386),
        '교량': (6.3, 0.714, 0.386),
        '터널': (5.748, 0.363, 0.386),
    }

    # 구조물에 따른 치수 가져오기 (기본값: 토공)
    top_tube_dim, main_pipe_dim, steady_arm_dim = tube_dimension_dict.get(
        current_structure, tube_dimension_dict['토공']
    )

    # 스케일 적용된 높이 계산
    top_tube_height = top_tube_dim * V_scale
    main_pipe_height = main_pipe_dim * V_scale
    steady_arm_height = steady_arm_dim * V_scale

    # 좌표 계산
    x, y = insert_point
    top_tube = (x, y + top_tube_height)
    main_pipe = (x, y + top_tube_height - main_pipe_height)
    steady_arm = (x, y + top_tube_height - main_pipe_height - steady_arm_height)

    # 브래킷 원 추가
    for position in [top_tube, main_pipe, steady_arm]:
        msp.add_circle(position, radius=0.03 * V_scale, dxfattribs={'layer': '브래킷', 'color': 6})

    return msp


def get_numberlist(unit, start, end):
    num_list = []
    station_count = end // unit
    """unit 간격으로 start부터 end까지 숫자 리스트 생성(예시 111, 125, 150,175,186)"""
    i = 0
    num_list.append(start)
    for i in range(station_count):
        if i * unit >= start:
            num_list.append(i * unit)
    num_list.append(end)
    return num_list


def draw_profile_alignmnet(msp, polyline):
    # 폴리선 플롯
    polyline_x = [point[0] for point in polyline]
    polyline_y = [point[3] * V_scale for point in polyline]

    polyline_points = list(zip(polyline_x, polyline_y))  # 올바른 zip 사용
    msp.add_lwpolyline(polyline_points, close=False, dxfattribs={'layer': '종단선형', 'color': 1})

    return msp


def draw_spreader(msp, origin):
    p1 = origin[0] + 0.075, origin[1]
    p2 = p1[0], p1[1] + 1.2
    p3 = p2[0] - 0.15, p2[1]
    p4 = p3[0], p1[1]
    points = [p1, p2, p3, p4]
    msp.add_lwpolyline(points, close=True, dxfattribs={'layer': '지지물', 'color': 4})
    return msp


def draw_mast_for_profile(msp, mast_name, mast_coord, current_structure):
    mast_length, mast_width = get_mast_length_and_width(mast_name)
    mast_length = mast_length * V_scale

    if current_structure in ['토공', '교량']:
        p1 = (mast_coord[0] + mast_width / 2, mast_coord[1])
    else:  # 터널
        p1 = (mast_coord[0] + mast_width / 2, mast_coord[1] + (4.54 * V_scale))

    p2 = p1[0], p1[1] + mast_length
    p3 = p2[0] - mast_width, p2[1]
    p4 = p3[0], p1[1]
    mast_points = [p1, p2, p3, p4]
    msp.add_lwpolyline(mast_points, close=True, dxfattribs={'layer': '전주', 'color': 4})

    return msp


def get_mast_length_and_width(mast_name: str):
    """딕셔너리를 활용해 전주 길이와 폭을 빠르게 추출하는 함수"""

    # 전주 길이 매핑
    mast_length_map = {
        'P-10"x7t-9m': 9,
        'P-12"x7t-8.5m': 8.5,
        '터널하수강': 1.735,
        'H형주-208X202': 9,
        'H형주-250X255': 10
    }

    # 전주 폭 매핑
    mast_width_map = {
        'P-10"x7t-9m': 0.2674,
        'P-12"x7t-8.5m': 0.312,
        '터널하수강': 0.25,
        'H형주-208X202': 0.25,
        'H형주-250X255': 0.25
        # H형주는 별도 규격이 없다고 가정
    }

    mast_length = mast_length_map.get(mast_name)
    mast_width = mast_width_map.get(mast_name)

    if mast_length is None or mast_width is None:
        raise ValueError(f"전주 정보 '{mast_name}'에서 길이 또는 폭을 찾을 수 없습니다.")

    return mast_length, mast_width


def return_pos_coord(polyline_with_sta, pos):
    point_a, P_A, vector_a = interpolate_coordinates(polyline_with_sta, pos)
    return point_a, vector_a


def save_to_dxf(doc, file_name='output.dxf'):
    '''
    dxf파일 저장함수
    :param doc: ezdxf doc객체
    :param file_name: 파일명 str
    :return: None 저장기능 수행
    '''
    doc.saveas(file_name)


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

    return positions


# 전주번호 추가함수
def generate_postnumbers(lst):
    postnumbers = []
    prev_km = -1
    count = 0

    for number in lst:
        km = number // 1000  # 1000으로 나눈 몫이 같은 구간
        if km == prev_km:
            count += 1  # 같은 구간에서 숫자 증가
        else:
            prev_km = km
            count = 1  # 새로운 구간이므로 count를 0으로 초기화

        postnumbers.append((number, f'{km}-{count}'))

    return postnumbers


def get_pole_data():
    """전주 데이터를 반환하는 기본 딕셔너리"""
    return {
        150: {
            'prefix': 'Cako150',
            'tunnel': (947, 946),
            'earthwork': (544, 545),
            'straight_bridge': (556, 557),
            'curve_bridge': (562, 563),
        },
        250: {
            'prefix': 'Cako250',
            'tunnel': (979, 977),  # 터널은 I,O반대
            'earthwork': (508, 510),
            'straight_bridge': (512, 514),
            'curve_bridge': (527, 529),
        },
        350: {
            'prefix': 'Cako350',
            'tunnel': (569, 568),
            'earthwork': (564, 565),
            'straight_bridge': (566, 567),
            'curve_bridge': (566, 567),
        }
    }


def format_pole_data(design_speed):
    """설계 속도에 따른 전주 데이터를 특정 형식으로 변환"""
    base_data = get_pole_data()

    if design_speed not in base_data:
        raise ValueError("올바른 DESIGNSPEED 값을 입력하세요 (150, 250, 350)")

    data = base_data[design_speed]
    prefix = data['prefix']

    def create_pole_types(i_type, o_type, bracket_suffix):
        return {
            'I_type': i_type,
            'O_type': o_type,
            'I_bracket': f'{prefix}_{bracket_suffix}-I',
            'O_bracket': f'{prefix}_{bracket_suffix}-O',
        }

    return {
        '교량': {
            '직선': create_pole_types(*data['straight_bridge'], 'OpG3.5'),
            '곡선': create_pole_types(*data['curve_bridge'], 'OpG3.5'),
        },
        '터널': create_pole_types(*data['tunnel'], 'Tn'),
        '토공': create_pole_types(*data['earthwork'], 'OpG3.0'),
    }


def define_airjoint_section(positions):
    airjoint_list = []  # 결과 리스트
    airjoint_span = 1600  # 에어조인트 설치 간격(m)

    def is_near_multiple_of_DIG(number, tolerance=100):
        """주어진 수가 1200의 배수에 근사하는지 판별하는 함수"""
        remainder = number % airjoint_span
        return number > airjoint_span and (remainder <= tolerance or remainder >= (airjoint_span - tolerance))

    i = 0  # 인덱스 변수
    while i < len(positions) - 1:  # 마지막 전주는 제외
        pos = positions[i]  # 현재 전주 위치

        if is_near_multiple_of_DIG(pos):  # 조건 충족 시
            next_values = positions[i + 1:min(i + 6, len(positions))]  # 다음 5개 값 가져오기
            tags = [
                AirJoint.START.value,
                AirJoint.POINT_2.value,
                AirJoint.MIDDLE.value,
                AirJoint.POINT_4.value,
                AirJoint.END.value
            ]

            # (전주 위치, 태그) 쌍을 리스트에 추가 (최대 5개까지만)
            airjoint_list.extend(list(zip(next_values, tags[:len(next_values)])))

            # 다음 5개의 값을 가져왔으므로 인덱스를 건너뛰기
            i += 5
        else:
            i += 1  # 조건이 맞지 않으면 한 칸씩 이동

    return airjoint_list


def check_isairjoint(input_sta, airjoint_list):
    for data in airjoint_list:
        sta, tag = data
        if input_sta == sta:
            return tag


def write_to_file(filename, lines):
    """리스트 데이터를 파일에 저장하는 함수"""
    filename = f'c:/temp/' + filename
    try:
        # 디렉토리 자동 생성
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(lines)  # 리스트 데이터를 한 번에 파일에 작성

        print(f"✅ 파일 저장 완료: {filename}")
    except Exception as e:
        print(f"⚠️ 파일 저장 중 오류 발생: {e}")


def get_airjoint_bracket_data():
    """에어조인트 브래킷 데이터를 반환하는 기본 딕셔너리"""
    return {
        150: {
            'prefix': 'Cako150',  # 150급은 별도의 aj없음
            '터널': (941, 942),  # G2.1 I,0
            '토공': (1252, 1253),  # G3.0 I,O
            '교량': (1254, 1255),  # G3.5 I,O
        },
        250: {
            'prefix': 'Cako250',
            '터널': (1325, 1326),  # CAKO250-Tn-AJ
            '토공': (1296, 1297),  # CAKO250-G3.0-AJ
            '교량': (1298, 1299),  # CAKO250-G3.5-AJ
        },
        350: {
            'prefix': 'Cako350',
            '터널': (639, 640),  # CAKO350-Tn-AJ
            '토공': (635, 636),  # CAKO350-G3.0-AJ
            '교량': (637, 638),  # CAKO350-G3.5-AJ
        }
    }


def get_F_bracket_data():
    """F브래킷 데이터를 반환하는 기본 딕셔너리"""
    return {
        150: {
            'prefix': 'Cako150',
            '터널': (1330, 1330),  # TN-F
            '토공': (1253, 1253),  # G3.0F
            '교량': (1255, 1255),  # G3.5-F
        },
        250: {
            'prefix': 'Cako250',
            '터널': (1290, 1291),
            '토공': (1284, 1285),  # CAKO250-G3.0-F(S) CAKO250-G3.0-F(L)
            '교량': (1286, 1287),  # CAKO250-G3.5-F
        },
        350: {
            'prefix': 'Cako350',
            '터널': (582, 583),  # CAKO350-Tn-F
            '토공': (578, 579),  # CAKO350-G3.0-F(S) CAKO250-G3.0-F(L)
            '교량': (580, 581),  # CAKO350-G3.5-F
        }
    }


def get_airjoint_fitting_data():
    """에어조인트 브래킷 금구류 데이터를 반환하는 기본 딕셔너리"""
    return {
        150: {
            'prefix': 'Cako150',
            '에어조인트': 499,  # 에어조인트용 조가선 지지금구
            'FLAT': (1292, 1292),  # 무효인상용 조가선,전차선 지지금구(150-급에서는 f형 돼지꼬리)
            '곡선당김금구': (1293, 1294),  # L,R
        },
        250: {
            'prefix': 'Cako250',  #
            '에어조인트': 1279,  # 에어조인트용 조가선 지지금구
            'FLAT': (1281, 1282),  # 무효인상용 조가선, 전차선  지지금구
            '곡선당김금구': (1280, 1283)  # L,R
        },
        350: {
            'prefix': 'Cako350',  # 350
            '에어조인트': 586,  # 에어조인트용 조가선 지지금구
            'FLAT': (584, 585),  # 무효인상용 조가선, 전차선  지지금구
            '곡선당김금구': (576, 577),  # L,R
        }
    }


def create_dic(*args):
    dic = {}
    for i, arg in enumerate(args):
        dic[f'{i}'] = arg  # 'arg1', 'arg2', ..., 'argN' as keys
    return dic


def get_poletype_brackettype_gauge_sign(line_idx, pole_type, pole_type2, bracket_type, bracket_type2, gauge,
                                        next_gauge):
    """ 하선과 상선에 맞는 전주(pole), 브래킷(bracket), 게이지(gauge) 값을 반환 """
    pole = pole_type if line_idx == 0 else pole_type2
    bracket = bracket_type if line_idx == 0 else bracket_type2
    gauge_value = gauge if line_idx == 0 else -gauge  # 이미 부호 적용됨
    next_gauge_value = next_gauge if line_idx == 0 else -next_gauge  # 이미 부호 적용됨
    return pole, bracket, gauge_value, next_gauge_value


def add_AJ_brackets_middle(DESIGNSPEED, lines, pos, bracket_code_start, bracket_code_end, airjoint_fitting,
                           steady_arm_fitting):
    """MIDDLE 구간에서 AJ형 브래킷 추가"""
    # AJ형 가동 브래킷 및 금구류 추가
    x1, y1 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간1')
    bracket_code_else = bracket_code_start if DESIGNSPEED == 150 else bracket_code_end
    steady_arm_fitting_else = steady_arm_fitting[0] if DESIGNSPEED == 150 else steady_arm_fitting[1]
    add_AJ_bracket(lines, pos - 0.8, bracket_code_else, '가동브래킷 AJ형', airjoint_fitting, steady_arm_fitting_else, x1, y1)

    # AJ형 가동 브래킷 및 금구류 추가
    x1, y1 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간2')
    add_AJ_bracket(lines, pos + 0.8, bracket_code_end, '가동브래킷 AJ형', airjoint_fitting, steady_arm_fitting[1], x1, y1)


def get_fitting_and_mast_data(DESIGNSPEED, current_structure, bracket_type):
    """금구류 및 전주 데이터를 가져옴"""
    fitting_data = get_airjoint_fitting_data().get(DESIGNSPEED, {})
    airjoint_fitting = fitting_data.get('에어조인트', 0)
    flat_fitting = fitting_data.get('FLAT', (0, 0))
    steady_arm_fitting = fitting_data.get('곡선당김금구', (0, 0))

    mast_type, mast_name = get_mast_type(DESIGNSPEED, current_structure)

    offset = get_pole_gauge(DESIGNSPEED, current_structure)

    return airjoint_fitting, flat_fitting, steady_arm_fitting, mast_type, mast_name, offset


def get_mast_type(DESIGNSPEED, current_structure):
    # 전주 인덱스 딕셔너리(idx,comment)
    mast_dic = {
        150: {
            'prefix': 'Cako150',
            '토공': (1370, 'P-10"x7t-9m'),
            '교량': (1376, 'P-12"x7t-8.5m'),
            '터널': (1400, '터널하수강'),
        },
        250: {
            'prefix': 'Cako250',
            '토공': (1370, 'P-10"x7t-9m'),
            '교량': (1376, 'P-12"x7t-8.5m'),
            '터널': (1400, '터널하수강'),
        },
        350: {
            'prefix': 'Cako350',  # 350
            '토공': (619, 'H형주-208X202'),
            '교량': (620, 'H형주-250X255'),
            '터널': (621, '터널하수강'),
        }
    }
    mast_data = mast_dic.get(DESIGNSPEED, mast_dic[250])
    mast_type, mast_name = mast_data.get(current_structure, ("", "알 수 없는 구조"))

    return mast_type, mast_name


def get_bracket_codes(DESIGNSPEED, current_structure):
    """브래킷 코드 가져오기"""
    airjoint_data = get_airjoint_bracket_data().get(DESIGNSPEED, {})
    f_data = get_F_bracket_data().get(DESIGNSPEED, {})

    bracket_values = airjoint_data.get(current_structure, (0, 0))
    f_values = f_data.get(current_structure, (0, 0))

    return bracket_values, f_values


def add_pole(lines, pos, current_airjoint):
    """전주를 추가하는 함수"""
    lines.extend([
        f"\n,;-----{current_airjoint}-----\n",
        f"{pos}\n"
    ])


# 에어조인트 편위와 인상높이 딕셔너리
def get_bracket_coordinates(DESIGNSPEED, bracket_type):
    """설계속도와 브래킷 유형에 따른 좌표 반환"""
    coordinates = {
        "F형_시점": {
            150: (-0.35, 0.3),
            250: (-0.3, 0.32),
            350: (-0.7, 0.5)
        },
        "AJ형_시점": {
            150: (-0.15, 0),
            250: (-0.1, 0),
            350: (-0.2, 0)
        },
        "AJ형_중간1": {
            150: (-0.15, 0),
            250: (-0.1, 0),
            350: (-0.25, 0)
        },
        "AJ형_중간2": {
            150: (0.15, 0),
            250: (0.1, 0),
            350: (0.25, 0)
        },
        "AJ형_끝": {
            150: (0.15, 0),
            250: (0.1, 0),
            350: (0.2, 0)
        },
        "F형_끝": {
            150: (0.35, 0.3),
            250: (0.3, 0.32),
            350: (0.7, 0.5)
        },
    }

    # 지정된 브래킷 유형과 속도에 맞는 좌표 반환
    return coordinates.get(bracket_type, {}).get(DESIGNSPEED, (0, 0))


def common_lines(lines, mast_type, offset, mast_name, feeder_idx, spreader_name, spreader_idx, line_idx):
    current_line = '하선' if line_idx == 0 else '상선'
    angle = 0 if line_idx == 0 else 180
    lines.extend([
        ',;전주 구문\n',
        f',;{current_line}\n',
        f".freeobj {line_idx};{mast_type};{offset};,;{mast_name}\n",
        f".freeobj {line_idx};{feeder_idx};{offset};;{angle};,;급전선 현수 조립체\n",
        f".freeobj {line_idx};{spreader_idx};{offset};,;{spreader_name}\n\n"
    ])


def get_feeder_insulator_idx(DESIGNSPEED, current_structure):
    idx_dic = {
        150: {
            'prefix': 'Cako150',
            '토공': 1234,
            '교량': 1234,
            '터널': 1249
        },
        250: {
            'prefix': 'Cako250',
            '토공': 1234,
            '교량': 1234,
            '터널': 1249
        },
        350: {
            'prefix': 'Cako350',
            '토공': 597,
            '교량': 597,
            '터널': 598
        }
    }

    idx_data = idx_dic.get(DESIGNSPEED, idx_dic[250])
    idx = idx_data.get(current_structure, idx_data['토공'])
    return idx


def get_spreader_idx(DESIGNSPEED, current_structure, current_airjoint):
    """평행틀 인덱스를 반환하는 기본 딕셔너리"""
    spreader_dictionary = {
        150: {
            'prefix': 'Cako150',
            '토공': (531, 532),
            '교량': (534, 535),
            '터널': (537, 538)
        },
        250: {
            'prefix': 'Cako250',
            '토공': (531, 532),
            '교량': (534, 535),
            '터널': (537, 538)
        },
        350: {
            'prefix': 'Cako350',
            '토공': (587, 588),
            '교량': (589, 590),
            '터널': (587, 588)
        }
    }

    spreader_data = spreader_dictionary.get(DESIGNSPEED, spreader_dictionary[250])
    spreader_str = spreader_data.get(current_structure, (0, 0))  # 기본값 (0, 0) 설정

    if current_airjoint in ['에어조인트 2호주', '에어조인트 4호주']:
        spreader_idx = spreader_str[0]
        spreader_name = '평행틀-1m'
    elif current_airjoint in ['에어조인트 중간주 (3호주)']:
        spreader_idx = spreader_str[1]
        spreader_name = '평행틀-1.6m'
    else:
        spreader_idx = spreader_str[0]
        spreader_name = '평행틀-1m'

    return spreader_name, spreader_idx


class DATA:
    def __init__(self, params, mode=1, LINECOUNT=1, LINEOFFSET=0.0, POLE_direction=0):
        """초기화"""
        # 데이터 언팩
        self._positions, self._structure_list, self._curve_list, self._pitch_list, self._DESIGNSPEED, \
            self._airjoint_list, self._polyline, self._post_type_list, self._post_number_lst, = unpack_dic(params)

        self._mode = mode
        self._LINENUM = LINECOUNT
        self._LINEOFFSET = LINEOFFSET

        # 선로 좌우측 확인 (항상 tuple로 변환)
        self._line1_pole_direction, self._line2_pole_direction = self._convert_to_tuple(POLE_direction)

        self._line1_angle = 0 if self._line1_pole_direction == -1 else 180  # 하선 좌측: 0, 우측: 180
        self._line2_angle = 180  # 상선은 항상 180

        # 전주 데이터
        self._pole_data = format_pole_data(self._DESIGNSPEED)
        self._polyline_with_sta = [(i * 25, *values) for i, values in enumerate(self._polyline)]

        # 모드 1인 경우 새로운 전주 번호 생성, 모드 2면 기존 유지
        self._post_numbers = generate_postnumbers(self._positions) if mode == 1 else self._post_number_lst

    def _convert_to_tuple(self, direction):
        """POLE 방향을 항상 튜플로 변환"""
        if isinstance(direction, tuple):
            return direction
        return direction, None

    # 속성 캡슐화 (읽기 전용)
    @property
    def positions(self):
        return self._positions[:]  # 복사본 반환 (원본 보호)

    @property
    def mode(self):
        return self._mode  # 복사본 반환 (원본 보호)

    @property
    def structure_list(self):
        return self._structure_list.copy()

    @property
    def curve_list(self):
        return self._curve_list.copy()

    @property
    def pitch_list(self):
        return self._pitch_list.copy()

    @property
    def DESIGNSPEED(self):
        return self._DESIGNSPEED

    @property
    def pole_data(self):
        return self._pole_data

    @property
    def LINENUM(self):
        return self._LINENUM

    @property
    def LINEOFFSET(self):
        return self._LINEOFFSET

    @property
    def post_numbers(self):
        return self._post_numbers.copy()

    @property
    def line1_angle(self):
        return self._line1_angle

    @property
    def line2_angle(self):
        return self._line2_angle

    @property
    def airjoint_list(self):
        return self._airjoint_list.copy()  # '_airjoint_list'를 반환

    @property
    def line1_pole_direction(self):
        return self._line1_pole_direction  # 'line1_pole_direction'를 반환

    @property
    def line2_pole_direction(self):
        return self._line2_pole_direction  # 'line1_pole_direction'를 반환

    @property
    def polyline_with_sta(self):
        return self._polyline_with_sta.copy()  # 'line1_pole_direction'를 반환


class Pitch:
    def __init__(self):
        self.data = {}

    def load_data(self, file_path):
        """Load pitch data from the given file."""
        pitch_data = pd.read_csv(file_path, names=["STA", "PITCH"])
        self.data = {row["STA"]: row["PITCH"] for _, row in pitch_data.iterrows()}

    def get_pitch(self, sta):
        """Get the pitch at a specific STA."""
        return self.data.get(sta, None)


class Coordinate:
    def __init__(self):
        self.data = []

    def load_data(self, file_path):
        """Load coordinate data from the given file."""
        coord_data = pd.read_csv(file_path, names=["X", "Y", "Z"])
        self.data = coord_data

    def get_total_length(self):
        """Calculate the total length of the alignment based on coordinates."""
        if self.data:
            return self.data["X"].iloc[-1]
        return 0

    def get_max_grade(self):
        """Calculate the maximum grade based on elevation changes."""
        if len(self.data) > 1:
            elevations = self.data["Z"]
            grades = elevations.diff().dropna()
            return grades.max()
        return 0


class Alignment:
    def __init__(self, name=None):
        self.name = None
        self.total_length = None
        self.start_sta = None
        self.end_sta = None

    @classmethod
    def create(cls, name):
        return cls(name)

    def delete(self):
        del self

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def get_total_length(self):
        return self.total_length


class Curves(Alignment):
    def __init__(self):
        super().__init__()
        self.data = {}
        self.txtfile_importer = TxTFileHandler()

    def load_data(self):
        """Load curve data from the given file and create Curve objects."""
        self.txtfile_importer.select_file('곡선ㅍ차일', [('a', 'txt')])
        file_path = self.txtfile_importer.get_filepath()

        # Read the curve data from the file
        curve_data = pd.read_csv(file_path, names=["STA", "RADIUS", "CANT"])

        # Create a Curve object for each row and store it in the dictionary
        for _, row in curve_data.iterrows():
            curve = Curve()  # Create a new Curve object
            curve.create_curve(row["STA"], row["RADIUS"], row["CANT"])  # Set the STA, RADIUS, and CANT
            self.data[row["STA"]] = curve  # Store the Curve object in the dictionary with STA as key


class Curve(Curves):
    def __init__(self):
        super().__init__()
        self.sta = None
        self.radius = None
        self.cant = None
        self.direction = None

    def create_curve(self, sta, radius, cant):
        self.sta = sta
        self.radius = radius
        self.cant = cant

    def get_sta(self):
        return self.sta

    def get_radius(self):
        return self.radius

    def get_cant(self):
        return self.cant


class PoleTypeHelper:
    """전주 타입 결정 관련 기능을 제공하는 헬퍼 클래스"""

    @staticmethod
    def isbridge_tunnel(sta, structure_list):
        """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
        for start, end in structure_list['bridge']:
            if start <= sta <= end:
                return '교량'

        for start, end in structure_list['tunnel']:
            if start <= sta <= end:
                return '터널'

        return '토공'

    @staticmethod
    def iscurve(cur_sta, curve_list):
        """sta가 곡선 구간에 해당하는지 구분하는 함수"""
        rounded_sta = get_block_index(cur_sta)  # 25 단위로 반올림

        for sta, R, c in curve_list:
            if rounded_sta == sta:
                if R == 0:
                    return '직선', 0, 0  # 반경이 0이면 직선
                return '곡선', R, c  # 반경이 존재하면 곡선

        return '직선', 0, 0  # 목록에 없으면 기본적으로 직선 처리

    @staticmethod
    def isslope(cur_sta, curve_list):
        """sta가 곡선 구간에 해당하는지 구분하는 함수"""
        rounded_sta = get_block_index(cur_sta)  # 25 단위로 반올림

        for sta, g in curve_list:
            if rounded_sta == sta:
                if g == 0:
                    return '수평', 0  # 반경이 0이면 직선
                else:
                    return '기울기', f'{g * 1000:.2f}'

        return '수평', 0  # 목록에 없으면 기본적으로 직선 처리

    @staticmethod
    def get_structure_type(pos, structure_list):
        """전주가 다리/터널/토공인지 판별"""
        return isbridge_tunnel(pos, structure_list)

    @staticmethod
    def get_curve_type(pos, curve_list):
        """전주가 곡선인지 직선인지 판별"""
        curve, _, _ = iscurve(pos, curve_list)
        return curve

    @staticmethod
    def get_station_data(pole_info, structure, curve):
        """구조물 및 곡선 여부에 따라 전주 데이터를 가져옴"""
        station_data = pole_info.pole_data.get(structure, pole_info.pole_data.get('토공', {}))

        # 곡선/직선 구분하여 데이터 선택
        if isinstance(station_data, dict) and '직선' in station_data:
            station_data = station_data.get('곡선' if curve == '곡선' else '직선', {})

        return station_data

    @staticmethod
    def determine_pole_type(pole_info, pos, i, station_data):
        """전주 타입(I/O)과 브래킷을 결정"""
        I_type, O_type = station_data.get('I_type', '기본_I_type'), station_data.get('O_type', '기본_O_type')
        I_bracket, O_bracket = station_data.get('I_bracket', '기본_I_bracket'), station_data.get('O_bracket',
                                                                                               '기본_O_bracket')

        is_I_type = (i % 2 == 1) if pole_info.mode == 1 else (
                get_current_post_type(pos, pole_info.post_type_list) == 'I'
        )

        return (I_type, I_bracket) if is_I_type else (O_type, O_bracket)

    @staticmethod
    def adjust_pole_type_for_double_track(pole_info, is_I_type, I_type, I_bracket, O_type, O_bracket):
        """복선일 경우 상선 전주 타입 반대로 설정"""
        if pole_info.LINENUM == 2:
            return (O_type, O_bracket) if is_I_type else (I_type, I_bracket)
        return None, None  # 단선이면 사용 안 함


class PoleDataProcessor:
    """전주 위치 데이터를 처리하는 클래스"""

    def __init__(self, pole_data):
        """초기화"""
        self.pole_info = pole_data  # pole_data는 DATA 인스턴스 pole info로 네이밍

    def get_pole_types(self, pole_info, pos, i):
        """전주 타입 및 브래킷 정보를 반환"""
        structure = isbridge_tunnel(pos, pole_info.structure_list)
        curve, _, _ = iscurve(pos, pole_info.curve_list)
        station_data = pole_info.pole_data.get(structure, pole_info.pole_data.get('토공', {}))

        # 곡선/직선에 따라 데이터 선택
        if isinstance(station_data, dict) and '직선' in station_data:
            station_data = station_data.get('곡선' if curve == '곡선' else '직선', {})

        I_type, O_type = station_data.get('I_type', '기본_I_type'), station_data.get('O_type', '기본_O_type')
        I_bracket, O_bracket = station_data.get('I_bracket', '기본_I_bracket'), station_data.get('O_bracket',
                                                                                               '기본_O_bracket')

        is_I_type = (i % 2 == 1) if pole_info.mode == 1 else (
                get_current_post_type(pos, pole_info.post_type_list) == 'I')
        pole_type, bracket_type = (I_type, I_bracket) if is_I_type else (O_type, O_bracket)

        if pole_info.LINENUM == 2:  # 복선이면 상선 전주 타입 반대로 설정
            pole_type2, bracket_type2 = (O_type, O_bracket) if is_I_type else (I_type, I_bracket)
        else:
            pole_type2, bracket_type2 = None, None  # 단선이면 사용 안 함

        return pole_type, bracket_type, pole_type2, bracket_type2, structure, curve

    def process_normal_pole(self, pole_info, pos, structure, curve, pole_type,
                            bracket_type, pole_type2, bracket_type2, lines):
        """일반 전주 처리"""
        lines.append(f"\n,;-----일반개소({structure})({curve})-----\n")
        for line_idx in range(pole_info.LINENUM):
            suffix = "상선" if line_idx == 1 else "하선"
            angle = pole_info.line1_angle if line_idx == 0 else pole_info.line2_angle
            lines.append(f",;{suffix}\n")
            line_str = "".join([
                f"{pos},.freeobj {line_idx};",
                f"{pole_type if line_idx == 0 else pole_type2};0;0;{angle};,;",
                f"{bracket_type if line_idx == 0 else bracket_type2}\n"
            ])
            lines.append(line_str)

    def process_pole_data(self):
        """전주 데이터 처리"""
        lines = []  # 최종 데이터 리스트
        pole_info = self.pole_info
        positions = pole_info.positions
        post_numbers = pole_info.post_numbers
        airjoint_list = pole_info.airjoint_list

        for i in range(len(positions) - 1):
            pos, next_pos = positions[i], positions[i + 1]
            post_number = self.find_post_number(post_numbers, pos)

            pole_type, bracket_type, pole_type2, bracket_type2, current_structure, current_curve = self.get_pole_types(
                pole_info, pos, i)
            _, _, _, _, next_structure, _ = self.get_pole_types(pole_info, next_pos, i)
            current_airjoint = check_isairjoint(pos, airjoint_list)

            lines.append(f"\n,;{post_number}")  # 전주 번호 추가
            if current_airjoint:
                pass
                '''
                self.process_airjoint_pole(pole_info, pos, next_pos, current_structure, next_structure, current_curve,
                                           pole_type, bracket_type, pole_type2, bracket_type2, current_airjoint,
                                           lines)
                '''
            else:
                self.process_normal_pole(pole_info, pos, current_structure, current_curve,
                                         pole_type, bracket_type, pole_type2, bracket_type2, lines)

        return lines

    def process_wire_data(self):
        pass

    @staticmethod
    def find_post_number(lst, pos):
        for arg in lst:
            if arg[0] == pos:
                return arg[1]

    def process_airjoint_pole(self, pole_info, pos, next_pos, current_structure, next_structure, current_curve,
                              pole_type, bracket_type, pole_type2, bracket_type2, current_airjoint, lines):
        """에어조인트 구간별 전주 데이터 생성"""
        lines = []
        sign1 = pole_info.line1_pole_direction  # 하선 부호
        sign2 = pole_info.line2_pole_direction  # 상선 부호
        angle1 = 0 if sign1 == -1 else 180  # 하선 각도
        angle2 = 0 if sign2 == -1 else 180  # 상선 각도

        # 데이터 가져오기
        airjoint_fitting, flat_fitting, steady_arm_fitting, \
            mast_type, mast_name, offset = self.get_fitting_and_mast_data(current_structure, bracket_type)
        bracket_values, f_values = get_bracket_codes(DESIGNSPEED, current_structure)

        # 구조물별 건식게이지 값(절대값)
        gauge = get_pole_gauge(DESIGNSPEED, current_structure)
        next_gauge = get_pole_gauge(DESIGNSPEED, next_structure)

        # 건식게이지에 선별 방향 적용
        gauge = gauge * sign1
        next_gauge = next_gauge * sign1

        bracket_code_start, bracket_code_end = bracket_values
        f_code_start, f_code_end = f_values

        # 공통구문 sta ;-----에어조인트 시작점 (1호주)-----
        add_pole(lines, pos, current_airjoint)

        # 급전선 설비 인덱스 가져오기
        feeder_idx = get_feeder_insulator_idx(DESIGNSPEED, current_structure)

        # 평행틀 설비 인덱스 가져오기
        spreader_name, spreader_idx = get_spreader_idx(DESIGNSPEED, current_structure, current_airjoint)

        # 공통 텍스트(전주,급전선,평행틀
        if current_airjoint in [AirJoint.POINT_2.value, AirJoint.MIDDLE.value, AirJoint.POINT_4.value]:
            for line_idx in range(LINECOUNT):
                gauge = gauge if line_idx == 0 else gauge * -1  # 이미 부호가 적용되어있음

                common_lines(lines, mast_type, gauge, mast_name, feeder_idx, spreader_name, spreader_idx, line_idx)

            # 모든 필요한 값들을 딕셔너리로 묶어서 전달
        params = create_dic(pole_info.polyline_with_sta, current_airjoint, lines, pos, next_pos, DESIGNSPEED,
                            airjoint_fitting,
                            steady_arm_fitting,
                            flat_fitting, pole_type, pole_type2, bracket_type, bracket_type2, offset,
                            f_code_start, f_code_end, bracket_code_start, bracket_code_end,
                            current_structure, next_structure, gauge, next_gauge, pole_info.line1_pole_direction,
                            pole_info.line2_pole_direction, LINECOUNT)

        # 에어조인트 구간별 처리(2호주 ,3호주, 4호주)
        brackets_processor = BracketsProcessor(self)

    def get_fitting_and_mast_data(self, current_structure, bracket_type):
        """금구류 및 전주 데이터를 가져옴"""
        fitting_data = get_airjoint_fitting_data().get(DESIGNSPEED, {})
        airjoint_fitting = fitting_data.get('에어조인트', 0)
        flat_fitting = fitting_data.get('FLAT', (0, 0))
        steady_arm_fitting = fitting_data.get('곡선당김금구', (0, 0))

        mast_type, mast_name = get_mast_type(DESIGNSPEED, current_structure)

        offset = get_pole_gauge(DESIGNSPEED, current_structure)

        return airjoint_fitting, flat_fitting, steady_arm_fitting, mast_type, mast_name, offset

    def get_bracket_codes(DESIGNSPEED, current_structure):
        """브래킷 코드 가져오기"""
        airjoint_data = get_airjoint_bracket_data().get(DESIGNSPEED, {})
        f_data = get_F_bracket_data().get(DESIGNSPEED, {})

        bracket_values = airjoint_data.get(current_structure, (0, 0))
        f_values = f_data.get(current_structure, (0, 0))

        return bracket_values, f_values


class PoleDataIterator:
    """전주 데이터를 순회하며 필요한 정보를 가져오는 클래스"""

    def __init__(self, pole_info):
        self.pole_info = pole_info
        self.positions = pole_info.positions
        self.post_numbers = {pos: num for pos, num in pole_info.post_numbers}  # 딕셔너리 변환
        self.airjoint_list = pole_info.airjoint_list

    def iterate_poles(self):
        """전주 데이터를 순회하며 정보 반환"""
        for i in range(len(self.positions) - 1):
            pos, next_pos = self.positions[i], self.positions[i + 1]
            post_number = self.post_numbers.get(pos, "N/A")
            current_airjoint = check_isairjoint(pos, self.airjoint_list)

            yield i, pos, next_pos, post_number, current_airjoint  # Generator로 반환


class BracketsProcessor:
    def __init__(self, pole_data_processor):
        self.pole_data_processor = pole_data_processor  # PoleDataProcessor 객체를 인자로 받음

    def add_airjoint_brackets(self):
        # 인자 분해
        # POLEDATA에서 값 가져오기
        DESIGNSPEED = self.pole_data_processor.DESIGNSPEED
        positions = self.pole_data_processor.positions
        structure_list = self.pole_data_processor.structure_list

        x, y = get_bracket_coordinates(DESIGNSPEED, 'AJ형_시점')
        x1, y1 = get_bracket_coordinates(DESIGNSPEED, 'F형_시점')
        x2, y2 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간1')
        x3, y3 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간2')
        x4, y4 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_끝')
        x5, y5 = get_bracket_coordinates(DESIGNSPEED, 'F형_끝')

        """에어조인트 각 구간별 브래킷 추가"""
        for line_idx in range(LINECOUNT):
            pole = pole_type if line_idx == 0 else pole_type2
            bracket = bracket_type if line_idx == 0 else bracket_type2

            if current_airjoint == AirJoint.START.value:
                # START 구간 처리
                start_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, gauge, x1)
                lines.extend([
                    f".freeobj {line_idx};{pole};,;{bracket}\n",
                    f".freeobj {line_idx};1247;{offset};0;{start_angle},;스프링식 장력조절장치\n"
                ])

            elif current_airjoint == AirJoint.POINT_2.value:
                # POINT_2 구간 처리
                add_F_and_AJ_brackets(DESIGNSPEED, lines, pos, f_code_start, bracket_code_start, airjoint_fitting,
                                      steady_arm_fitting, flat_fitting)

            elif current_airjoint == AirJoint.MIDDLE.value:
                # MIDDLE 구간 처리
                add_AJ_brackets_middle(DESIGNSPEED, lines, pos, bracket_code_start, bracket_code_end, airjoint_fitting,
                                       steady_arm_fitting)

            elif current_airjoint == AirJoint.POINT_4.value:
                # POINT_4 구간 처리
                add_F_and_AJ_brackets(DESIGNSPEED, lines, pos, f_code_end, bracket_code_end, airjoint_fitting,
                                      steady_arm_fitting, flat_fitting, end=True)

            elif current_airjoint == AirJoint.END.value:
                # END 구간 처리
                end_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x5, next_gauge)
                lines.append(f".freeobj {line_idx};{pole};,;{bracket}\n")
                lines.append(f".freeobj {line_idx};1247;{offset};0;{180 + end_angle};,;스프링식 장력조절장치\n")

    def add_F_and_AJ_brackets(self, lines, pos, f_code, bracket_code, airjoint_fitting, steady_arm_fitting,
                              flat_fitting, end=False):
        """F형 및 AJ형 브래킷을 추가하는 공통 함수"""
        self.add_bracket(lines, pos, f_code, "F형", flat_fitting, 'F형_시점' if not end else 'F형_끝', end)
        self.add_bracket(lines, pos, bracket_code, "AJ형", airjoint_fitting, 'AJ형_시점' if not end else 'AJ형_끝', end,
                         steady_arm_fitting)

    def add_bracket(self, lines, pos, bracket_code, bracket_type, fitting_data, bracket_pos_key, end=False,
                    steady_arm_fitting=None):
        """브래킷 추가하는 공통 함수"""
        x1, y1 = self.get_bracket_coordinates(bracket_pos_key if not end else f'{bracket_type}_끝')
        if bracket_type == "F형":
            self.add_F_bracket(lines, pos, bracket_code, bracket_type, fitting_data, x1, y1)
        else:  # AJ형
            self.add_AJ_bracket(lines, pos, bracket_code, bracket_type, fitting_data, steady_arm_fitting, x1, y1)

    def add_F_bracket(self, lines, pos, bracket_code, bracket_type, fitting_data, x1, y1):
        """F형 가동 브래킷 및 금구류 추가"""
        idx1, idx2 = fitting_data
        if self.DESIGNSPEED == 150:
            lines.extend([
                ',;가동브래킷구문\n',
                f"{pos},.freeobj 0;{bracket_code};0;{y1};,;{bracket_type}\n",
                f"{pos},.freeobj 0;{idx1};{x1};{y1},;조가선지지금구-F용\n",
                f"{pos},.freeobj 0;{idx2};{x1};{y1},;전차선선지지금구-F용\n",
            ])
        else:
            lines.extend([
                ',;가동브래킷구문\n',
                f"{pos},.freeobj 0;{bracket_code};0;0;,;{bracket_type}\n",
                f"{pos},.freeobj 0;{idx1};{x1};0,;조가선지지금구-F용\n",
                f"{pos},.freeobj 0;{idx2};{x1};0,;전차선선지지금구-F용\n",
            ])

    def add_AJ_bracket(self, lines, pos, bracket_code, bracket_type, fitting_data, steady_arm_fitting, x1, y1):
        """AJ형 가동 브래킷 및 금구류 추가"""
        lines.extend([
            ',;가동브래킷구문\n',
            f"{pos},.freeobj 0;{bracket_code};0;0;,;{bracket_type}\n",
            f"{pos},.freeobj 0;{fitting_data};{x1};{y1},;조가선지지금구-AJ용\n",
            f"{pos},.freeobj 0;{steady_arm_fitting};{x1};{y1},;곡선당김금구\n",
        ])

    def get_bracket_coordinates(self, pos_key):
        """브래킷 좌표 계산 (예시로 값을 반환)"""
        # 실제 좌표 계산 로직을 여기에 작성
        return (0, 0)  # (x1, y1) 값을 반환하도록 수정


def unpack_dic(dic):
    result = []  # Use a more descriptive variable name than 'list'
    for key, value in dic.items():
        result.append(value)  # Append the key-value pair as a tuple
    return result


def get_block_index(current_track_position, block_interval=25):
    """현재 트랙 위치를 블록 인덱스로 변환"""
    return math.floor(current_track_position / block_interval + 0.001) * block_interval


def process_to_WIRE(params, mode=1, LINECOUNT=1, LINEOFFSET=0.0, POLE_direction=None):
    positions, structure_list, curve_list, pitchlist, DESIGNSPEED, airjoint_list, polyline, post_type_list, post_number_lst = unpack_dic(
        params)

    """ 전주 위치에 wire를 배치하는 함수 """
    # 모드 1인경우 새 리스트 생성 아닌경우 기존 리스트 활용
    generated_post_numbers = generate_postnumbers(positions) if mode == 1 else post_number_lst
    polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]
    lines = []
    for i in range(len(positions) - 1):
        pos, next_pos = positions[i], positions[i + 1]
        currentspan = next_pos - pos  # 전주 간 거리 계산
        current_structure = isbridge_tunnel(pos, structure_list)
        next_structure = isbridge_tunnel(next_pos, structure_list)
        current_curve, R, c = iscurve(pos, curve_list)
        current_slope, pitch = isslope(pos, pitchlist)  # 현재 측점의 구배
        next_slope, next_pitch = isslope(next_pos, pitchlist)  # 다음 측점의 구배
        current_z = get_elevation_pos(pos, polyline_with_sta)  # 현재 측점의 z값
        next_z = get_elevation_pos(next_pos, polyline_with_sta)  # 다음 측점의 z값
        # z값 param
        param_z = {
            'current_slope': current_slope,
            'pitch': pitch,
            'next_slope': next_slope,
            'next_pitch': next_pitch,
            'current_z': current_z,
            'next_z': next_z
        }

        current_sta = get_block_index(pos)
        current_airjoint = check_isairjoint(pos, airjoint_list)
        if mode == 1:
            is_I_type = (i % 2 == 1)
            next_type = None
        else:
            is_I_type = (get_current_post_type(pos, post_type_list) == 'I')
            next_type = get_current_post_type(next_pos, post_type_list)
        currnet_type = 'I' if is_I_type else 'O'
        post_number = find_post_number(generated_post_numbers, pos)
        obj_index, comment, AF_wire, FPW_wire = get_wire_span_data(DESIGNSPEED, currentspan, current_structure)

        # AF와 FPW오프셋(X,Y)
        AF_X_offset, AF_y_offset, fpw_wire_X_offset, fpw_wire_y_offset, AF_yz_angle, FPW_yz_angle, AF_xy_angle, FPW_xy_angle, AF_X_offset_Next, fpw_wire_X_offset_Next = CALULATE_AF_FPW_OFFET_ANGLE(
            current_structure, next_structure, currentspan)

        lines.extend([f'\n,;{post_number}'])
        if current_airjoint in ['에어조인트 시작점 (1호주)', '에어조인트 (2호주)', '에어조인트 중간주 (3호주)', '에어조인트 (4호주)', '에어조인트 끝점 (5호주)']:
            lines.extend([f'\n,;-----{current_airjoint}({current_structure})-----\n'])
        else:

            lines.extend([f'\n,;-----일반개소({current_structure})({current_curve})-----\n'])

        lines.extend(handle_curve_and_straight_section(pos, next_pos, currentspan, polyline_with_sta, current_airjoint,
                                                       obj_index, comment, currnet_type, next_type, current_structure,
                                                       next_structure, param_z))
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, AF_X_offset, AF_X_offset_Next)
        lines.append(f"{pos},.freeobj 0;{AF_wire};{AF_X_offset};{AF_y_offset};{adjusted_angle};{AF_yz_angle};,;급전선\n")
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, fpw_wire_X_offset,
                                               fpw_wire_X_offset_Next)
        lines.append(
            f"{pos},.freeobj 0;{FPW_wire};{fpw_wire_X_offset};{fpw_wire_y_offset};{adjusted_angle};{FPW_yz_angle};,;FPW\n")

    return lines


def get_elevation_pos(pos, polyline_with_sta):
    new_z = None

    for i in range(len(polyline_with_sta) - 1):
        sta1, x1, y1, z1 = polyline_with_sta[i]  # 현재값
        sta2, x2, y2, z2 = polyline_with_sta[i + 1]  # 다음값
        L = sta2 - sta1
        L_new = pos - sta1

        if sta1 <= pos < sta2:
            new_z = calculate_height_at_new_distance(z1, z2, L, L_new)
            return new_z

    return new_z


def calculate_height_at_new_distance(h1, h2, L, L_new):
    """주어진 거리 L에서의 높이 변화율을 기반으로 새로운 거리 L_new에서의 높이를 계산"""
    h3 = h1 + ((h2 - h1) / L) * L_new
    return h3


def CALULATE_AF_FPW_OFFET_ANGLE(current_structure, next_structure, currentspan):
    # 현재
    AF_X_offset, AF_y_offset, fpw_wire_X_offset, fpw_wire_y_offset = get_wire_offsetanlge(DESIGNSPEED,
                                                                                          current_structure)
    # 다음
    AF_X_offset_Next, AF_y_offset_Next, fpw_wire_X_offset_Next, fpw_wire_y_offset_Next = get_wire_offsetanlge(
        DESIGNSPEED, next_structure)

    # YZ 평면 각도 계산
    AF_yz_angle = math.degrees(math.atan((AF_y_offset_Next - AF_y_offset) / currentspan))
    FPW_yz_angle = math.degrees(math.atan((fpw_wire_y_offset_Next - fpw_wire_y_offset) / currentspan))

    # XY 평면 각도 계산
    AF_xy_angle = math.degrees(math.atan((AF_X_offset_Next - AF_X_offset) / currentspan))
    FPW_xy_angle = math.degrees(math.atan((fpw_wire_X_offset_Next - fpw_wire_X_offset) / currentspan))

    return AF_X_offset, AF_y_offset, fpw_wire_X_offset, fpw_wire_y_offset, AF_yz_angle, FPW_yz_angle, AF_xy_angle, FPW_xy_angle, AF_X_offset_Next, fpw_wire_X_offset_Next


def get_wire_offsetanlge(DESIGNSPEED, current_structure):
    """AF,FPW offset을 반환하는 기본 딕셔너리(x,y)"""
    AF_offset_values = {
        150: {
            'prefix': 'Cako150',
            '토공': (0, 0),
            '교량': (-0.5, 0),
            '터널': (-0.443, -2.335)
        },
        250: {
            'prefix': 'Cako250',
            '토공': (0, 0),
            '교량': (-0.5, 0),
            '터널': (-0.28, -1.75)
        },
        350: {
            'prefix': 'Cako350',
            '토공': (-2.732, -1.043),
            '교량': (-0.785, 0.905),
            '터널': (3.98, 0.828)
        }
    }

    FPW_offset_values = {
        150: {
            'prefix': 'Cako150',
            '토공': (0, 0),
            '교량': (-0.5, 0),
            '터널': (0.93, 0)
        },
        250: {
            'prefix': 'Cako250',
            '토공': (0, 0),
            '교량': (-0.5, 0),
            '터널': (0.93, 0)
        },
        350: {
            'prefix': 'Cako350',
            '토공': (-0.193, 0.592),
            '교량': (-0.4389, 0.573),
            '터널': (0.1, 0)
        }
    }
    AF_data = AF_offset_values.get(DESIGNSPEED, AF_offset_values[250])
    AF_X_offset, AF_y_offset = AF_data[current_structure]
    FPW_data = FPW_offset_values.get(DESIGNSPEED, FPW_offset_values[250])
    fpw_wire_X_offset, fpw_wire_y_offset = FPW_data[current_structure]

    return [AF_X_offset, AF_y_offset, fpw_wire_X_offset, fpw_wire_y_offset]


def buffered_write(filename, lines):
    """파일 쓰기 버퍼 함수"""
    filename = "C:/TEMP/" + filename
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(lines)


def get_wire_span_data(DESIGNSPEED, currentspan, current_structure):
    """ 경간에 따른 wire 데이터 반환 """
    # SPEED STRUCTURE span 45, 50, 55, 60
    span_data = {
        150: {
            'prefix': 'Cako150',
            '토공': (592, 593, 594, 595),  # 가고 960
            '교량': (592, 593, 594, 595),  # 가고 960
            '터널': (614, 615, 616, 617)  # 가고 710
        },
        250: {
            'prefix': 'Cako250',
            '토공': (484, 478, 485, 479),  # 가고 1200
            '교량': (484, 478, 485, 479),  # 가고 1200
            '터널': (494, 495, 496, 497)  # 가고 850
        },
        350: {
            'prefix': 'Cako350',
            '토공': (488, 489, 490, 491),  # 가고 1400
            '교량': (488, 489, 490, 491),  # 가고 1400
            '터널': (488, 489, 490, 491)  # 가고 1400
        }
    }

    # DESIGNSPEED에 맞는 구조 선택 (기본값 250 사용)
    span_values = span_data.get(DESIGNSPEED, span_data[250])

    # current_structure에 맞는 값 추출
    current_structure_list = span_values[current_structure]

    # currentspan 값을 통해 인덱스를 추출
    span_index_mapping = {
        45: (0, '경간 45m', 1236, 1241),
        50: (1, '경간 50m', 1237, 1242),
        55: (2, '경간 55m', 1238, 1243),
        60: (3, '경간 60m', 1239, 1244)
    }

    # currentspan이 유효한 값인지 확인
    if currentspan not in span_index_mapping:
        raise ValueError(f"Invalid span value '{currentspan}'. Valid values are 45, 50, 55, 60.")

    # currentspan에 해당하는 인덱스 및 주석 추출
    idx, comment, feeder_idx, fpw_idx = span_index_mapping[currentspan]
    # idx 값을 current_structure_list에서 가져오기
    idx_value = current_structure_list[idx]

    return idx_value, comment, feeder_idx, fpw_idx


def get_lateral_offset_and_angle(index, currentspan):
    """ 홀수/짝수 전주에 따른 편위 및 각도 계산 """
    sign = -1 if index % 2 == 1 else 1
    return sign * 0.2, -sign * math.degrees(0.4 / currentspan)


def handle_curve_and_straight_section(pos, next_pos, currentspan, polyline_with_sta, current_airjoint, obj_index,
                                      comment, currnet_type, next_type, current_structure, next_structure, param_z):
    """ 직선, 곡선 구간 wire 처리 """
    lines = []
    sign = -1 if currnet_type == 'I' else 1
    next_sign = -1 if next_type == 'I' else 1

    lateral_offset = sign * 0.2
    next_offset = next_sign * 0.2
    x, y = get_bracket_coordinates(DESIGNSPEED, 'AJ형_시점')
    x1, y1 = get_bracket_coordinates(DESIGNSPEED, 'F형_시점')
    x2, y2 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간1')
    x3, y3 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간2')
    x4, y4 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_끝')
    x5, y5 = get_bracket_coordinates(DESIGNSPEED, 'F형_끝')

    # z값 변수 언팩
    current_slope = param_z['current_slope']
    current_pitch = param_z['pitch']
    next_slope = param_z['next_slope']
    next_pitch = param_z['next_pitch']
    current_z = param_z['current_z']
    next_z = param_z['next_z']

    # 구조물 OFFSET 가져오기
    gauge = get_pole_gauge(DESIGNSPEED, current_structure)
    next_gauge = get_pole_gauge(DESIGNSPEED, next_structure)
    # 전차선 정보 가져오기
    contact_object_index, messenger_object_index, system_heigh, contact_height = get_contact_wire_and_massanger_wire_info(
        DESIGNSPEED, current_structure, currentspan)

    # H1 전차선높이
    # H2 조가선 높이

    # 에어조인트 구간 처리
    if current_airjoint == '에어조인트 시작점 (1호주)':

        # 본선
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, lateral_offset, x)
        lines.append(f'{pos},.freeobj 0;{obj_index};{lateral_offset};0;{adjusted_angle};,;본선\n')

        # 무효선

        slope_degree1, slope_degree2, h1, h2, pererall_d, sta2 = initialrize_tenstion_device(pos, gauge, currentspan,
                                                                                             contact_height,
                                                                                             system_heigh,
                                                                                             adjusted_angle, y1)
        slope_degree2 = calculate_slope(h2, contact_height + system_heigh, currentspan)  # 조가선 상하각도
        slope_degree1 = calculate_slope(h1, contact_height + y1, currentspan)  # 전차선 상하각도
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, gauge, x1)  # 평면각도
        lines.append(
            f'{sta2},.freeobj 0;{messenger_object_index};{pererall_d};{h2};{adjusted_angle};{slope_degree2},;무효조가선\n')
        lines.append(
            f'{sta2},.freeobj 0;{contact_object_index};{pererall_d};{h1};{adjusted_angle};{slope_degree1},;무효전차선\n')

    elif current_airjoint == '에어조인트 (2호주)':
        # 본선 각도
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x, x3)
        lines.append(f"{pos},.freeobj 0;{obj_index};{x};0;{adjusted_angle};,;본선\n")

        # 무효선 하강
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x1, x2)  # 평면각도

        adjusted_angle_conatctwire = calculate_slope(contact_height + y1, contact_height, currentspan)  # 전차선상하각도
        adjusted_angle_massangerwire = calculate_slope(contact_height + system_heigh, contact_height + system_heigh,
                                                       currentspan)  # 조가선 상하각도
        '''
        lines.append(f"{pos},.freeobj 0;{contact_object_index};{x1};{contact_height + y1};{adjusted_angle};{adjusted_angle_conatctwire};,;무효전차선\n")
        lines.append(f"{pos},.freeobj 0;{messenger_object_index};{x1};{contact_height + system_heigh};{adjusted_angle};{adjusted_angle_massangerwire};,;무효조가선\n")
        '''
        lines.append(f"{pos},.freeobj 0;{obj_index};{x1};{y1};{adjusted_angle};{adjusted_angle_conatctwire};,;무효선\n")
    elif current_airjoint == '에어조인트 중간주 (3호주)':
        # 본선 >무효선 상승
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x3, x5)  # 평면각도
        topdown_angle_conatctwire = calculate_slope(contact_height, contact_height + y1, currentspan)  # 전차선 상하각도
        topdown_angle_massangerwire = calculate_slope(contact_height + system_heigh, contact_height + system_heigh,
                                                      currentspan)  # 조가선 상하각도
        '''
        lines.append(f"{pos},.freeobj 0;{contact_object_index};{x3};0;{adjusted_angle};{topdown_angle_conatctwire};,;본선전차선\n")
        lines.append(f"{pos},.freeobj 0;{messenger_object_index};{x3};0;{adjusted_angle};{topdown_angle_massangerwire};,;본선조가선\n")
        '''
        lines.append(f"{pos},.freeobj 0;{obj_index};{x3};0;{adjusted_angle};{topdown_angle_conatctwire};,;무효선\n")
        # 무효선 >본선
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x2, x4)
        lines.append(f"{pos},.freeobj 0;{obj_index};{x2};0;{adjusted_angle};0;,;무효선\n")

    elif current_airjoint == '에어조인트 (4호주)':
        # 본선 각도
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x4, -lateral_offset)
        lines.append(f"{pos},.freeobj 0;{obj_index};{x4};0;{adjusted_angle};,;본선\n")

        # H1 전차선높이
        # H2 조가선 높이

        # 무효선

        slope_degree1, slope_degree2, h1, h2, pererall_d, _ = initialrize_tenstion_device(pos, gauge, currentspan,
                                                                                          contact_height, system_heigh,
                                                                                          adjusted_angle, y1)
        topdown_angle_conatctwire = calculate_slope(contact_height + y1, h1, currentspan)  # 전차선 상하각도
        topdown_angle_massangerwire = calculate_slope(contact_height + system_heigh, h2, currentspan)  # 조가선 상하각도
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x5, next_gauge)  # 평면각도
        lines.append(
            f'{pos},.freeobj 0;{messenger_object_index};{x5};{contact_height + system_heigh};{adjusted_angle};{topdown_angle_massangerwire};,;무효조가선\n')
        lines.append(
            f'{pos},.freeobj 0;{contact_object_index};{x5};{contact_height + y1};{adjusted_angle};{topdown_angle_conatctwire};,;무효전차선\n')

    # 일반구간
    else:
        if next_type is None:
            adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, lateral_offset, -lateral_offset)
        else:
            adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, lateral_offset, next_offset)
        pitch_angle = change_permile_to_degree(current_pitch)
        topdown_angle = calculate_slope(current_z, next_z, currentspan) - pitch_angle  # 전차선 상하각도
        lines.append(f"{pos},.freeobj 0;{obj_index};{lateral_offset};;{adjusted_angle};{topdown_angle};,;{comment}\n")
    return lines


def change_permile_to_degree(permile):
    """퍼밀 값을 도(degree)로 변환"""
    # 정수 또는 문자열이 들어오면 float으로 변환
    if not isinstance(permile, (int, float)):
        permile = float(permile)

    return math.degrees(math.atan(permile / 1000))  # 퍼밀을 비율로 변환 후 계산


def calculate_slope(h1, h2, gauge):
    """주어진 높이 차이와 수평 거리를 바탕으로 기울기(각도) 계산"""
    slope = (h2 - h1) / gauge  # 기울기 값 (비율)
    return math.degrees(math.atan(slope))  # 아크탄젠트 적용 후 degree 변환


def initialrize_tenstion_device(pos, gauge, currentspan, contact_height, system_heigh, adjusted_angle=0, y=0):
    # 장력장치 치수
    tension_device_length = 7.28

    # 전선 각도
    new_length = currentspan - tension_device_length  # 현재 span에서 장력장치까지의 거리
    pererall_d, vertical_offset = return_new_point(gauge, currentspan, tension_device_length)  # 선형 시작점에서 전선까지의 거리

    sta2 = pos + vertical_offset  # 전선 시작 측점
    h1 = 5.563936  # 장력장치 전차선 높이
    h2 = 6.04784  # 장력장치 조가선 높이

    slope_radian1 = math.atan((h1 - (contact_height + y)) / currentspan)  # 전차선 각도(라디안)
    slope_radian2 = math.atan((h2 - (contact_height + system_heigh)) / currentspan)  # 조가선 각도(라디안)

    slope_degree1 = math.degrees(slope_radian1)  # 전차선 각도(도)
    slope_degree2 = math.degrees(slope_radian2)  # 조가선 각도(도)

    return slope_degree1, slope_degree2, h1, h2, pererall_d, sta2


# 새로운 점 계산 함수
def return_new_point(x, y, L):
    A = (x, 0)  # A점 좌표
    B = (0, 0)  # 원점 B
    C = (0, y)  # C점 좌표
    theta = math.degrees(abs(math.atan(y / x)))
    D = calculate_destination_coordinates(A[0], A[1], theta, L)  # 이동한 D점 좌표
    E = B[0], B[1] + D[1]
    d1 = calculate_distance(D[0], D[1], E[0], E[1])
    d2 = calculate_distance(B[0], B[1], E[0], E[1])

    # 외적을 이용해 좌우 판별
    v_x, v_y = C[0] - B[0], C[1] - B[1]  # 선분 벡터
    w_x, w_y = A[0] - B[0], A[1] - B[1]  # 점에서 선분 시작점까지의 벡터
    cross = v_x * w_y - v_y * w_x  # 외적 계산
    sign = -1 if cross > 0 else 1

    return d1 * sign, d2


def calculate_curve_angle(polyline_with_sta, pos, next_pos, stagger1, stagger2):
    finale_anlge = None
    point_a, P_A, vector_a = interpolate_coordinates(polyline_with_sta, pos)
    point_b, P_B, vector_b = interpolate_coordinates(polyline_with_sta, next_pos)

    if point_a and point_b:
        offset_point_a = calculate_offset_point(vector_a, point_a, stagger1)
        offset_point_b = calculate_offset_point(vector_b, point_b, stagger2)

        offset_point_a_z = (offset_point_a[0], offset_point_a[1], 0)  # Z값 0추가
        offset_point_b_z = (offset_point_b[0], offset_point_b[1], 0)  # Z값 0추가

        a_b_angle = calculate_bearing(offset_point_a[0], offset_point_a[1], offset_point_b[0], offset_point_b[1])
        finale_anlge = vector_a - a_b_angle
    return finale_anlge


def get_pole_gauge(DESIGNSPEED, current_structure):
    GAUGE_dictionary = {
        150: {'토공': 3, '교량': 3.5, '터널': 2.1},
        250: {'토공': 3, '교량': 3.5, '터널': 2.1},
        350: {'토공': 3.267, '교량': 3.5156, '터널': 2.1}
    }
    gauge = GAUGE_dictionary.get(DESIGNSPEED, {}).get(current_structure, "알 수 없는 구조")
    return gauge


def get_airjoint_angle(gauge, stagger, span):
    S_angle = abs(math.degrees((gauge + stagger) / span)) if span != 0 else 0.0
    E_angle = abs(math.degrees((gauge - stagger) / span)) if span != 0 else 0.0

    return S_angle, E_angle


def get_contact_wire_and_massanger_wire_info(DESIGNSPEED, current_structure, span):
    inactive_contact_wire = {40: 1257, 45: 1258, 50: 1259, 55: 1260, 60: 1261}  # 무효 전차선 인덱스
    inactive_messenger_wire = {40: 1262, 45: 1263, 50: 1264, 55: 1265, 60: 1266}  # 무효 조가선 인덱스

    # 객체 인덱스 가져오기 (기본값 60)
    contact_object_index = inactive_contact_wire.get(span, 1261)
    messenger_object_index = inactive_messenger_wire.get(span, 1266)

    # 가고와 전차선 높이정보
    contact_height_dictionary = {
        150: {'토공': (0.96, 5.2), '교량': (0.96, 5.2), '터널': (0.71, 5)},
        250: {'토공': (1.2, 5.2), '교량': (1.2, 5.2), '터널': (0.85, 5)},
        350: {'토공': (1.4, 5.1), '교량': (1.4, 5.1), '터널': (1.4, 5.1)}
    }

    contact_data = contact_height_dictionary.get(DESIGNSPEED, contact_height_dictionary[250])
    system_heigh, contact_height = contact_data.get(current_structure, (0, 0))  # 기본값 (0, 0) 설정

    return contact_object_index, messenger_object_index, system_heigh, contact_height


def calculate_distance(x1, y1, x2, y2):
    """두 점 (x1, y1)과 (x2, y2) 사이의 유클리드 거리 계산"""
    return math.hypot(x2 - x1, y2 - y1)  # math.sqrt((x2 - x1)**2 + (y2 - y1)**2)와 동일


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
        v1 = calculate_bearing(x1, y1, x2, y2)
        # target_sta가 두 점 사이에 있는 경우 보간 수행
        if sta1 <= target_sta < sta2:
            t = abs(target_sta - sta1)
            x, y = calculate_destination_coordinates(x1, y1, v1, t)
            z = z1 + t * (z2 - z1)
            return (x, y, z), (x1, y1, z1), v1

    return None  # 범위를 벗어난 sta 값에 대한 처리


# 폴리선 좌표 읽기


# 파일 읽기


# 추가
# 방위각 거리로 점 좌표반환
def calculate_destination_coordinates(x1, y1, bearing, distance):
    # Calculate the destination coordinates given a starting point, bearing, and distance in Cartesian coordinates
    angle = math.radians(bearing)
    x2 = x1 + distance * math.cos(angle)
    y2 = y1 + distance * math.sin(angle)
    return x2, y2


# offset 좌표 반환
def calculate_offset_point(vector, point_a, offset_distance):
    if offset_distance > 0:  # 우측 오프셋
        vector -= 90
    else:
        vector += 90  # 좌측 오프셋
    offset_a_xy = calculate_destination_coordinates(point_a[0], point_a[1], vector, abs(offset_distance))
    return offset_a_xy


def calculate_bearing(x1, y1, x2, y2):
    # Calculate the bearing (direction) between two points in Cartesian coordinates
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.degrees(math.atan2(dy, dx))
    return bearing


# 실행


def createtxt(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        for line in data:
            f.write(f'{line}\n')


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


def get_dxf_scale(scale=None):
    """
    도면 축척을 반환하는 함수
    :param scale: 도면 축척 값 (예: 1000 -> 1, 500 -> 0.5)
    :return: 변환된 축척 값 (1:1000 -> 1, 1:500 -> 0.5)
    """
    h_scale = None
    v_scale = None

    if scale is None:
        try:
            h_scale = int(input('프로젝트의 평면축척 입력 (예: 1000 -> 1, 500 -> 0.5): '))
            v_scale = int(input('프로젝트의 종단축척 입력 (예: 1000 -> 1, 500 -> 0.5): '))
        except ValueError:
            print("❌ 잘못된 입력! 숫자를 입력하세요.")
            return None

    if h_scale <= 0 or v_scale <= 0:
        print("❌ 축척 값은 양수여야 합니다!")
        return None
    h_scale = h_scale / 1000
    v_scale = 1000 / v_scale

    return h_scale, v_scale


def get_current_post_type(pos: int, typeList: list) -> str:
    for sta, post_type in typeList:
        if sta == pos:
            return post_type
    return 'None'


def get_filename_tk_inter():
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김

    # 파일 선택 대화상자 열기
    file_path = filedialog.askopenfilename(defaultextension=".txt",
                                           filetypes=[("txt files", "*.txt"), ("All files", "*.*")])

    if not file_path:
        print("파일을 선택하지 않았습니다.")
        return ""  # 빈 문자열을 반환하여 선택이 없음을 나타냄

    try:
        print('현재 파일:', file_path)
    except Exception as e:
        print(f'예외가 발생했습니다. 내용: {e}')
        return ""  # 예외가 발생한 경우 빈 문자열을 반환

    return file_path  # 파일 경로 반환


# 실행
if __name__ == "__main__":
    gui = PoleDataGUI()
    gui.mainloop()
