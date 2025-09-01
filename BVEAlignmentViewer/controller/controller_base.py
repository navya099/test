from tkinter import filedialog, messagebox

from RouteManager2.CurrentRoute import CurrentRoute
from core.calculator import Calculator
from core.datacontainer import BVERouteFactory
from core.parser import CSVRouteParser
from model.model import BVERouteData



# 기능 클래스(모든 기능을 넣을 예정)
class AppController:
    """
    기능 관리 클래스.

    Attributes:
        current_route (CurrentRoute): openbve CurrentRoute객체 노선의 트랙, 곡선, 구배, 좌표, 역 정보를 포함.
        main_app (tk.Tk) TK 메인 인스턴스
        file_ctrl(FileController): 파일 열기/저장 및 경로 관리를 담당하는 컨트롤러
        parser (CSVRouteParser): CSVRouteParser 호출용 클래스
        calculator (Calculator): 선형 계산용 클래스
    """
    def __init__(self, main_app, file_controller):
        self.current_route = None
        self.main_app = main_app  # MainApp 인스턴스 (UI 접근용)
        self.file_ctrl = file_controller
        # Alignment 데이터 컨테이너

        # 기능 전담 클래스 인스턴스 보관
        self.parser = CSVRouteParser()
        self.calculator = Calculator()

    def load_route(self, filepath: str):
        """
        파일에서 BVE 루트를 로드하고, 필요한 데이터 리스트를 반환.
        Attributes:
            filepath (str): 루트파일 경로
        Returns:
            list: 다음 6개 리스트로 구성된 리스트
            - trackpositions (list[float]): 궤도 상의 절대 거리 (m 단위)
            - radiuss (list[float]): 곡선 반경 (m 단위, 직선은 0)
            - pitch_values (list[float]): 종단 구배 값 (%)
            - station_names (list[str]): 역 이름
            - coords (list[Vector3]): 각 지점의 좌표 (X, Y, Z)
            - directions (list[Vector3]): 각 지점에서의 진행 방향 벡터
        """
        self.parser.parse_route(filepath) #루트 파싱 실행
        self.current_route = self.parser.current_route # 파싱후 current_route 저장
        datalist = self.parser.extract_currentroute() # 필요한 요소만 리스트로 추출
        return datalist

    def convert_to_bveroute(self, extracted_currentroute_list: list):
        """
        extract_currentroute에서 반환된 리스트를 BVERouteData 객체로 변환.

        Args:
            extracted_currentroute_list (list): extract_currentroute에서 반환된 6개 리스트

        Returns:
            BVERouteData: 변환된 BVERouteData 객체
        """
        return BVERouteFactory.from_current_route(extracted_currentroute_list)

class FileController:
    def __init__(self):
        self.filepath: str = ''
        self.savefilepath: str = ''

    def open_file(self):
        filename = filedialog.askopenfilename(title="파일 열기")
        if filename:
            messagebox.showinfo("파일 선택", f"선택한 파일: {filename}")
            self.filepath = filename

    def save_file(self):
        filename = filedialog.asksaveasfilename(title="파일 저장")
        if filename:
            messagebox.showinfo("저장", f"저장 위치: {filename}")

    # 파일 읽기 함수
    def read_file(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
        except UnicodeDecodeError:
            with open(self.filepath, 'r', encoding='euc-kr') as file:
                lines = file.readlines()

        return lines


class EditController:
    def copy(self):
        messagebox.showinfo("복사", "복사 기능 실행")

    def paste(self):
        messagebox.showinfo("붙여넣기", "붙여넣기 기능 실행")
class SettingsController:
    def open_settings(self):
        messagebox.showinfo("환경 설정", "환경 설정 창 열기")
class HelpController:
    def show_help(self):
        messagebox.showinfo(title='정보', message='개발자 : dger 2025/08/28')