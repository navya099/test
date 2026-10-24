# visual/mappapp.py (상단)
import logging
import threading
import time
from queue import Queue

import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
from matplotlib import pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import contextily as ctx

from xref.utils.coordinate_utils import convert_coordinates
from local.localentry import run_main_process

logger = logging.getLogger(__name__)


def _setup_korean_font():
    for name in ("Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR"):
        if any(f.name == name for f in fm.fontManager.ttflist):
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False


_setup_korean_font()

class MapVisualizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.end_scatter = None
        self.start_scatter = None
        self.dragging_target = None
        self.dragging_index = None
        self.points = []   # 리스트로 초기화
        self.title("지도 맵")
        self.geometry("1200x1000")


        self.fig, self.ax = plt.subplots(figsize=(8, 6))

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()

        # 이벤트 등록
        self.canvas.mpl_connect('pick_event', self.on_pick)
        self.canvas.mpl_connect('motion_notify_event', self.on_drag)
        self.canvas.mpl_connect('button_release_event', self.on_release)


        control = ttk.Frame(self)
        control.pack(fill=tk.X, pady=5)

        self._run_button = ttk.Button(control, text="실행", command=self.run)
        self._run_button.pack(side=tk.LEFT, padx=5)

        #초기 포인트 지정
        self.start = 14135232.111179,4518422.053022 #서울
        self.end = 14149229.343401,4506939.479597 #수서

        xs = [self.start[0], self.end[0]]
        ys = [self.start[1], self.end[1]]
        margin_x = (max(xs) - min(xs)) * 0.15 or 500
        margin_y = (max(ys) - min(ys)) * 0.15 or 500
        self.ax.set_xlim(min(xs) - margin_x, max(xs) + margin_x)
        self.ax.set_ylim(min(ys) - margin_y, max(ys) + margin_y)

        self.update_plot("초기화")

    def run(self):
        if not (self.start and self.end):
            messagebox.showwarning("경고", "시작점과 끝점을 먼저 선택하세요!")
            return

        start_lonlat = convert_coordinates(self.start, 3857, 4326)
        end_lonlat = convert_coordinates(self.end, 3857, 4326)
        start = (start_lonlat[1], start_lonlat[0])
        end = (end_lonlat[1], end_lonlat[0])

        self._set_busy(True)
        self._result_queue = Queue()

        def worker():
            try:
                top = run_main_process(
                    start, end,
                    n_candidates=30, n_generations=50, top_n=10, chain=25,
                )
                self._result_queue.put(("ok", top))
            except Exception as e:
                logger.exception("run_main_process 실패")
                self._result_queue.put(("err", e))

        threading.Thread(target=worker, daemon=True).start()
        self.after(100, self._poll_result)

    def _poll_result(self):
        try:
            status, payload = self._result_queue.get_nowait()
        except Exception:
            self.after(100, self._poll_result)
            return

        self._set_busy(False)
        if status == "ok":
            messagebox.showinfo("정보", "모든 작업이 성공적으로 완료됐습니다.")
        else:
            messagebox.showerror("실행 실패", str(payload))

    def _set_busy(self, busy: bool):
        if hasattr(self, "_run_button"):
            self._run_button.config(state=tk.DISABLED if busy else tk.NORMAL)

    def on_pick(self, event):
        # 시작점인지 확인
        if event.artist == self.start_scatter:
            self.dragging_target = "start"
            self.dragging_index = event.ind[0]
            print(f'시작 좌표 : {self.start[0]},{self.start[1]}')# 항상 0
            return

        # 끝점인지 확인
        if event.artist == self.end_scatter:
            self.dragging_target = "end"
            self.dragging_index = event.ind[0]  # 항상 0
            print(f'끝 좌표 : {self.end[0]},{self.end[1]}')  # 항상 0
            return

    def on_drag(self, event):
        if self.dragging_index is None:
            return
        now = time.monotonic()
        if now - getattr(self, "_last_drag", 0) < 0.03:  # 30ms
            return
        self._last_drag = now
        self._drag_pi(event)

    def _drag_pi(self, event):
        """PI 드래그 중 (지도 갱신 생략)"""
        if self.dragging_index is None:
            return
        if event.xdata is None or event.ydata is None:
            return
        # 좌표 갱신
        if self.dragging_target == "start":
            self.start = (event.xdata, event.ydata)
        elif self.dragging_target == "end":
            self.end = (event.xdata, event.ydata)

        # 지도 제외 부분 갱신
        self._redraw_partial()

    def _redraw_partial(self):
        # 줌/이동 유지
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        # 잔상 제거: PI scatter + midpoint scatter + 세그먼트 선들 제거
        if self.start_scatter:
            self.start_scatter.remove()
            self.start_scatter = None
        if self.end_scatter:
            self.end_scatter.remove()
            self.end_scatter = None

        # 다시 그림 (지도는 건드리지 않음)
        self._draw_segments()

        # 축 복원
        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)

        self.canvas.draw_idle()

    def on_release(self, event):
        if self.dragging_index is None:
            return

        # 줌/이동 상태 저장
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        # 전체 갱신 (지도 포함)
        self.update_plot("드래그 종료")

        # 확대/이동 복원
        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)
        self.canvas.draw_idle()

        # 상태 초기화
        self.dragging_index = None

    def update_plot(self, title="SegmentCollection",
                    force_xlim=None, force_ylim=None, zoom=None):
        """전체 다시 그림 — 지도 로딩은 _draw_map_basemap 한 번만."""
        self.ax.clear()
        self.ax.set_title(title)
        self._draw_segments()
        self._draw_map_basemap(zoom=zoom, force_xlim=force_xlim, force_ylim=force_ylim)
        # update_map_zoom() 호출 제거 (중복)
        self.canvas.draw_idle()

    def _draw_map_basemap(self, zoom=None, force_xlim=None, force_ylim=None):
        if not (self.start and self.end):
            logger.warning("start/end 미설정 — 베이스맵 생략")
            return

        xs = [self.start[0], self.end[0]]
        ys = [self.start[1], self.end[1]]
        margin_x = (max(xs) - min(xs)) * 0.15 or 500
        margin_y = (max(ys) - min(ys)) * 0.15 or 500

        if force_xlim is not None and force_ylim is not None:
            self.ax.set_xlim(force_xlim)
            self.ax.set_ylim(force_ylim)
        else:
            self.ax.set_xlim(min(xs) - margin_x, max(xs) + margin_x)
            self.ax.set_ylim(min(ys) - margin_y, max(ys) + margin_y)

        self.ax.set_aspect("equal", adjustable="datalim")

        if zoom is None:
            dx = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]
            dy = self.ax.get_ylim()[1] - self.ax.get_ylim()[0]
            zoom = int(np.clip(18 - np.log2(max(dx, dy) / 500), 5, 18))
        else:
            zoom = int(np.clip(zoom, 5, 18))

        try:
            ctx.add_basemap(
                self.ax,
                crs="EPSG:3857",
                source=ctx.providers.OpenStreetMap.Mapnik,
                zoom=zoom,
            )
        except Exception as e:
            logger.warning("베이스맵 로드 실패: %s (zoom=%s)", e, zoom)

    def save_lim(self):
        # 현재 확대/이동 상태 저장
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        return xlim, ylim

    def restore_lim(self, xlim, ylim):
        # 축 상태 복원
        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)

    def _draw_segments(self):
        """세그먼트 + PI + 텍스트"""
        x, y = self.start
        self.start_scatter = self.ax.scatter(x, y, color='red', marker='x', s=60,
                                          zorder=6, picker=5)
        x, y = self.end
        self.end_scatter = self.ax.scatter(x, y, color='blue', marker='x', s=60,
                                             zorder=6, picker=5)

        self.ax.set_aspect('equal', adjustable='datalim')
        self.ax.grid(False)

    def update_map_zoom(self):
        """현재 뷰 범위 기반으로 지도 타일만 다시 로드."""
        try:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            dx = xlim[1] - xlim[0]
            dy = ylim[1] - ylim[0]
            zoom = int(np.clip(18 - np.log2(max(dx, dy) / 500), 5, 18))

            for im in list(self.ax.images):
                im.remove()

            ctx.add_basemap(
                self.ax, crs="EPSG:3857",
                source=ctx.providers.OpenStreetMap.Mapnik, zoom=zoom,
            )
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)
            self.canvas.draw_idle()
            logger.debug("지도 갱신 완료 zoom=%s", zoom)
        except Exception as e:
            logger.exception("지도 갱신 실패")
            messagebox.showerror("지도 갱신 실패", str(e))