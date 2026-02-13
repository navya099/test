import tkinter as tk
from matplotlib import pyplot as plt
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk, messagebox

from utils.math_util import interpolate_cached, calculate_offset_point
from xref_module.transaction import Transaction


class PlotPoleMap(tk.Frame):
    def __init__(self, runner, events=None, master=None):
        super().__init__(master)
        self.selected_epole = None
        self.selected_pole_scatter = None
        self.sel_xy = None
        self.selected_pole = None
        self.runner = runner
        self.events = events
        if self.events:
            self.events.bind("pole_selected", self.on_pole_selected)

        # Matplotlib Figure/Axes 생성
        plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] = False

        self.fig, self.ax = plt.subplots(figsize=(8,8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # 툴바 추가
        toolbar = NavigationToolbar2Tk(self.canvas, self)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")

        # 이동 버튼 등록
        btn_left = tk.Button(self, text="-5m", command=self.move_left)
        btn_right = tk.Button(self, text="+5m", command=self.move_right)
        btn_left.pack(side="left")
        btn_right.pack(side="right")

    def draw_alignment(self):
        # polyline 좌표 꺼내기
        sta_list, x_list, y_list, z_list = zip(*self.runner.polyline_with_sta)
        # 선형 그리기 (예: x vs z)
        self.ax.plot(x_list, y_list, color="gray", label="선형")

    def draw_poles(self):
        # 전주 위치(pos)를 x축에 표시
        poles = self.runner.poledata
        x_val = [pole.coord[0] for pole in poles]
        y_val = [pole.coord[1] for pole in poles]
        self.ax.scatter(x_val, y_val, c="blue", marker="o", label="전주")

    def update_plot(self):
        self.ax.clear()
        self.ax.set_title("전주 위치 맵")
        self.ax.set_xlabel("X좌표")
        self.ax.set_ylabel("Y좌표")

        self.draw_alignment()
        self.draw_poles()
        self.canvas.draw()

    def highlight_pole(self, pos):
        self.ax.set_title("선택된 전주")
        self.ax.clear()
        self.draw_alignment()
        self.draw_poles()
        poles = self.runner.poledata
        # 선택된 전주 강조
        for pole in poles:
            if pole.pos == pos:
                self.selected_pole = pole
                self.sel_xy = pole.coord[0], pole.coord[1]

                self.selected_pole_scatter = self.ax.scatter(self.sel_xy[0], self.sel_xy[1], c="red", s=100, label="선택된 전주", picker=5)
                self.ax.text(self.sel_xy[0], self.sel_xy[1], f'{pole.post_number}')
                self.ax.set_xlim(self.sel_xy[0] - 50, self.sel_xy[0] + 50)
                self.ax.set_ylim(self.sel_xy[1] - 50, self.sel_xy[1] + 50)
                break

        self.ax.legend()
        self.canvas.draw()

    def on_pole_selected(self, epole):
        self.selected_epole = epole
        self.highlight_pole(epole.pole.pos)

    def move_left(self):
        self._move_pole(-5)

    def move_right(self):
        self._move_pole(+5)

    def _move_pole(self, delta):
        if not self.selected_epole: return

        new_pos = self.selected_epole.pole.pos + delta
        prev_pos = self.selected_epole.prev_pole.pole.pos if self.selected_epole.prev_pole else None
        next_pos = self.selected_epole.next_pole.pole.pos if self.selected_epole.next_pole else None

        # 범위 검사
        if prev_pos and new_pos <= prev_pos: return
        if next_pos and new_pos >= next_pos: return
        #타입ㄱ머사
        if self.selected_epole.pole.section is not None:
            messagebox.showerror('오류', f'{self.selected_epole.pole.post_number}: 지정한 전주는 일반개소가 아닙니다. 일반개소만 이동이 가능합니다.')
            return
        #span 검사
        new_prev_pole_span = new_pos - prev_pos #이전전주와의 span
        new_span = next_pos - new_pos #다음 전주와의 스판

        if new_prev_pole_span not in self.runner.dataprocessor.get_span_list() or new_span not in self.runner.dataprocessor.get_span_list():
            messagebox.showerror('오류', f'{self.selected_epole.pole.post_number}: 지정한 전주는 span 범위에 없습니다.')
            return

        # 보간 좌표 계산
        coord, _, v1 = interpolate_cached(self.runner.polyline_with_sta, new_pos)
        pos_coord_with_offset = calculate_offset_point(v1, coord, self.selected_epole.pole.gauge)

        # 최종 반영
        with Transaction(self.selected_epole.pole,
                         self.selected_epole.prev_pole.pole if self.selected_epole.prev_pole else None,
                         self.selected_epole.next_pole.pole if self.selected_epole.next_pole else None):
            self.selected_epole.update(pos=new_pos)

        self.selected_epole.pole.coord = pos_coord_with_offset
        self.runner.wire_data = self.runner.wire_processor.process_to_wire()
        self.runner.log(f"전주 {self.selected_epole.pole.post_number} 이동 완료: {new_pos}")

        self.highlight_pole(new_pos)
        self.events.emit('pole_moved') #전주 이동 이벤트 발생