import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import copy
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk, FigureCanvasTkAgg

from data.alignment.alignment import Alignment
from data.alignment.exception.alignment_error import AlignmentError, AlreadyHasCurveError
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
        ttk.Label(control, text="대상 PI 인덱스:").pack(side=tk.LEFT, padx=5)
        self.pi_index_var = tk.IntVar(value=1)
        ttk.Entry(control, textvariable=self.pi_index_var, width=5).pack(side=tk.LEFT)

        ttk.Button(control, text="PI 삭제", command=self.remove_pi).pack(side=tk.LEFT, padx=5)
        ttk.Button(control, text="초기상태로 되돌리기", command=self.reset_to_initial).pack(side=tk.LEFT, padx=5)

        # ✅ ADD_PI 모드 버튼 추가
        self.add_pi_mode = False
        self.add_pi_button = ttk.Button(control, text="PI 추가 모드: OFF", command=self.toggle_add_pi_mode)
        self.add_pi_button.pack(side=tk.LEFT, padx=10)

        # ✅ 커브만 삭제 모드 체크박스
        self.remove_curve_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control, text="곡선만 삭제", variable=self.remove_curve_var).pack(side=tk.LEFT, padx=10)

        #곡선 추가 대화상자
        self.add_curve_button = ttk.Button(control, text="곡선 추가", command=self.add_curve_ui)
        self.add_curve_button.pack(side=tk.LEFT, padx=10)

        # --- drag 관련 상태 ---
        self.dragging_index = None

        # --- 이벤트 연결 ---
        self.canvas.mpl_connect('pick_event', self.on_pick)
        self.canvas.mpl_connect('motion_notify_event', self.on_drag)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        # ✅ 마우스 클릭으로 PI 추가
        self.canvas.mpl_connect('button_press_event', self.add_pi)

        # 초기 그림 표시
        self.update_plot()

    # ✅ ADD_PI 모드 토글
    def toggle_add_pi_mode(self):
        self.add_pi_mode = not self.add_pi_mode
        if self.add_pi_mode:
            self.add_pi_button.config(text="PI 추가 모드: ON", style="Accent.TButton")
            messagebox.showinfo("PI 추가 모드", "화면을 클릭하면 해당 위치에 PI가 추가됩니다.")
        else:
            self.add_pi_button.config(text="PI 추가 모드: OFF")
            messagebox.showinfo("PI 추가 모드 종료", "PI 추가 모드가 비활성화되었습니다.")

    def add_curve_ui(self):
        """PI 클릭 후 반경 입력받아 곡선 추가"""
        try:
            idx = self.pi_index_var.get()

            # --- 반경 입력 대화상자 ---
            radius_str = simpledialog.askstring("곡선 추가", "곡선 반경 (R)을 입력하세요:", parent=self)
            if not radius_str:
                return  # 사용자가 취소 누름
            try:
                radius = float(radius_str)
                if radius <= 0:
                    raise ValueError("반경은 양수여야 합니다.")
            except ValueError:
                messagebox.showerror("입력 오류", "유효한 숫자를 입력하세요.")
                return

            # --- 곡선 추가 로직 ---
            self.collection.add_curve_at_simple_curve(idx, radius)

            # --- 시각화 갱신 ---
            self.update_plot()
            self.json_export()
            messagebox.showinfo("완료", f"PI {idx}에 반경 {radius:.2f}m 곡선을 추가했습니다.")

        except AlignmentError as e:
            messagebox.showerror("에러", f"{e}")
        except Exception as e:
            messagebox.showerror("예외 발생", f"처리 중 오류: {e}")

    # ✅ 클릭 시 ADD_PI 실행
    def add_pi(self, event):
        if not self.add_pi_mode:
            return  # 모드가 꺼져 있으면 무시
        if event.xdata is None or event.ydata is None:
            return

        coord = Point2d(event.xdata, event.ydata)
        try:
            idx = self.collection.add_pi_by_coord(coord)
            self.update_plot()
            self.json_export()
            messagebox.showinfo("PI 추가 완료", f"새로운 PI가 인덱스 {idx} 위치에 추가되었습니다.")
        except Exception as e:
            messagebox.showerror("PI 추가 오류", str(e))

        # 한 번 추가 후 모드 자동 종료 (원하면 유지도 가능)
        self.toggle_add_pi_mode()

    def remove_pi(self):
        idx = self.pi_index_var.get()
        try:
            if self.remove_curve_var.get():
                print(f"PI {idx} 의 커브만 제거")
                self.collection.remove_curve_at_pi_by_index(idx)
            else:
                self.collection.remove_pi_at_index(idx)
        except Exception as e:
            messagebox.showerror("오류", str(e))
            return
        self.update_plot(f"After: PI({idx}) 제거 후 선형")
        self.json_export()

    def update_plot(self, title="SegmentCollection"):
        """SegmentCollection 전체를 다시 그림"""
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title(title)

        # --- 세그먼트 다시 그림 ---
        self._draw_segments()

        # --- 이벤트 재등록 (scatter 다시 생성되므로) ---
        self.canvas.mpl_disconnect(getattr(self, "_pick_cid", None) or 0)
        self._pick_cid = self.canvas.mpl_connect('pick_event', self.on_pick)

        # --- UI 갱신 ---
        try:
            self.toolbar.update()
        except Exception:
            pass
        self.canvas.draw_idle()


    def reset_to_initial(self):

        self.collection = copy.deepcopy(self.original_collection)
        self.update_plot('초기화 선형')

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
        try:
            with Transaction(self.collection):
                self.collection.update_pi_by_index(new_point, idx)
        except AlignmentError as e:
            messagebox.showerror('업데이트 실패', str(e))
            return  # 롤백 후 종료
        else:
            self.update_plot()  # 실시간 갱신
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