import tkinter as tk

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk, messagebox

from matplotlib.collections import LineCollection

from utils.math_util import interpolate_cached, calculate_offset_point
from xref_module.preview.preview_sevice import PreviewService
from xref_module.preview.preview_viewer import PreviewViewer
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
        btn_preview = tk.Button(self, text="전주 미리보기", command=self.show_preview)
        btn_preview.pack(side="bottom")

        # ✅ 미리보기 뷰어를 한 번만 생성
        self.viewer = PreviewViewer()
        self.viewer.set_projection('front')

        self.service = PreviewService()

    def show_preview(self):
        self.viewer.objects.clear()
        result = self.service.build(self.selected_epole.pole)
        for obj in result.objects:
            self.viewer.add_object(obj)
        if result.missing:
            messagebox.showwarning(
                '일부 파일 누락',
                '다음 파일을 찾을 수 없습니다:\n\n' + '\n'.join(result.missing)
            )
        self.viewer.draw()

    def draw_alignment(self):
        # 본선 선형
        if self.runner.polyline_with_sta:
            # (x, y) 좌표 쌍을 라인 세그먼트로 변환
            points = [(x, y) for _, x, y, _ in self.runner.polyline_with_sta]
            segments = [(points[i], points[i + 1]) for i in range(len(points) - 1)]
            lc = LineCollection(segments, colors="gray", linewidths=1, label="본선 선형")
            self.ax.add_collection(lc)

        # 상선 선형
        if self.runner.track_mode == "double" and self.runner.offset_line_with_25:
            points_sub = [(x, y) for _, x, y in self.runner.offset_line_with_25]
            segments_sub = [(points_sub[i], points_sub[i + 1]) for i in range(len(points_sub) - 1)]
            lc_sub = LineCollection(segments_sub, colors="blue", linewidths=1, linestyles="--", label="상선 선형")
            self.ax.add_collection(lc_sub)

        self.ax.autoscale()  # 좌표 범위 자동 조정
        self.ax.legend()
        self.canvas.draw_idle()

    def draw_poles(self):
        # 본선 전주 좌표 배열
        main_coords = np.array([pole.coord for pole in self.runner.poledata.get("main", [])])
        if len(main_coords) > 0:
            self.ax.scatter(
                main_coords[:, 0], main_coords[:, 1],
                c="blue", marker="o", label="본선 전주"
            )

        # 상선 전주 좌표 배열
        sub_coords = np.array([pole.coord for pole in self.runner.poledata.get("sub", [])])
        if len(sub_coords) > 0:
            self.ax.scatter(
                sub_coords[:, 0], sub_coords[:, 1],
                c="green", marker="^", label="상선 전주"
            )

        self.ax.legend()
        self.canvas.draw_idle()

    def update_plot(self):
        self.ax.clear()
        self.ax.set_title("전주 위치 맵")
        self.ax.set_xlabel("X좌표")
        self.ax.set_ylabel("Y좌표")

        self.draw_alignment()
        self.draw_poles()
        self.canvas.draw_idle()

    def highlight_pole(self, pos):
        # 기존 선택 마커 삭제
        if hasattr(self, "selected_pole_scatter") and self.selected_pole_scatter:
            self.selected_pole_scatter.remove()

        # 선택된 전주 찾기
        for track_name, poles in self.runner.poledata.items():
            for pole in poles:
                if pole.pos == pos:
                    self.selected_pole = pole
                    self.sel_xy = pole.coord[0], pole.coord[1]

                    # 새로운 강조 마커만 추가
                    self.selected_pole_scatter = self.ax.scatter(
                        self.sel_xy[0], self.sel_xy[1],
                        c="red", s=100, zorder=5
                    )
                    self.ax.text(self.sel_xy[0], self.sel_xy[1], f'{pole.post_number}')
                    self.ax.set_xlim(self.sel_xy[0] - 50, self.sel_xy[0] + 50)
                    self.ax.set_ylim(self.sel_xy[1] - 50, self.sel_xy[1] + 50)
                    break

        self.canvas.draw_idle()

    def on_pole_selected(self, epole):
        self.selected_epole = epole
        self.highlight_pole(epole.pole.pos)

    def move_left(self):
        self._move_pole(-5)

    def move_right(self):
        self._move_pole(+5)

    def _move_pole(self, delta):
        if not self.selected_epole:
            return

        new_pos = self.selected_epole.pole.pos + delta
        prev_pos = self.selected_epole.prev_pole.pole.pos if self.selected_epole.prev_pole else None
        next_pos = self.selected_epole.next_pole.pole.pos if self.selected_epole.next_pole else None

        # 범위 검사
        if prev_pos and new_pos <= prev_pos:
            return
        if next_pos and new_pos >= next_pos:
            return

        # 타입 검사
        if self.selected_epole.pole.section is not None:
            messagebox.showerror('오류', f'{self.selected_epole.pole.post_number}: 지정한 전주는 일반개소가 아닙니다. 일반개소만 이동이 가능합니다.')
            return

        # span 검사
        new_prev_pole_span = new_pos - prev_pos if prev_pos else None
        new_span = next_pos - new_pos if next_pos else None
        if (new_prev_pole_span and new_prev_pole_span not in self.runner.dataprocessor.get_span_list()) or \
                (new_span and new_span not in self.runner.dataprocessor.get_span_list()):
            messagebox.showerror('오류', f'{self.selected_epole.pole.post_number}: 지정한 전주는 span 범위에 없습니다.')
            return

        # 본선/상선 구분해서 보간 좌표 계산
        if self.selected_epole.pole.track == "main":
            coord, _, v1 = interpolate_cached(self.runner.polyline_with_sta, new_pos)
        else:  # 상선
            coord, _, v1 = interpolate_cached(self.runner.offset_line_with_25, new_pos)

        pos_coord_with_offset = calculate_offset_point(v1, coord, self.selected_epole.pole.gauge)

        # 최종 반영
        with Transaction(
                self.selected_epole.pole,
                self.selected_epole.prev_pole.pole if self.selected_epole.prev_pole else None,
                self.selected_epole.next_pole.pole if self.selected_epole.next_pole else None
        ):
            self.selected_epole.update(pos=new_pos)

        self.selected_epole.pole.coord = pos_coord_with_offset
        self.runner.wire_data = self.runner.wire_processor.process_to_wire()
        self.runner.log(f"전주 {self.selected_epole.pole.post_number} 이동 완료: {new_pos}")

        self.highlight_pole(new_pos)
        if self.events:
            self.events.emit('pole_moved')