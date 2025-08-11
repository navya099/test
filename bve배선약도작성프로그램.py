
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import matplotlib
# ---- Matplotlib Tkinter 연결 ----
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import os

# bve클래스 정의
# alignment.py
class Rail:
    def __init__(self, station: float, railindex: int, rail_x: float, rail_y: float, object_index: int):
        self.station = station
        self.railindex = railindex
        self.rail_x = rail_x
        self.rail_y = rail_y
        self.object_index = object_index


class Alignment:
    def __init__(self, name: str):
        self.name: str = name
        self.raildata: list[Rail] = []


# 메뉴 클래스
# gui.py
class FileMenu(tk.Menu):
    def __init__(self, master, event_handler):
        super().__init__(master, tearoff=0)
        self.add_command(label="열기", command=event_handler.on_file_open)
        self.add_command(label="저장", command=event_handler.on_file_save)
        self.add_separator()
        self.add_command(label="종료", command=master.quit)



# menus/edit_menu.py
class EditMenu(tk.Menu):
    def __init__(self, master, controller):
        super().__init__(master, tearoff=0)
        self.controller = controller
        self.add_command(label="복사", command=self.controller.copy)
        self.add_command(label="붙여넣기", command=self.controller.paste)


# menus/settings_menu.py
class SettingsMenu(tk.Menu):
    def __init__(self, master, controller, event_handler):
        super().__init__(master, tearoff=0)
        self.controller = controller
        self.add_command(label="환경 설정", command=event_handler.on_open_settings)


# 도움말 및 정보 메뉴
class HelpMenu(tk.Menu):
    def __init__(self, master, controller):
        super().__init__(master, tearoff=0)
        self.controller = controller
        self.add_command(label='도움말', command=self.controller.show_help)


# 메뉴 메밍ㄴgui클래스
# 각 메뉴에 해당하는 컨트롤러를 직접 전달
class MenuGUI:
    def __init__(self, master, event_handler, edit_ctrl, settings_ctrl, help_ctrl):
        menubar = tk.Menu(master)
        menubar.add_cascade(label="파일", menu=FileMenu(menubar, event_handler))
        menubar.add_cascade(label="편집", menu=EditMenu(menubar, edit_ctrl))
        menubar.add_cascade(label="설정", menu=SettingsMenu(menubar, settings_ctrl, event_handler))
        menubar.add_cascade(label="도움말", menu=HelpMenu(menubar, help_ctrl))
        master.config(menu=menubar)



# plot.py
# matplot plot 클래스
class PlotFrame(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.original_colors = {}  # 선 객체별 원래 색 저장용 딕셔너리

        # Matplotlib Figure 생성
        fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = fig.add_subplot(111)

        # 한글 폰트 설정 (전역 설정)

        matplotlib.rcParams['font.family'] = 'Malgun Gothic'
        matplotlib.rcParams['axes.unicode_minus'] = False

        # 빈 상태라 아무 축도 설정하지 않음
        self.ax.clear()

        # 빈 도화지라 축 숨김
        self.ax.grid(True)
        self.ax.axis('off')

        # Figure를 Tkinter Canvas에 붙이기
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 툴바 생성 및 배치
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        self.toolbar.pack_forget()  # 초기에는 숨김

    def update_plot(self, x_data, y_data, title="그래프"):
        self.ax.clear()

        if x_data and y_data:  # 데이터가 있으면 툴바 보임
            self.apply_decoration(title, "X", "Y")
            self.ax.plot(x_data, y_data, marker="o")
            self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)  # 툴바 보이기
        else:
            # 데이터 없으면 빈 도화지 + 축 숨김 + 툴바 숨김
            self.ax.axis('off')
            self.toolbar.pack_forget()
        self.canvas.draw()

    def plot_multiple(self, alignments, title):
        self.ax.clear()
        self.original_colors.clear()
        self.apply_decoration(title, "Station", "x")
        for alignment in alignments:
            x_data = [rail.station for rail in alignment.raildata]
            y_data = [rail.rail_x * -1 for rail in alignment.raildata] #bve좌표계와 반대
            if x_data and y_data:
                line, = self.ax.plot(x_data, y_data, label=alignment.name)
                self.original_colors[line] = line.get_color()  # 원래 색 저장

        self.ax.legend()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.draw()

    def apply_decoration(self, title, xlabel, ylabel, show_grid=True):
        """그래프 기본 스타일 적용"""
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        if show_grid:
            self.ax.grid(True)
        self.ax.axis('on')

# 컨트롤러 클래스
# controller.py
class FileController:
    def __init__(self):
        self.filepath: str = ''

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
        messagebox.showinfo(title='도움말', message='도움말 열기')


# 유틸함수
# utils.py
def try_parse_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def try_parse_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def parse_rail_components(components, linenumber):
    rail_index, x, y, obj_index = 0, 0.0, 0.0, 0
    for i, val in enumerate(components):
        try:
            if i == 0:
                rail_index = try_parse_int(val)
            elif i == 1:
                x = try_parse_float(val)
            elif i == 2:
                y = try_parse_float(val)
            elif i == 3:
                obj_index = try_parse_int(val)
        except ValueError:
            print(f"ValueError: 줄 {linenumber} 열 {i} 파싱 실패: {val}")
    return rail_index, x, y, obj_index

