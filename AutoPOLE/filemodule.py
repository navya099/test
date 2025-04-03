import datetime

from loggermodule import logger
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import pandas as pd
import chardet


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

    def set_filepath(self, filepath):
        self.filepath = filepath

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


def buffered_write(filename, lines):
    """파일 쓰기 버퍼 함수"""
    filename = "C:/TEMP/" + filename
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(lines)
