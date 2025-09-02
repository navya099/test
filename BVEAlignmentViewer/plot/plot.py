import tkinter as tk
from enum import Enum

from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class ViewType(Enum):
    PLAN = '평면'
    PROFILE = '종단'
    SECTION = '횡단'

class PlotFrame(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Matplotlib Figure 생성
        self.current_view = ViewType.PLAN
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

    def set_data(self, alignments, origin_bve_data):
        """새 데이터 설정"""
        self.alignments = alignments
        self.origin_bve_data = origin_bve_data
        self.title = self.current_view
        self.redraw()

    def redraw(self):
        """현재 alignments 기준으로 현재 뷰 redraw"""
        if self.current_view == ViewType.PLAN:
            self.plot_plan_view(ViewType.PLAN.value)
        elif self.current_view == ViewType.PROFILE:
            self.plot_profile_view(self.alignments, ViewType.PROFILE.value)
        elif self.current_view == ViewType.SECTION:
            self.plot_section_view(self.alignments, ViewType.SECTION.value)

    def plot_plan_view(self, title):
        self.ax.clear()
        self.apply_decoration(title, "X(N)", "Y(E)")

        #IP라인 그리기
        x_data = [alignment.coord.x for alignment in self.alignments]
        y_data = [alignment.coord.y for alignment in self.alignments]
        if x_data and y_data:
            line, = self.ax.plot(x_data, y_data, label='IP라인')
        #곡선 그리기
        x_data = [coord.x for coord in self.origin_bve_data.coords]
        y_data = [coord.y for coord in self.origin_bve_data.coords]
        if x_data and y_data:
            line, = self.ax.plot(x_data, y_data, color='red', label='FL')
        self.ax.legend()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.draw()

    def plot_profile_view(self, alignments, viewtype):
        pass
    def plot_section_view(self, alignments, viewtype):
        pass
    def apply_decoration(self, title, xlabel, ylabel, show_grid=True):
        """그래프 기본 스타일 적용"""
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        if show_grid:
            self.ax.grid(True)
        self.ax.axis('on')
        self.ax.set_aspect('equal')
