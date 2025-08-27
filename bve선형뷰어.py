

from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import re
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import numpy as np
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import os
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import csv
import matplotlib
# ---- Matplotlib Tkinter 연결 ----
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from traits.trait_types import self


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

#도움말 및 정보 메뉴
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

#plot.py
#matplot plot 클래스
class PlotFrame(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Matplotlib Figure 생성
        fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = fig.add_subplot(111)

        # 한글 폰트 설정 (전역 설정)

        matplotlib.rcParams['font.family'] = 'Malgun Gothic'
        matplotlib.rcParams['axes.unicode_minus'] = False

        # 빈 상태라 아무 축도 설정하지 않음
        self.ax.clear()

        #빈 도화지라 축 숨김
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
            self.ax.plot(x_data, y_data, marker="o")
            self.ax.set_title(title)
            self.ax.set_xlabel("X축")
            self.ax.set_ylabel("Y축")
            self.ax.axis('on')  # 축 보임
            self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)  # 툴바 보이기
        else:
            # 데이터 없으면 빈 도화지 + 축 숨김 + 툴바 숨김
            self.ax.axis('off')
            self.toolbar.pack_forget()
        self.canvas.draw()

#컨트롤러 클래스
#controller.py
class FileController:
    def __init__(self):
        self.filepath: str = ''
        self.savefilepath: str = ''

    def open_file(self):
        filename = filedialog.askopenfilename(title="파일 열기")
        if filename:
            messagebox.showinfo("파일 선택", f"선택한 파일: {filename}")

    def save_file(self):
        filename = filedialog.asksaveasfilename(title="파일 저장")
        if filename:
            messagebox.showinfo("저장", f"저장 위치: {filename}")
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

    def on_file_save(self):
        filename = self.file_controller.save_file()
        if filename:
            messagebox.showinfo("파일 저장 기능", f"파일 저장 기능 {filename}")

    def on_open_settings(self):
        messagebox.showinfo("설정 기능", f"설정 저장 기능")

# 기능 클래스(모든 기능을 넣을 예정)
class AppController:
    def __init__(self, main_app, file_controller):
        self.main_app = main_app  # MainApp 인스턴스 (UI 접근용)
        self.file_ctrl = file_controller

        # Alignment 데이터 컨테이너

        # 기능 전담 클래스 인스턴스 보관

#메인클래스 main.py
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OPENBVE 선형뷰어")
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

        #PLOT 프레임
        self.plot_frame = PlotFrame(main_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
