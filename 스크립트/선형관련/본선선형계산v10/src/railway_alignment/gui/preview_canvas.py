"""
평면 미리보기 캔버스 (줌/팬 지원, 뷰포트 유지)
================================================
- 마우스 휠: 커서 위치 기준 줌
- 좌클릭 드래그: 팬
- IP 마커 클릭: IP 선택 (드래그 없이 짧게 클릭)
- Ctrl+F / Ctrl+Home: 전체 보기
- 재계산 시 뷰포트 유지 (편집 중 확대/이동 상태 보존)
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk,
)
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)

try:
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False
except Exception:
    pass


class PreviewCanvas(ttk.Frame):
    """평면선형 미리보기 캔버스 (줌/팬/뷰포트 유지)"""

    ZOOM_FACTOR = 1.2
    CLICK_TOLERANCE_PX = 8

    def __init__(
        self,
        master: tk.Widget,
        on_ip_click: Optional[Callable[[int], None]] = None,
    ):
        super().__init__(master)
        self._on_ip_click = on_ip_click

        # IP 마커 상태
        self._highlighted_ip: Optional[int] = None
        self._ip_markers: dict[int, plt.Line2D] = {}
        self._ip_positions: dict[int, tuple[float, float]] = {}

        # 팬 상태
        self._pan_start: Optional[tuple[float, float]] = None
        self._pan_xlim: Optional[tuple[float, float]] = None
        self._pan_ylim: Optional[tuple[float, float]] = None
        self._pan_moved: bool = False

        # ✅ 최초 fit 여부 추적 (뷰포트 유지용)
        self._has_initial_fit: bool = False
        self._last_xlim: Optional[tuple[float, float]] = None
        self._last_ylim: Optional[tuple[float, float]] = None

        self._build()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build(self) -> None:
        self.figure = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.figure.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        toolbar_frame = ttk.Frame(self)
        toolbar_frame.pack(fill="x")
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        ttk.Button(
            toolbar_frame, text="맞춤", command=self.fit_view, width=6,
        ).pack(side="left", padx=(8, 2))

        ttk.Label(
            toolbar_frame,
            text="휠:줌 | 드래그:이동 | Ctrl+F:맞춤",
            foreground="gray",
        ).pack(side="left", padx=(8, 4))

        # 이벤트
        self.canvas.mpl_connect("scroll_event", self._on_scroll)
        self.canvas.mpl_connect("button_press_event", self._on_button_press)
        self.canvas.mpl_connect("button_release_event", self._on_button_release)
        self.canvas.mpl_connect("motion_notify_event", self._on_motion)

        # 키보드 단축키
        self.canvas.get_tk_widget().bind("<Control-f>", lambda e: self.fit_view())
        self.canvas.get_tk_widget().bind("<Control-F>", lambda e: self.fit_view())
        self.canvas.get_tk_widget().bind("<Control-Home>", lambda e: self.fit_view())

        self._init_axes()

    def _init_axes(self) -> None:
        self.ax.set_aspect("equal")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlabel("East (Y) [m]")
        self.ax.set_ylabel("North (X) [m]")
        self.ax.set_title("평면선형 미리보기", fontsize=10)

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------
    def plot_alignment(
        self,
        ip_points: list[tuple[float, float]],
        element_points: Optional[list[tuple[float, float]]] = None,
        clear_first: bool = True,
        labels: Optional[list[str]] = None,
    ) -> None:
        # ✅ 현재 뷰포트 저장 (fit 이후 상태 기준)
        prev_view = self._capture_view() if self._has_initial_fit else None

        if clear_first:
            self._reset_axes()

        # 선형 본체
        if element_points and len(element_points) >= 2:
            pts = [self._to_plot(p) for p in element_points]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            self.ax.plot(xs, ys, "-", color="tab:blue", lw=1.5, label="선형")
        elif ip_points and len(ip_points) >= 2:
            pts = [self._to_plot(p) for p in ip_points]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            self.ax.plot(xs, ys, "--", color="tab:gray", lw=1.0, label="IP 연결(참고)")

        # IP 마커
        for idx, (x, y) in enumerate(ip_points):
            px, py = self._to_plot((x, y))
            marker, = self.ax.plot(px, py, "o", color="tab:red", markersize=7)
            self._ip_markers[idx] = marker
            self._ip_positions[idx] = (x, y)

            label_text = (
                labels[idx] if labels and idx < len(labels)
                else f"IP{idx + 1}"
            )
            self.ax.annotate(
                label_text, (px, py),
                textcoords="offset points", xytext=(5, 5),
                fontsize=8, color="tab:red",
            )

        if self._highlighted_ip is not None:
            self._apply_highlight(self._highlighted_ip)

        if self._ip_markers or element_points:
            self.ax.legend(loc="best", fontsize=8)

        # ✅ 뷰포트 복원 또는 최초 1회만 fit
        if self._has_initial_fit and prev_view is not None:
            self._restore_view(prev_view)
        else:
            self._auto_fit()
            self._has_initial_fit = True

        self.canvas.draw_idle()

    def highlight_ip(self, ip_index: Optional[int]) -> None:
        if self._highlighted_ip is not None:
            prev = self._ip_markers.get(self._highlighted_ip)
            if prev is not None:
                prev.set_markersize(7)
                prev.set_color("tab:red")
        self._highlighted_ip = ip_index
        if ip_index is not None:
            self._apply_highlight(ip_index)
        self.canvas.draw_idle()

    def clear(self) -> None:
        self._reset_axes()
        self._has_initial_fit = False   # ✅ clear 시 다시 fit 준비
        self.canvas.draw_idle()

    def fit_view(self) -> None:
        """전체 선형이 화면에 맞도록 자동 스케일."""
        self._auto_fit()
        self.canvas.draw_idle()

    def reset_view_state(self) -> None:
        """뷰포트 상태 초기화 (다음 플롯 시 자동 fit).

        새 파일 열기, 프로젝트 로드 시 호출.
        편집 중 재계산 시에는 호출하지 않아 뷰포트가 유지됨.
        """
        self._has_initial_fit = False

    # ------------------------------------------------------------------
    # 뷰포트 관리
    # ------------------------------------------------------------------
    def _capture_view(self) -> tuple[tuple[float, float], tuple[float, float]]:
        return (self.ax.get_xlim(), self.ax.get_ylim())

    def _restore_view(
        self, view: tuple[tuple[float, float], tuple[float, float]],
    ) -> None:
        xlim, ylim = view
        try:
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)
        except Exception:
            logger.exception("뷰포트 복원 실패, 자동 fit으로 대체")
            self._auto_fit()

    def _auto_fit(self) -> None:
        self.ax.relim()
        self.ax.autoscale_view()

    # ------------------------------------------------------------------
    # 내부
    # ------------------------------------------------------------------
    def _reset_axes(self) -> None:
        self.ax.clear()
        self._ip_markers.clear()
        self._ip_positions.clear()
        self._init_axes()

    def _apply_highlight(self, ip_index: int) -> None:
        marker = self._ip_markers.get(ip_index)
        if marker is not None:
            marker.set_markersize(11)
            marker.set_color("tab:orange")

    def _to_plot(self, p: tuple[float, float]) -> tuple[float, float]:
        x_north, y_east = p
        return (y_east, x_north)

    # ---------- 줌 ----------
    def _on_scroll(self, event) -> None:
        # ✅ matplotlib 툴바 모드 활성 시 무시
        if getattr(self.toolbar, "mode", "") != "":
            return
        if event.inaxes != self.ax:
            return
        if event.xdata is None or event.ydata is None:
            return

        zoom_factor = self.ZOOM_FACTOR if event.button == "up" else 1.0 / self.ZOOM_FACTOR
        x, y = event.xdata, event.ydata
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        new_xlim = (
            x - (x - xlim[0]) / zoom_factor,
            x + (xlim[1] - x) / zoom_factor,
        )
        new_ylim = (
            y - (y - ylim[0]) / zoom_factor,
            y + (ylim[1] - y) / zoom_factor,
        )
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.canvas.draw_idle()

    # ---------- 팬 + 클릭 ----------
    def _on_button_press(self, event) -> None:
        # ✅ matplotlib 툴바 모드 활성 시 자체 팬 무시
        if getattr(self.toolbar, "mode", "") != "":
            return
        if event.inaxes != self.ax:
            return
        if event.button != 1:
            return

        if self._find_nearest_ip(event.x, event.y) is not None:
            return

        self._pan_start = (event.xdata, event.ydata)
        self._pan_xlim = self.ax.get_xlim()
        self._pan_ylim = self.ax.get_ylim()
        self._pan_moved = False

    def _on_motion(self, event) -> None:
        if self._pan_start is None or event.xdata is None or event.ydata is None:
            return
        dx = event.xdata - self._pan_start[0]
        dy = event.ydata - self._pan_start[1]

        x_range = self._pan_xlim[1] - self._pan_xlim[0]
        threshold = x_range / 1000
        if abs(dx) > threshold or abs(dy) > threshold:
            self._pan_moved = True

        self.ax.set_xlim(self._pan_xlim[0] - dx, self._pan_xlim[1] - dx)
        self.ax.set_ylim(self._pan_ylim[0] - dy, self._pan_ylim[1] - dy)
        self.canvas.draw_idle()

    def _on_button_release(self, event) -> None:
        was_drag = self._pan_moved
        self._pan_start = None
        self._pan_xlim = None
        self._pan_ylim = None
        self._pan_moved = False

        if not was_drag and event.button == 1:
            self._handle_ip_click(event)

    def _handle_ip_click(self, event) -> None:
        if event.inaxes != self.ax or event.xdata is None:
            return
        if not self._ip_positions:
            return

        best_idx = self._find_nearest_ip(event.x, event.y)
        if best_idx is None:
            return

        self.highlight_ip(best_idx)
        if self._on_ip_click is not None:
            try:
                self._on_ip_click(best_idx)
            except Exception:
                logger.exception("on_ip_click 콜백 실행 중 오류")

    def _find_nearest_ip(self, click_x_px: float, click_y_px: float) -> Optional[int]:
        best_idx = None
        best_dist_sq = float("inf")
        for idx, (x_data, y_data) in self._ip_positions.items():
            px, py = self._to_plot((x_data, y_data))
            try:
                x_px, y_px = self.ax.transData.transform((px, py))
            except Exception:
                continue
            dx = x_px - click_x_px
            dy = y_px - click_y_px
            dist_sq = dx * dx + dy * dy
            if dist_sq < best_dist_sq:
                best_dist_sq = dist_sq
                best_idx = idx

        if best_idx is None:
            return None
        if best_dist_sq > self.CLICK_TOLERANCE_PX ** 2:
            return None
        return best_idx