#이벤트 핸들러
#EVNET.PY
class EventHandler:
    def __init__(self, main_app, app_controller, file_controller, settings_controller):
        self.some_option_var = None
        self.main_app = main_app
        self.app_controller = app_controller
        self.file_controller = file_controller
        self.settings_controller = settings_controller

    def on_file_open(self):
        self.file_controller.open_file()
        filepath = self.file_controller.filepath
        filename = os.path.basename(filepath)
        if filepath:
            lines = self.file_controller.read_file()
            alignments = self.app_controller.process_lines_to_alginment_data(lines)

            if alignments:
                #모든 배선 플로팅
                self.main_app.plot_frame.plot_multiple(alignments, filename)

    def reload(self):
        filepath = self.file_controller.filepath
        if filepath:
            lines = self.file_controller.read_file()
            alignments = self.app_controller.process_lines_to_alginment_data(lines)
            if alignments:
                self.main_app.plot_frame.plot_multiple(alignments, os.path.basename(filepath))

    def on_file_save(self):
        self.file_controller.save_file()

    def on_open_settings(self):
        settings_win = tk.Toplevel(self.main_app)
        settings_win.title("환경 설정")
        settings_win.geometry("300x150")

        self.some_option_var = tk.BooleanVar(value=False)
        # 체크박스가 바뀔 때 호출할 함수 연결
        chk = tk.Checkbutton(settings_win, text="배선 색 모두 동일하게", variable=self.some_option_var,
                             command=self.on_check_box_visible)
        chk.pack(pady=20)

        close_btn = tk.Button(settings_win, text="닫기", command=settings_win.destroy)
        close_btn.pack(pady=10)

    def on_check_box_visible(self):
        lines = self.main_app.plot_frame.ax.lines
        if self.some_option_var.get():
            for line in lines:
                line.set_color('black')
        else:
            for line in lines:
                original_color = self.main_app.plot_frame.original_colors.get(line, None)
                if original_color:
                    line.set_color(original_color)
                else:
                    line.set_color(None)
        self.main_app.plot_frame.canvas.draw()


# 기능 클래스(모든 기능을 넣을 예정)
class AppController:
    def __init__(self, main_app, file_controller):
        self.main_app = main_app  # MainApp 인스턴스 (UI 접근용)
        self.file_ctrl = file_controller

    def process_lines_to_alginment_data(self, lines):
        linenumber = 1  # 줄번호 추적변수
        currnet_rail_name = ''  # 배선이름
        currnetpart = 1  # 현재 파츠
        alignment = None
        alignments = []
        max_station = 0.0 #배선에서의 최소 측점
        min_station = 0.0 #배선에서의 최대측점
        station_list = [] #측점 저장 리스트

        for linenumber, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue

            # 주석으로 배선 이름 찾기 (예: ',;배선명')
            if line.startswith(',;'):
                # 이전 alignment가 있고, raildata가 있으면 저장
                if alignment and alignment.raildata:
                    alignments.append(alignment)

                # 새 배선 생성
                current_rail_name = line.split(';', 1)[1].strip()
                alignment = Alignment(current_rail_name)
                continue

            # rail 또는 railend 라인 처리
            # 예: '47725,.rail 5;10.895;0;'
            if '.rail' in line.lower() and '.railtype' not in line.lower():
                parts = line.split(',', 1)
                if len(parts) < 2:
                    print(f"형식 오류: 줄 {linenumber}: {line}")
                    continue

                try:
                    station = float(parts[0])
                except ValueError:
                    print(f"ValueError: 줄 {linenumber} station parsing 실패")
                    station = 0.0
                station_list.append(station)
                rail_info = parts[1].strip().split(' ', 1)
                if len(rail_info) < 2:
                    print(f"형식 오류: 줄 {linenumber}: {line}")
                    continue

                rail_components = rail_info[1].split(';')
                try:
                    rail_index, x, y, obj_index = parse_rail_components(rail_components, linenumber)
                except Exception as e:
                    print(f"함수 실행 실패: {e} ")
                    rail_index, x, y, obj_index = 0, 0.0, 0.0, 0  # 안전값 할당
                rail = Rail(station, rail_index, x, y, obj_index)
                if alignment is not None:
                    alignment.raildata.append(rail)
                else:
                    print(f"경고: 줄 {linenumber} - 배선 이름이 설정되지 않음")
            else:
                # rail 관련 구문이 아니면 무시
                continue

        #최소 최대 범위설정(bve 최소가시거리 600)
        min_station = min(station_list) - 600
        max_station = max(station_list) + 600
        #자선 추가
        alignments.append(self.create_mainline(min_station, max_station))

        #마지막 선형 추가
        # 반복문 끝난 뒤 마지막 alignment 추가
        if alignment and alignment.raildata:
            alignments.append(alignment)
        return alignments

    def create_mainline(self, min_station, max_station):
        al = Alignment(name='자선')
        count = int((max_station - min_station) // 25)
        for i in range(count):
            current_station = min_station + i * 25
            al.raildata.append(Rail(current_station,railindex=0, rail_x=0.0, rail_y=0.0,object_index=0))
        return al

# 메인클래스 main.py
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BVE 배선약도 작성 프로그램")
        self.geometry("650x450")

        # 컨트롤러 생성
        self.file_ctrl = FileController()
        self.edit_ctrl = EditController()
        self.settings_ctrl = SettingsController()
        self.help_ctrl = HelpController()
        self.appcontroller = AppController(self, self.file_ctrl)

        # 이벤트 핸들러 생성
        self.event_handler = EventHandler(self, self.appcontroller, self.file_ctrl, self.settings_ctrl)

        # 메뉴 GUI 생성 시 이벤트 핸들러 메서드를 넘김
        MenuGUI(self, self.event_handler, self.edit_ctrl, self.settings_ctrl, self.help_ctrl)


        # 메인 프레임
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # PLOT 프레임
        self.plot_frame = PlotFrame(main_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)

        # F5 키 바인딩
        self.bind("<F5>", self.on_refresh)

    def on_refresh(self, event=None):
        # 새로고침 기능 구현
        # 예: 파일 다시 열기, 그래프 다시 그리기 등 원하는 동작 수행
        self.event_handler.reload()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
