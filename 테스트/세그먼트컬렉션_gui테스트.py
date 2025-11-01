import tkinter as tk
from tkinter import ttk, messagebox
import copy
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk, FigureCanvasTkAgg

from data.alignment.alignment import Alignment
from data.alignment.exception.alignment_error import AlignmentError
from data.segment.curve_segment import CurveSegment
from data.segment.straight_segment import StraightSegment
from math_utils import draw_arc
from transaction import Transaction
from 세그먼트컬렉션_cui테스트 import test_current_collection
from data.segment.segment_collection import SegmentCollection
from AutoCAD.point2d import Point2d

plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False

class SegmentVisualizer(tk.Tk):
    """SegmentCollection 시각적 테스트용 GUI + DRAG 가능 PI"""

    def __init__(self, alignment):
        super().__init__()
        self.title("SegmentCollection 시각화 테스트")
        self.geometry("1000x700")

        # --- 데이터 ---

        self.original_collection = alignment.collection
        self.collection = copy.deepcopy(alignment.collection)

        # --- matplotlib figure ---
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- control frame ---
        control = ttk.Frame(self)
        control.pack(fill=tk.X, pady=5)
        ttk.Label(control, text="삭제할 PI 인덱스:").pack(side=tk.LEFT, padx=5)
        self.pi_index_var = tk.IntVar(value=1)
        ttk.Entry(control, textvariable=self.pi_index_var, width=5).pack(side=tk.LEFT)
        ttk.Button(control, text="Before 보기", command=self.plot_before).pack(side=tk.LEFT, padx=5)
        ttk.Button(control, text="PI 삭제 후 보기", command=self.plot_after).pack(side=tk.LEFT, padx=5)
        ttk.Button(control, text="초기상태로 되돌리기", command=self.reset_to_initial).pack(side=tk.LEFT, padx=5)

        # ✅ ADD_PI 모드 버튼 추가
        self.add_pi_mode = False
        self.add_pi_button = ttk.Button(control, text="PI 추가 모드: OFF", command=self.toggle_add_pi_mode)
        self.add_pi_button.pack(side=tk.LEFT, padx=10)

        # --- drag 관련 상태 ---
        self.dragging_index = None

        # --- 이벤트 연결 ---
        self.canvas.mpl_connect('pick_event', self.on_pick)
        self.canvas.mpl_connect('motion_notify_event', self.on_drag)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        # ✅ 마우스 클릭으로 PI 추가
        self.canvas.mpl_connect('button_press_event', self.on_click)

        # 초기 그림 표시
        self.plot_before()

    # ✅ ADD_PI 모드 토글
    def toggle_add_pi_mode(self):
        self.add_pi_mode = not self.add_pi_mode
        if self.add_pi_mode:
            self.add_pi_button.config(text="PI 추가 모드: ON", style="Accent.TButton")
            messagebox.showinfo("PI 추가 모드", "화면을 클릭하면 해당 위치에 PI가 추가됩니다.")
        else:
            self.add_pi_button.config(text="PI 추가 모드: OFF")
            messagebox.showinfo("PI 추가 모드 종료", "PI 추가 모드가 비활성화되었습니다.")

    # ✅ 클릭 시 ADD_PI 실행
    def on_click(self, event):
        if not self.add_pi_mode:
            return  # 모드가 꺼져 있으면 무시
        if event.xdata is None or event.ydata is None:
            return

        coord = Point2d(event.xdata, event.ydata)
        try:
            idx = self.collection.add_pi_by_coord(coord)
            self.plot_before()
            self.json_export()
            messagebox.showinfo("PI 추가 완료", f"새로운 PI가 인덱스 {idx} 위치에 추가되었습니다.")
        except Exception as e:
            messagebox.showerror("PI 추가 오류", str(e))

        # 한 번 추가 후 모드 자동 종료 (원하면 유지도 가능)
        self.toggle_add_pi_mode()

    # --- 버튼 동작 ---
    def plot_before(self):
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Before: 기존 선형")
        self._draw_segments()

        # ✅ 이벤트 다시 연결 (새로 그릴 때마다 scatter가 바뀌므로)
        self.canvas.mpl_connect('pick_event', self.on_pick)

        try:
            self.toolbar.update()
        except Exception:
            pass
        self.canvas.draw_idle()

    def plot_after(self):
        idx = self.pi_index_var.get()
        try:
            self.collection.remove_pi_at_index(idx)
        except Exception as e:
            messagebox.showerror("오류", str(e))
            return
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title(f"After: PI({idx}) 제거 후 선형")
        self._draw_segments()
        # ✅ 동일하게 이벤트 재연결
        self.canvas.mpl_connect('pick_event', self.on_pick)

        self.json_export()
        try:
            self.toolbar.update()
        except Exception:
            pass
        self.canvas.draw_idle()

    def reset_to_initial(self):

        self.collection = copy.deepcopy(self.original_collection)
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self._draw_segments()
        try:
            self.toolbar.update()
        except Exception:
            pass
        self.canvas.draw_idle()
        self.json_export()
        messagebox.showinfo("초기화 완료", "SegmentCollection이 초기 상태로 복원되었습니다.")

    # --- 내부 도식 ---
    def _draw_segments(self):
        colors = {"StraightSegment": "blue", "CurveSegment": "orange", "CUBICSegment": "green"}
        for seg in self.collection.segment_list:
            name = seg.__class__.__name__
            c = colors.get(name, "gray")
            pts = self._segment_to_xy(seg)
            if pts:
                x, y = zip(*pts)
                self.ax.plot(x, y, color=c, lw=2)

        # --- PI 점 표시 (picker=True) ---
        pi_x = [pt.x for pt in self.collection.coord_list]
        pi_y = [pt.y for pt in self.collection.coord_list]
        self.pi_scatter = self.ax.scatter(pi_x, pi_y, color='red', marker='x', s=60, zorder=6, picker=5)
        self.ax.plot(pi_x, pi_y, color='red', linestyle='--', lw=1, zorder=4)
        self.ax.axis("equal")
        self.ax.grid(True, lw=0.3, alpha=0.5)

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

    # --- Drag 이벤트 ---
    def on_pick(self, event):
        if event.artist != self.pi_scatter:
            return
        self.dragging_index = event.ind[0]  # 선택된 PI 인덱스

    def on_drag(self, event):
        if self.dragging_index is None:
            return
        if event.xdata is None or event.ydata is None:
            return

        idx = self.dragging_index
        new_point = Point2d(event.xdata, event.ydata)
        radius = self.collection.radius_list[idx-1]
        try:
            with Transaction(self.collection):
                self.collection.update_pi_and_radius_by_index(new_point, radius, idx)
        except AlignmentError as e:
            messagebox.showerror('업데이트 실패', str(e))
            return  # 롤백 후 종료
        else:
            self.plot_before()  # 실시간 갱신
            self.json_export()

    def on_release(self, event):
        self.dragging_index = None

if __name__ == "__main__":

    al = Alignment(name='test')
    coord_list = [Point2d(0,0), Point2d(100,0), Point2d(150,50), Point2d(200,50)]
    radius_list = [50, 30]
    try:
        al.create(coord_list, radius_list)
    except AlignmentError as e:
        messagebox.showerror('에러', f'{e}')
    app = SegmentVisualizer(al)
    app.mainloop()