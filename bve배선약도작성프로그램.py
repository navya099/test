
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import matplotlib
import numpy as np
# ---- Matplotlib Tkinter 연결 ----
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import os
import math

from pandas.core.ops.mask_ops import raise_for_nan


# bve클래스 정의
# alignment.py
class Rail:
    def __init__(self, station: float, railindex: int, rail_x: float, rail_y: float, object_index: int):
        self.station = station
        self.railindex = railindex
        self.rail_x = rail_x
        self.rail_y = rail_y
        self.object_index = object_index
        self.coord = Vector3(x=0, y=0, z=0)

class Curve:
    def __init__(self, station: float, radius: float, cant: float):
        self.station = station
        self.radius = radius
        self.cant = cant

class Form:
    def __init__(self, station: float, rail1_index: int, rail2_index: int, roofindex: int, objindex: int):
        self.station = station
        self.rail1_index = rail1_index
        self.rail2_index = rail2_index
        self.roofindex = roofindex
        self.objindex = objindex

class FormData:
    def __init__(self, name: str):
        self.name = name
        self.formdata: list[Form] = []

class Alignment:
    def __init__(self, name: str):
        self.name = name
        self.raildata: list[Rail] = []
        self.curvedata: list[Curve] = []

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

        # 자선 찾기
        main_alignment = next((a for a in alignments if a.name == '자선'), None)
        if not main_alignment:
            print("자선이 없습니다.")
            main_station_to_y = {}
        else:
            # station: rail_y 딕셔너리 생성 (station은 고유한 키)
            main_station_to_y = {rail.station: rail.coord.y for rail in main_alignment.raildata}

        for alignment in alignments:
            x_data = [rail.station for rail in alignment.raildata]

            if alignment.name == '자선':
                y_data = [rail.coord.y for rail in alignment.raildata]
            else:
                y_data = []
                for i, rail in enumerate(alignment.raildata):
                    offset = main_station_to_y.get(rail.station, 0)  # station 기준 매칭, 없으면 0
                    y_val = -(rail.rail_x - offset)
                    # 기존 rail_x 반전 + 자선 rail_y 오프셋
                    y_data.append(y_val)

            if x_data and y_data:
                line, = self.ax.plot(x_data, y_data, label=alignment.name)
                self.original_colors[line] = line.get_color()

        self.ax.legend()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.draw()

    def plot_forms(self, alignments: list[Alignment], forms: list[FormData]):
        for formdata in forms:
            x_data = []
            y_data = []
            x1_data = []
            y1_data = []
            rail_map = {}
            for alignment in alignments:
                for rail in alignment.raildata:
                    key = (rail.railindex, rail.station)
                    rail_map[key] = rail

            for form in formdata.formdata:
                key1 = (form.rail1_index, form.station)
                key2 = (form.rail2_index, form.station)

                rail1 = rail_map.get(key1)
                rail2 = rail_map.get(key2)

                if rail1 and rail2:
                    x_data.append(rail1.station)
                    y_data.append((rail1.rail_x * -1) - 2)  # 2 이격, bve 좌표계 변환

                    x1_data.append(rail2.station)
                    y1_data.append((rail2.rail_x * -1) + 2)  # 반대 방향 이격

            x1_data.reverse()
            y1_data.reverse()

            x_data.extend(x1_data)
            y_data.extend(y1_data)

            # 닫힌 도형 위해 시작점 다시 추가
            if x_data and y_data:
                x_data.append(x_data[0])
                y_data.append(y_data[0])

            self.ax.plot(x_data, y_data, color='gray')

            # 중심 좌표 계산
            center_x = sum(x_data) / len(x_data)
            center_y = sum(y_data) / len(y_data)

            # 텍스트 추가 (formdata 이름 등 필요에 따라 바꾸기)
            self.ax.text(center_x, center_y, formdata.name, fontsize=12, ha='center', va='center', color='black')

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

def parse_form_components(components, linenumber):
    a, b, c, d = 0, 0, 0, 0
    for i, val in enumerate(components):
        try:
            if i == 0:
                a = try_parse_int(val)
            elif i == 1:
                b = try_parse_int(val)
            elif i == 2:
                c = try_parse_int(val)
            elif i == 3:
                d = try_parse_int(val)
        except ValueError:
            print(f"ValueError: 줄 {linenumber} 열 {i} 파싱 실패: {val}")
    return a, b, c, d

