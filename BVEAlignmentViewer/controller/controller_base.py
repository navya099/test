from tkinter import filedialog, messagebox

from core.parser import CSVRouteParser


# 기능 클래스(모든 기능을 넣을 예정)
class AppController:
    def __init__(self, main_app, file_controller):
        self.route_data = None
        self.main_app = main_app  # MainApp 인스턴스 (UI 접근용)
        self.file_ctrl = file_controller

        # Alignment 데이터 컨테이너

        # 기능 전담 클래스 인스턴스 보관
        self.parser = CSVRouteParser()

    def load_route(self, filepath: str):
        self.parser.parse_route(filepath) #루트 파싱 실행
        self.route_data = self.parser.current_route # 파싱후 current_route 저장
        return self.route_data

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