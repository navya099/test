
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import matplotlib
import numpy as np
from ezdxf.render import forms
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
        self.direction = Vector2(x=0, y=0)

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
        self.alignments = []

        # Matplotlib Figure 생성
        fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = fig.add_subplot(111)

        self.current_view = "plan"  # 기본 뷰
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

    def show_view(self, view_name):
        """뷰 전환 및 redraw"""
        self.current_view = view_name
        if self.alignments:
            self.redraw()

    def redraw(self):
        """현재 alignments 기준으로 현재 뷰 redraw"""
        if self.current_view == "plan":
            self.plot_plan_view(self.alignments, '평면')
        elif self.current_view == "profile":
            self.plot_profile_view(self.alignments, '종단')
        elif self.current_view == "section":
            self.plot_section_view(self.alignments, '횡단')

    def set_data(self, alignments, title):
        """새 데이터 설정"""
        self.alignments = alignments
        self.title = title
        self.redraw()

    def plot_plan_view(self, alignments, title):
        self.ax.clear()
        self.original_colors.clear()
        self.apply_decoration(title, "Station", "x")

        for alignment in alignments:
            x_data = [rail.coord.x for rail in alignment.raildata]
            y_data = [rail.coord.y for rail in alignment.raildata]
            z_data = [rail.coord.z for rail in alignment.raildata]
            if x_data and y_data:
                line, = self.ax.plot(x_data, y_data, label=alignment.name)
                self.original_colors[line] = line.get_color()

        self.ax.legend()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.draw()

    def plot_profile_view(self, alignments, title):
        self.ax.clear()
        self.original_colors.clear()
        self.apply_decoration(title, "Station", "x")

        for alignment in alignments:
            x_data = [rail.coord.x for rail in alignment.raildata]
            y_data = [rail.coord.y for rail in alignment.raildata]
            z_data = [rail.coord.z for rail in alignment.raildata]
            if x_data and y_data:
                line, = self.ax.plot(x_data, z_data, label=alignment.name)
                self.original_colors[line] = line.get_color()

        self.ax.legend()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.draw()

    def plot_section_view(self, alignments, title):
        pass

    def plot_forms(self, alignments: list[Alignment], forms: list[FormData]):
        for formdata in forms:
            x1_data = []
            y1_data = []
            x_data = []
            y_data = []
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
                    angle = rail1.direction.todegree()  - 90
                    left_form_coord = Math.calculate_destination_coordinates(
                        Vector2(rail1.coord.x,rail1.coord.y),
                    angle,
                    2
                    )
                    angle = rail2.direction.todegree() + 90
                    right_form_coord = Math.calculate_destination_coordinates(
                        Vector2(rail2.coord.x, rail2.coord.y),
                        angle,
                        -2
                    )
                    x_data.append(left_form_coord.x)
                    y_data.append(left_form_coord.y)
                    x1_data.append(right_form_coord.x)
                    y1_data.append(right_form_coord.y)

                elif rail1 and form.rail2_index == -1:
                    angle = rail1.direction.todegree() + 90
                    left_form_coord = Math.calculate_destination_coordinates(
                        Vector2(rail1.coord.x, rail1.coord.y),
                        angle,
                        -2
                    )
                    right_form_coord = Math.calculate_destination_coordinates(
                        Vector2(rail1.coord.x, rail1.coord.y),
                        angle,
                        -7
                    )
                    x_data.append(rail1.coord.x)
                    y_data.append(rail1.coord.y)

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

class PlanViewFrame(tk.Frame):
    def plot(self, alignments, title):
        # 기존 plot_multiple 로직 적용
        pass

class ProfileViewFrame(tk.Frame):
    def plot(self, alignments, title):
        # 종단선용 y/z 좌표 plot
        pass