def parse_curve_components(components, linenumber):
    a, b = 0.0, 0.0
    for i, val in enumerate(components):
        try:
            if i == 0:
                a = try_parse_float(val)
            elif i == 1:
                b = try_parse_float(val)
        except ValueError:
            print(f"ValueError: 줄 {linenumber} 열 {i} 파싱 실패: {val}")
    return a, b

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
            alignments, forms = self.app_controller.process_lines_to_alginment_data(lines)

            if alignments:
                #자선 y값 조정(곡선반경 적용)
                alignments = self.app_controller.calculate_mainline_coordinates(alignments)
                #모든 배선 플로팅
                self.main_app.plot_frame.plot_multiple(alignments, filename)
            if forms:
                self.main_app.plot_frame.plot_forms(alignments, forms)

    def reload(self):
        filepath = self.file_controller.filepath
        if filepath:
            lines = self.file_controller.read_file()
            alignments ,forms = self.app_controller.process_lines_to_alginment_data(lines)
            if alignments:
                # 모든 배선 플로팅
                self.main_app.plot_frame.plot_multiple(alignments, os.path.basename(filepath))
            if forms:
                self.main_app.plot_frame.plot_forms(alignments, forms)

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

    def parse_lines_to_rail(self, line, linenumber):
        parts = line.split(',', 1)
        if len(parts) < 2:
            print(f"형식 오류: 줄 {linenumber}: {line}")
            return 0

        try:
            station = float(parts[0])
        except ValueError:
            print(f"ValueError: 줄 {linenumber} station parsing 실패")
            station = 0.0
        rail_info = parts[1].strip().split(' ', 1)
        if len(rail_info) < 2:
            print(f"형식 오류: 줄 {linenumber}: {line}")
            return 0

        rail_components = rail_info[1].split(';')
        try:
            rail_index, x, y, obj_index = parse_rail_components(rail_components, linenumber)
        except Exception as e:
            print(f"함수 실행 실패: {e} ")
            rail_index, x, y, obj_index = 0, 0.0, 0.0, 0  # 안전값 할당
        rail = Rail(station, rail_index, x, y, obj_index)


        return rail, station

    def parse_lines_to_form(self, line, linenumber):
        parts = line.split(',', 1)
        if len(parts) < 2:
            print(f"형식 오류: 줄 {linenumber}: {line}")
            return 0

        try:
            station = float(parts[0])
        except ValueError:
            print(f"ValueError: 줄 {linenumber} station parsing 실패")
            station = 0.0
        form_info = parts[1].strip().split(' ', 1)
        if len(form_info) < 2:
            print(f"형식 오류: 줄 {linenumber}: {line}")
            return 0

        form_components = form_info[1].split(';')
        try:
            rail1_index, rail2_index, roof_index, obj_index = parse_form_components(form_components, linenumber)
        except Exception as e:
            print(f"함수 실행 실패: {e} ")
            rail1_index, rail2_index, roof_index, obj_index = 0, 0, 0, 0  # 안전값 할당
        form = Form(station, rail1_index, rail2_index, roof_index, obj_index)

        return form

    def parse_lines_to_curve(self, line, linenumber):
        parts = line.split(',', 1)
        if len(parts) < 2:
            print(f"형식 오류: 줄 {linenumber}: {line}")
            return 0

        try:
            station = float(parts[0])
        except ValueError:
            print(f"ValueError: 줄 {linenumber} station parsing 실패")
            station = 0.0
        curve_info = parts[1].strip().split(' ', 1)
        if len(curve_info) < 2:
            print(f"형식 오류: 줄 {linenumber}: {line}")
            return 0

        curve_components = curve_info[1].split(';')
        try:
            radius, cant = parse_curve_components(curve_components, linenumber)
        except Exception as e:
            print(f"함수 실행 실패: {e} ")
            radius, cant = 0.0, 0.0 # 안전값 할당
        curve = Curve(station, radius, cant)

        return curve

    def process_lines_to_alginment_data(self, lines):
        # 기존 변수 초기화
        alignment = None
        alignments = []
        station_list = []
        forms = []
        formdata = None

        curve_list_for_main = []  # 자선에 넣을 curve 리스트 따로 저장

        for linenumber, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue

            if line.startswith(',;'):
                # 기존 alignment 저장
                if alignment and alignment.raildata:
                    alignments.append(alignment)

                # 새 배선 생성
                current_rail_name = line.split(';', 1)[1].strip()
                alignment = Alignment(current_rail_name)

                if formdata and formdata.formdata:
                    forms.append(formdata)
                formdata = FormData(current_rail_name)

                continue

            if '.rail' in line.lower() and '.railtype' not in line.lower():
                rail, station = self.parse_lines_to_rail(line, linenumber)
                station_list.append(station)
                if alignment:
                    alignment.raildata.append(rail)
                else:
                    print(f"경고: 줄 {linenumber} - 배선 이름이 설정되지 않음")

            # curve 구문은 기존 alignment에 넣지 말고 별도 리스트에 저장
            elif '.curve' in line.lower():
                try:
                    curve = self.parse_lines_to_curve(line, linenumber)
                    if curve:
                        curve_list_for_main.append(curve)  # 자선에 넣을 곡선 데이터 따로 저장
                except Exception as e:
                    print(f"경고: 줄 {linenumber}, parse_lines_to_curve에서 예외발생: 텍스트:{line}, 예외:{e}")

            elif '.form' in line.lower():
                try:
                    form = self.parse_lines_to_form(line, linenumber)
                    if form:
                        formdata.formdata.append(form)
                except Exception as e:
                    print(f"경고: 줄 {linenumber}, parse_lines_to_form에서 예외발생: 텍스트:{line}, 예외:{e}")
            else:
                continue

        min_station = min(station_list) - 600
        max_station = max(station_list) + 600

        # 자선 생성 및 curve 데이터 할당
        main_alignment = self.create_mainline(min_station, max_station)
        main_alignment.curvedata.extend(curve_list_for_main)  # 자선에만 curve 데이터 넣기
        alignments.append(main_alignment)

        # 마지막 배선, 폼 데이터 누락 방지
        if alignment and alignment.raildata:
            alignments.append(alignment)
        if formdata and formdata.formdata:
            forms.append(formdata)

        return alignments, forms

    def create_mainline(self, min_station, max_station):
        al = Alignment(name='자선')
        count = int((max_station - min_station) // 25)
        for i in range(count):
            current_station = min_station + i * 25
            al.raildata.append(Rail(current_station,railindex=0, rail_x=0.0, rail_y=0.0,object_index=0))
        return al

    def calculate_mainline_coordinates(self, alignments: list[Alignment]):

        # 자선 찾기
        main_alignment = next((a for a in alignments if a.name == '자선'), None)
        if not main_alignment:
            print('자선이 존재하지 않습니다.')
            return alignments  # 자선 없음

        curvedata = sorted(main_alignment.curvedata, key=lambda c: c.station)
        raildata = main_alignment.raildata

        # raildata에 station별 radius 할당 (곡선 반경 범위 할당)
        radius_map = {}

        current_radius = 0.0
        prev_station = 0.0

        for curve in curvedata:
            start_station = prev_station
            end_station = curve.station

            # start_station 이상 end_station 미만 범위의 raildata에 현재 radius 할당
            for rail in raildata:
                if start_station <= rail.station < end_station:
                    radius_map[rail.station] = current_radius

            current_radius = curve.radius
            prev_station = end_station

        # 마지막 곡선 이후 구간에 반경 할당
        for rail in raildata:
            if rail.station >= prev_station:
                radius_map[rail.station] = current_radius
        direction = Vector2(x=1.0, y=0.0)
        position = Vector3(x=raildata[0].station, y=0.0, z=0.0)
        for i, rail in enumerate(raildata):
            station = rail.station
            radius = radius_map.get(station, 0.0)


            data = []
            a = 0.0
            c = 25
            h = 0.0
            pitch = 0

            rail.coord.x = position.copy().x
            rail.coord.z = position.copy().y
            rail.coord.y = position.copy().z

            if radius != 0.0 and pitch != 0.0:
                d = 25
                p = pitch
                r = radius
                s = d / math.sqrt(1.0 + p * p)
                h = s * p
                b = s / abs(r)
                c = math.sqrt(2.0 * r * r * (1.0 - math.cos(b)))

                a = 0.5 * np.sign(r) * b
                direction.rotate(math.cos(-a), math.sin(-a))
            elif radius != 0.0:
                d = 25
                r = radius
                b = d / abs(r)
                c = math.sqrt(2.0 * r * r * (1.0 - math.cos(b)))
                a = 0.5 * np.sign(r) * b
                direction.rotate(math.cos(-a), math.sin(-a))
            elif pitch != 0.0:
                p = pitch
                d = 25
                c = d / math.sqrt(1.0 + p * p)
                h = c * p

            TrackYaw = math.atan2(direction.x, direction.y)
            TrackPitch = math.atan(pitch)

            position.x += direction.x * c
            position.y += h
            position.z += direction.y * c

            if a != 0.0:
                direction.rotate(math.cos(-a), math.sin(-a))


        return alignments

class Vector2:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def rotate(self, cosine_of_angle, sine_of_angle):
        x_new = cosine_of_angle * self.x - sine_of_angle * self.y
        y_new = sine_of_angle * self.x + cosine_of_angle * self.y
        self.x, self.y = x_new, y_new

    def copy(self):
        return Vector2(self.x, self.y)

class Vector3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def copy(self):
        return Vector3(self.x, self.y, self.z)

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
