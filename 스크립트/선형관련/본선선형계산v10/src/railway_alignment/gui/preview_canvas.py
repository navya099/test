"""
평면 미리보기 캔버스
=====================
Matplotlib을 Tkinter에 임베딩. IP 클릭 시 테이블과 동기화.

설계 원칙:
    - 외부 API의 인덱스는 0-based (result.curves 순서와 동일)
    - IP 좌표는 _ip_positions에 별도 저장 → 클릭 판정 시 transform 안전
    - plot_alignment()는 호출할 때마다 전체 재구성 (증분 갱신 없음)
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

# 한글 폰트 (Windows)
try:
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False
except Exception:
    pass


class PreviewCanvas(ttk.Frame):
    """평면선형 미리보기 캔버스.

    이벤트:
        on_ip_click(ip_index) — IP 마커 클릭 시 (0-based)
    """

    def __init__(
        self,
        master: tk.Widget,
        on_ip_click: Optional[Callable[[int], None]] = None,
    ):
        super().__init__(master)
        self._on_ip_click = on_ip_click

        # 상태
        self._highlighted_ip: Optional[int] = None
        self._ip_markers: dict[int, plt.Line2D] = {}
        self._ip_positions: dict[int, tuple[float, float]] = {}
        self._click_tolerance_px = 8

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

        self.canvas.mpl_connect("button_press_event", self._on_canvas_click)

        self._init_axes()

    def _init_axes(self) -> None:
        self.ax.set_aspect("equal")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlabel("X (North) [m]")
        self.ax.set_ylabel("Y (East) [m]")
        self.ax.set_title("평면선형 미리보기", fontsize=10)

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------
    def plot_alignment(
        self,
        ip_points: list[tuple[float, float]],
        element_points: Optional[list[tuple[float, float]]] = None,
        clear_first: bool = True,
    ) -> None:
        """평면선형을 캔버스에 그린다.

        Parameters
        ----------
        ip_points : [(X, Y), ...]
            IP 좌표 리스트 (curves 순서대로). 마커 인덱스 = 리스트 인덱스.
        element_points : [(X, Y), ...], optional
            요소별로 이어붙인 전체 선형 좌표 (result.polycurve).
            없으면 IP를 점선으로 연결한다.
        clear_first : bool
            True면 기존 아티스트 초기화 후 그림 (기본값).
        """
        if clear_first:
            self._reset_axes()

        # 1) 선형 본체
        if element_points and len(element_points) >= 2:
            xs = [p[0] for p in element_points]
            ys = [p[1] for p in element_points]
            self.ax.plot(xs, ys, "-", color="tab:blue", lw=1.5, label="선형")
        elif ip_points and len(ip_points) >= 2:
            xs = [p[0] for p in ip_points]
            ys = [p[1] for p in ip_points]
            self.ax.plot(
                xs, ys, "--", color="tab:gray", lw=1.0, label="IP 연결(참고)"
            )

        # 2) IP 마커 + 라벨
        for idx, (x, y) in enumerate(ip_points):
            marker, = self.ax.plot(
                x, y, "o", color="tab:red", markersize=7
            )
            self._ip_markers[idx] = marker
            self._ip_positions[idx] = (x, y)

            label = self._marker_label(idx, len(ip_points))
            self.ax.annotate(
                label,
                (x, y),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=8,
                color="tab:red",
            )

        # 3) 강조 표시 복원
        if self._highlighted_ip is not None:
            self._apply_highlight(self._highlighted_ip)

        # 4) 범례 + 자동 스케일
        if self._ip_markers or element_points:
            self.ax.legend(loc="best", fontsize=8)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()

    def highlight_ip(self, ip_index: Optional[int]) -> None:
        """특정 IP를 강조 표시(또는 해제).

        Parameters
        ----------
        ip_index : int | None
            0-based 인덱스. None이면 모든 강조 해제.
        """
        # 이전 강조 해제
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
        """캔버스 초기화."""
        self._reset_axes()
        self.canvas.draw_idle()

    def get_ip_count(self) -> int:
        """현재 그려진 IP 마커 개수."""
        return len(self._ip_markers)

    # ------------------------------------------------------------------
    # 내부
    # ------------------------------------------------------------------
    def _reset_axes(self) -> None:
        self.ax.clear()
        self._ip_markers.clear()
        self._ip_positions.clear()
        # 강조 상태는 유지 (재plot 후 복원)
        self._init_axes()

    def _marker_label(self, idx: int, total: int) -> str:
        """마커 라벨. BP/IP/EP 표시."""
        if total <= 1:
            return "IP"
        if idx == 0:
            return "BP"
        if idx == total - 1:
            return "EP"
        return f"IP{idx}"

    def _apply_highlight(self, ip_index: int) -> None:
        marker = self._ip_markers.get(ip_index)
        if marker is not None:
            marker.set_markersize(11)
            marker.set_color("tab:orange")

    def _on_canvas_click(self, event) -> None:
        """캔버스 클릭 → 가장 가까운 IP 마커 탐색 후 콜백."""
        if event.inaxes is not self.ax or event.xdata is None:
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

    def _find_nearest_ip(
        self, click_x_px: float, click_y_px: float
    ) -> Optional[int]:
        """픽셀 거리 기준으로 가장 가까운 IP 인덱스 반환."""
        best_idx: Optional[int] = None
        best_dist_sq = float("inf")

        for idx, (x_data, y_data) in self._ip_positions.items():
            try:
                x_px, y_px = self.ax.transData.transform((x_data, y_data))
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
        if best_dist_sq > self._click_tolerance_px ** 2:
            return None
        return best_idx