class SectionViewFrame(tk.Frame):
    def plot(self, alignments, title):
        # 단면도용 x/z or 특정 cross-section plot
        pass

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
        if filepath:
            filename = os.path.basename(filepath)
            lines = self.file_controller.read_file()
            self._process_and_plot(lines, filename)

    def reload(self):
        filepath = self.file_controller.filepath
        if filepath:
            filename = os.path.basename(filepath)
            lines = self.file_controller.read_file()
            self._process_and_plot(lines, filename)

    def _process_and_plot(self, lines, filename):
        # AppController에서 파싱과 메인라인 생성까지 책임지게 하는 게 깔끔
        alignments, forms = self.app_controller.build_alignments(lines)

        if alignments:
            self.app_controller.calculator.calculate_mainline_coordinates(alignments)
            self.app_controller.calculator.calculate_otherline_coordinates(alignments)
            # PlotFrame에 데이터 설정
            self.main_app.plot_frame.set_data(alignments, filename)

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

    def todegree(self) -> float:
        """벡터의 방향을 degree 단위로 반환 (0°=+X, 반시계 증가)."""
        return math.degrees(math.atan2(self.y, self.x))

class Vector3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def copy(self):
        return Vector3(self.x, self.y, self.z)

class Math:
    #2D MATH 변환
    @staticmethod
    def calculate_destination_coordinates(coord: Vector2, bearing: float, distance: float) -> Vector2:
        # Calculate the destination coordinates given a starting point, bearing, and distance in Cartesian coordinates
        angle = math.radians(bearing)
        x2 = coord.x + distance * math.cos(angle)
        y2 = coord.y + distance * math.sin(angle)
        return Vector2(x2, y2)

# 기능 클래스(모든 기능을 넣을 예정)
class AppController:
    def __init__(self, main_app, file_controller):
        self.main_app = main_app  # MainApp 인스턴스 (UI 접근용)
        self.file_ctrl = file_controller

        # Alignment 데이터 컨테이너
        self.alignments: list[Alignment] = []

        # 기능 전담 클래스 인스턴스 보관
        self.parser = AlignmentParser()
        self.calculator = AlignmentCalculator()

    def build_alignments(self, lines):
        alignments, forms, curves, min_station, max_station = self.parser.process_lines_to_alginment_data(lines)

        if alignments:
            main_alignment = self.calculator.create_mainline(min_station - 600, max_station + 600)
            main_alignment.curvedata.extend(curves)
            alignments.append(main_alignment)

        return alignments, forms

