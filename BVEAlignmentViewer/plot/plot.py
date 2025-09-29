import tkinter as tk
from enum import Enum
from tkinter import messagebox
from typing import Union

from matplotlib.figure import Figure
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from Profile.profile import Profile
from core.profile.profileprocessor import ProfileProcessor
from model.bveroutedata import BVERouteData
from model.ipdata import EndPoint, IPdata


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

    def set_data(self, alignments: list[Union[EndPoint, IPdata]], bvedata:BVERouteData, profile: Profile):
        """새 데이터 설정"""
        self.alignments = alignments
        self.bvedata = bvedata
        self.profile = profile
        self.title = self.current_view
        self.redraw()

    def switch_view(self, view_type: ViewType):
        """뷰 전환 + redraw"""
        self.current_view = view_type
        self.redraw()

    def redraw(self):
        """현재 alignments 기준으로 현재 뷰 redraw"""
        if self.current_view == ViewType.PLAN:
            self.plot_plan_view(ViewType.PLAN.value)
        elif self.current_view == ViewType.PROFILE:
            self.plot_profile_view(ViewType.PROFILE.value)
        elif self.current_view == ViewType.SECTION:
            self.plot_section_view(ViewType.SECTION.value)

    def plot_plan_view(self, title):
        self.ax.clear()
        self.apply_decoration(title, "X(N)", "Y(E)")

        #IP라인 그리기
        x_data = [alignment.coord.x for alignment in self.alignments]
        y_data = [alignment.coord.y for alignment in self.alignments]
        if x_data and y_data:
            line, = self.ax.plot(x_data, y_data, color='gray', label='IP라인')
            self.set_fixed_view(x_data, y_data)
        #IP제원
        for i, alignment in enumerate(self.alignments):
            if i== 0:
                text = 'BP'
            elif i == len(self.alignments)-1:
                text = 'EP'
            else:
                text = f'IP{alignment.ipno}\nR={alignment.radius}'
            self.ax.text(alignment.coord.x, alignment.coord.y, text)
        #곡선 그리기
        x_data = [coord.x for coord in self.bvedata.coords]
        y_data = [coord.y for coord in self.bvedata.coords]
        if x_data and y_data:
            line, = self.ax.plot(x_data, y_data, color='red', label='FL')
        self.ax.legend()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.draw()

    def plot_profile_view(self, title):
        self.ax.clear()
        self.apply_decoration(title, "X(거리)", "Y(표고)",set_aspect='auto')

        #종단 선
        #VIP라인 그리기
        x_data = [pvi.station for pvi in self.profile.pvis]
        y_data = [pvi.elevation for pvi in self.profile.pvis]
        if x_data and y_data:
            line, = self.ax.plot(x_data, y_data, color='red', label='FL')
            self.ax.set_xlim(min(x_data), max(x_data))
            self.ax.set_ylim(min(y_data), max(y_data))

        self.ax.legend()
        self.toolbar.update()
        self.canvas.draw()

    def plot_section_view(self, title):
        """횡단면도: 추후 구현 예정"""
        self.ax.clear()
        self.apply_decoration(title, "X", "Y")
        self.ax.text(
            0.5, 0.5,
            "SECTION VIEW (미구현)",
            ha="center", va="center", transform=self.ax.transAxes,
            fontsize=12, color="red"
        )
        self.canvas.draw()

    def apply_decoration(self, title, xlabel, ylabel, show_grid=True, set_aspect="equal"):
        """그래프 기본 스타일 적용"""
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        if show_grid:
            self.ax.grid(True)
        self.ax.axis('on')
        self.ax.set_aspect(set_aspect)

    def set_fixed_view(self, x_data, y_data, box_size=1000):
        """
        데이터 중심 기준으로 항상 고정된 박스를 설정하고,
        데이터 범위에 따라 축척을 유동적으로 조정
        """
        if not x_data or not y_data:
            return

        # 데이터 중심 계산
        x_center = (max(x_data) + min(x_data)) / 2
        y_center = (max(y_data) + min(y_data)) / 2

        # 데이터 크기
        data_width = max(x_data) - min(x_data)
        data_height = max(y_data) - min(y_data)

        # 초기 박스 크기 절반
        half_box = box_size / 2

        # 데이터 크기에 맞춰 스케일 조정
        scale_x = data_width / box_size if data_width > box_size else 1
        scale_y = data_height / box_size if data_height > box_size else 1
        scale = max(scale_x, scale_y)

        half_width = half_box * scale
        half_height = half_box * scale

        # x, y 범위 설정
        self.ax.set_xlim(x_center - half_width, x_center + half_width)
        self.ax.set_ylim(y_center - half_height, y_center + half_height)

        # 화면 비율 유지
        self.ax.set_aspect("equal")


