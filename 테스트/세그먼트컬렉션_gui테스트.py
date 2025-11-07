import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import copy
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk, FigureCanvasTkAgg
from pyproj import Transformer
import contextily as ctx

from data.alignment.alignment import Alignment
from data.alignment.exception.alignment_error import AlignmentError
from data.segment.curve_segment import CurveSegment
from data.segment.straight_segment import StraightSegment
from math_utils import draw_arc
from transaction import Transaction
from 세그먼트컬렉션_cui테스트 import test_current_collection
from AutoCAD.point2d import Point2d

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

transformer_to_3857 = Transformer.from_crs("EPSG:5186", "EPSG:3857", always_xy=True)
transformer_to_5186 = Transformer.from_crs("EPSG:3857", "EPSG:5186", always_xy=True)


class SegmentVisualizer(tk.Tk):
    """SegmentCollection 시각화 + 지도 모드 + 드래그 가능한 PI"""

    def __init__(self, alignment):
        super().__init__()
        self.title("SegmentCollection 시각화 테스트")
        self.geometry("1000x700")

        # 데이터 복제
        self.original_collection = alignment.collection
        self.collection = copy.deepcopy(alignment.collection)

        # matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # UI 컨트롤
        control = ttk.Frame(self)
        control.pack(fill=tk.X, pady=5)
        ttk.Label(control, text="PI 인덱스:").pack(side=tk.LEFT, padx=5)
        self.pi_index_var = tk.IntVar(value=1)
        ttk.Entry(control, textvariable=self.pi_index_var, width=5).pack(side=tk.LEFT)
        ttk.Button(control, text="PI 삭제", command=self.remove_pi).pack(side=tk.LEFT, padx=5)
        ttk.Button(control, text="초기화", command=self.reset_to_initial).pack(side=tk.LEFT, padx=5)

        self.add_pi_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(control, text="PI 추가", variable=self.add_pi_mode).pack(side=tk.LEFT, padx=10)

        self.remove_curve_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control, text="곡선만 삭제", variable=self.remove_curve_var).pack(side=tk.LEFT, padx=10)

        self.view_map_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(control, text="지도 보기", variable=self.view_map_mode,
                        command=lambda: self.update_plot("지도 갱신")).pack(side=tk.LEFT, padx=10)

        ttk.Button(control, text="곡선 추가", command=self.add_curve_ui).pack(side=tk.LEFT, padx=10)
        ttk.Button(control, text="곡선 변경", command=self.update_radius_ui).pack(side=tk.LEFT, padx=10)

        # 상태
        self.dragging_index = None
        self._overlay_artists = []

        # 이벤트 등록
        self.canvas.mpl_connect('pick_event', self.on_pick)
        self.canvas.mpl_connect('motion_notify_event', self.on_drag)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('button_press_event', self.add_pi)

        # 초기 표시
        self.update_plot("초기 상태")

    # ────────────────────────────────
    # UI 로직
    # ────────────────────────────────

    def add_curve_ui(self):
        """곡선 추가"""
        try:
            idx = self.pi_index_var.get()
            radius_str = simpledialog.askstring("곡선 추가", "곡선 반경 (R)을 입력하세요:", parent=self)
            if not radius_str:
                return
            radius = float(radius_str)
            if radius <= 0:
                raise ValueError("반경은 양수여야 합니다.")
            self.collection.add_curve_at_simple_curve(idx, radius)
            xlim, ylim = self.save_lim()
            self.update_plot()
            self.restore_lim(xlim, ylim)
            self.json_export()
            messagebox.showinfo("완료", f"PI {idx}에 반경 {radius:.2f}m 곡선 추가 완료")
        except Exception as e:
            messagebox.showerror("에러", str(e))

    def update_radius_ui(self):
        """곡선 반경 변경"""
        try:
            idx = self.pi_index_var.get()
            radius_str = simpledialog.askstring("곡선 변경", "새 반경 R을 입력:", parent=self)
            if not radius_str:
                return
            radius = float(radius_str)
            self.collection.update_radius_by_index(radius, idx)
            xlim, ylim = self.save_lim()
            self.update_plot()
            self.restore_lim(xlim, ylim)
            self.json_export()
        except Exception as e:
            messagebox.showerror("에러", str(e))

    def remove_pi(self):
        """PI 삭제"""
        idx = self.pi_index_var.get()
        try:
            if self.remove_curve_var.get():
                self.collection.remove_curve_at_pi_by_index(idx)
            else:
                self.collection.remove_pi_at_index(idx)
        except Exception as e:
            messagebox.showerror("오류", str(e))
            return
        xlim, ylim = self.save_lim()
        self.update_plot()
        self.restore_lim(xlim, ylim)
        self.json_export()

    def reset_to_initial(self):
        """초기 상태로 복원"""
        self.collection = copy.deepcopy(self.original_collection)
        self.update_plot("초기화 완료")

    def add_pi(self, event):
        """마우스 클릭으로 PI 추가"""
        if not self.add_pi_mode.get():
            return
        if event.xdata is None or event.ydata is None:
            return

        if self.view_map_mode.get():
            x, y = transformer_to_5186.transform(event.xdata, event.ydata)
        else:
            x, y = event.xdata, event.ydata
        coord = Point2d(x, y)

        try:
            idx = self.collection.add_pi_by_coord(coord)
            # 현재 확대/이동 상태 저장
            xlim, ylim = self.save_lim()
            self.update_plot()
            self.restore_lim(xlim, ylim)

            self.json_export()
        except Exception as e:
            messagebox.showerror("PI 추가 오류", str(e))

    # ────────────────────────────────
    # Plot / 지도 관련
    # ────────────────────────────────

    def update_plot(self, title="SegmentCollection"):
        """전체 다시 그림"""
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title(title)

        if self.view_map_mode.get():
            self._draw_map_basemap()

        self._draw_segments()
        self.canvas.draw_idle()

    def _draw_map_basemap(self):
        """지도 배경 추가"""
        if not self.collection.coord_list:
            return
        xs, ys = zip(*[transformer_to_3857.transform(pt.x, pt.y)
                       for pt in self.collection.coord_list])
        margin_x = (max(xs) - min(xs)) * 0.15 or 500
        margin_y = (max(ys) - min(ys)) * 0.15 or 500
        self.ax.set_xlim(min(xs) - margin_x, max(xs) + margin_x)
        self.ax.set_ylim(min(ys) - margin_y, max(ys) + margin_y)
        self.ax.set_aspect('equal', adjustable='datalim')
        try:
            ctx.add_basemap(self.ax, crs="EPSG:3857", source=ctx.providers.OpenStreetMap.Mapnik)
        except Exception as e:
            print(f"[지도 로드 실패]: {e}")

    def _draw_segments(self):
        """세그먼트 + PI + 텍스트"""
        colors = {"StraightSegment": "blue", "CurveSegment": "orange", "CUBICSegment": "green"}
        map_mode = self.view_map_mode.get()

        # --- 세그먼트 ---
        for seg in self.collection.segment_list:
            name = seg.__class__.__name__
            color = colors.get(name, "gray")
            pts = self._segment_to_xy(seg)
            if not pts:
                continue
            if map_mode:
                pts = [transformer_to_3857.transform(x, y) for x, y in pts]
            x, y = zip(*pts)
            self.ax.plot(x, y, color=color, lw=2, zorder=2)

        # --- PI ---
        if map_mode:
            pi_pts = [transformer_to_3857.transform(pt.x, pt.y)
                      for pt in self.collection.coord_list]
        else:
            pi_pts = [(pt.x, pt.y) for pt in self.collection.coord_list]

        x, y = zip(*pi_pts)
        self.pi_scatter = self.ax.scatter(x, y, color='red', marker='x', s=60,
                                          zorder=6, picker=5)
        self.ax.plot(x, y, color='red', linestyle='--', lw=1, zorder=4)

        # --- PI 텍스트 ---
        for i, (px, py) in enumerate(pi_pts):
            if i == 0:
                label = "BP"
            elif i == len(pi_pts) - 1:
                label = "EP"
            else:
                label = f"IP.{i}"
            self.ax.text(px, py + 20, label, fontsize=9, ha='center', va='bottom',
                         bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))

        self.ax.set_aspect('equal', adjustable='datalim')
        self.ax.grid(False)

    def _segment_to_xy(self, seg):
        if isinstance(seg, StraightSegment):
            return [(seg.start_coord.x, seg.start_coord.y),
                    (seg.end_coord.x, seg.end_coord.y)]
        if isinstance(seg, CurveSegment):
            x_arc, y_arc = draw_arc(seg.direction, seg.start_coord, seg.end_coord, seg.center_coord)
            return list(zip(x_arc, y_arc))
        return None

    def json_export(self):
        test_current_collection(self.collection, "c:/temp/")

    def save_lim(self):
        # 현재 확대/이동 상태 저장
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        return xlim, ylim

    def restore_lim(self, xlim, ylim):
        # 축 상태 복원
        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)

    # ────────────────────────────────
    # 드래그 이벤트
    # ────────────────────────────────

    def on_pick(self, event):
        if event.artist != self.pi_scatter:
            return
        self.dragging_index = event.ind[0]

    def on_drag(self, event):
        """PI 드래그 중 (지도 갱신 생략)"""
        if self.dragging_index is None:
            return
        if event.xdata is None or event.ydata is None:
            return

        # EPSG 변환 (지도 모드면 5186으로 변환)
        if self.view_map_mode.get():
            x, y = transformer_to_5186.transform(event.xdata, event.ydata)
        else:
            x, y = event.xdata, event.ydata

        new_point = Point2d(x, y)
        try:
            with Transaction(self.collection):
                self.collection.update_pi_by_index(new_point, self.dragging_index)
        except AlignmentError as e:
            messagebox.showerror('업데이트 실패', str(e))
            return
        else:
            # 확대/이동 상태 유지
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()

            # 기존 그래픽 제거 (지도는 그대로 둠)
            for artist in list(self.ax.lines) + list(self.ax.texts) + [self.pi_scatter]:
                artist.remove()

            # 지도는 다시 안 그림, 세그먼트 + PI만 다시 그림
            self._draw_segments()

            # 축 상태 복원
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)

            self.canvas.draw_idle()
            self.json_export()

    def on_release(self, event):
        """드래그 종료 → 지도 포함 전체 다시 그림"""
        if self.dragging_index is not None:
            # 현재 확대/이동 상태 저장
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()

            # 전체 갱신 (지도 포함)
            self.update_plot("PI 이동 완료")

            # 확대/이동 상태 복원
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)
            self.canvas.draw_idle()

            self.json_export()

        self.dragging_index = None


# ================= 실행 =================
if __name__ == "__main__":
    al = Alignment(name='test')
    coord_list = [
        Point2d(198322.295865, 551717.440486),
        Point2d(198989.169204, 548303.499112),
        Point2d(202935.041692, 545189.094109),
        Point2d(199139.705729, 536601.555990)
    ]
    radius_list = [None, 5000, 3100, None]
    al.create(coord_list, radius_list)
    app = SegmentVisualizer(al)
    app.mainloop()