#라인파서
class AlignmentParser:
    def __init__(self):
        self.lines: list[str] = []
        self.line: str = ''
        self.linenumber: int = 0

    def _parse_line(self):
        """공통 파싱: station과 components 리스트 추출"""
        parts = self.line.split(',', 1)
        if len(parts) < 2:
            print(f"형식 오류: 줄 {self.linenumber}: {self.line}")
            return 0.0, []

        try:
            station = float(parts[0])
        except ValueError:
            print(f"ValueError: 줄 {self.linenumber} station parsing 실패")
            station = 0.0

        info = parts[1].strip().split(' ', 1)
        if len(info) < 2:
            print(f"형식 오류: 줄 {self.linenumber}: {self.line}")
            return station, []

        components = info[1].split(';')
        return station, components

    def parse_line(self, parse_func, cls):
        """
        제네릭 파서
        parse_func: components -> 필요한 값 반환
        cls: 생성할 도메인 클래스(Rail, Form, Curve 등)
        return: 생성한 클래스 객체
        """
        station, components = self._parse_line()
        if not components:
            return 0

        try:
            parsed_values = parse_func(components)
        except Exception as e:
            print(f"{cls.__name__} 파싱 실패: {e}")
            # 안전값 반환
            if cls.__name__ == "Rail":
                parsed_values = (0, 0.0, 0.0, 0)
            elif cls.__name__ == "Form":
                parsed_values = (0, 0, 0, 0)
            elif cls.__name__ == "Curve":
                parsed_values = (0.0, 0.0)
            else:
                parsed_values = ()

        # 객체 생성
        obj = cls(station, *parsed_values)
        return obj

    def parse_rail_components(self, components):
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
                print(f"ValueError: 줄 {self.linenumber} 열 {i} 파싱 실패: {val}")
        return rail_index, x, y, obj_index

    def parse_form_components(self, components):
        a, b, c, d = 0, 0, 0, 0
        for i, val in enumerate(components):
            try:
                if i == 0:
                    a = try_parse_int(val)
                elif i == 1:
                    b = try_parse_int(val)
                    if b == -1 or (isinstance(val, str) and val.strip().lower() == 'l'):
                        b = -1
                elif i == 2:
                    c = try_parse_int(val)
                elif i == 3:
                    d = try_parse_int(val)
            except ValueError:
                print(f"ValueError: 줄 {self.linenumber} 열 {i} 파싱 실패: {val}")
        return a, b, c, d

    def parse_curve_components(self, components):
        a, b = 0.0, 0.0
        for i, val in enumerate(components):
            try:
                if i == 0:
                    a = try_parse_float(val)
                elif i == 1:
                    b = try_parse_float(val)
            except ValueError:
                print(f"ValueError: 줄 {self.linenumber} 열 {i} 파싱 실패: {val}")
        return a, b
    #통합 처리 메소드
    def process_lines_to_alginment_data(self, lines):
        # 기존 변수 초기화
        alignment = None
        alignments = []
        station_list = []
        forms = []
        formdata = None
        self.lines = lines
        curve_list_for_main = []  # 자선에 넣을 curve 리스트 따로 저장

        line_type_map = {
            '.rail': (self.parse_rail_components, Rail),
            '.curve': (self.parse_curve_components, Curve),
            '.form': (self.parse_form_components, Form)
        }

        for linenumber, line in enumerate(self.lines, start=1):
            #linenumber와 line 상태저장
            self.linenumber = linenumber
            self.line = line.strip()

            if not self.line:
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

            line_lower = self.line.lower()
            matched = False
            for key, (parse_func, cls) in line_type_map.items():
                if key == '.rail' and key in line_lower and '.railtype' not in line_lower:
                    matched = True
                elif key != '.rail' and key in line_lower:
                    matched = True
                if matched:
                    obj = self.parse_line(parse_func, cls)
                    if obj:
                        if isinstance(obj, Rail):
                            station_list.append(obj.station)
                            if alignment:
                                alignment.raildata.append(obj)
                        elif isinstance(obj, Form) and formdata:
                            formdata.formdata.append(obj)
                        elif isinstance(obj, Curve):
                            curve_list_for_main.append(obj)
                    break  # 한 줄은 한 타입만

        # 마지막 배선, 폼 데이터 누락 방지
        if alignment and alignment.raildata:
            alignments.append(alignment)
        if formdata and formdata.formdata:
            forms.append(formdata)

        return alignments, forms ,curve_list_for_main,  min(station_list), max(station_list)

class AlignmentCalculator:
    def __init__(self):
        self.alignments: list[Alignment] = []

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
            rail.direction = direction.copy()

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

    def calculate_otherline_coordinates(self, alignments: list[Alignment]):
        # 자선 찾기
        main_alignment = next((a for a in alignments if a.name == '자선'), None)
        if not main_alignment:
            print('자선이 존재하지 않습니다.')
            return alignments

        # station -> mainrail dict 생성
        mainrail_map = {rail.station: rail for rail in main_alignment.raildata}

        for al in alignments:
            if al.name == '자선':
                continue  # 자선 스킵
            for rail in al.raildata:
                mainrail = mainrail_map.get(rail.station)
                if not mainrail:
                    continue
                # 좌표 변환
                #평면좌표
                angle = mainrail.direction.todegree() + (90 if rail.rail_x < 0 else -90)
                newcoord = Math.calculate_destination_coordinates(
                    Vector2(mainrail.coord.x, mainrail.coord.y),
                    angle,
                    abs(rail.rail_x)
                )
                new_z = mainrail.coord.z + rail.rail_y
                rail.coord.x = newcoord.x
                rail.coord.y = newcoord.y
                rail.coord.z = new_z

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

        #키 바인딩
        self.bind("<F5>", self.on_refresh)
        self.bind("<F6>", lambda e: self.plot_frame.show_view("plan"))
        self.bind("<F7>", lambda e: self.plot_frame.show_view("profile"))
        self.bind("<F8>", lambda e: self.plot_frame.show_view("section"))

    def on_refresh(self, event=None):
        # 새로고침 기능 구현
        # 예: 파일 다시 열기, 그래프 다시 그리기 등 원하는 동작 수행
        self.event_handler.reload()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
