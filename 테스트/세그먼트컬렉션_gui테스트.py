import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import copy
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk, FigureCanvasTkAgg
from pyproj import Transformer
import contextily as ctx
import json

from curvedirection import CurveDirection
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

    def __init__(self):
        super().__init__()
        self.title("SegmentCollection 시각화 테스트")
        self.geometry("1200x1000")
        self.collection = None

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

        # ✅ 지도 갱신 버튼 추가
        ttk.Button(control, text="지도 갱신", command=self.update_map_zoom).pack(side=tk.LEFT, padx=10)

        # ✅저장 버튼 추가
        ttk.Button(control, text="저장", command=self.save_to_json).pack(side=tk.LEFT, padx=10)

        # ✅로드 버튼 추가
        ttk.Button(control, text="로드", command=self.load_from_json).pack(side=tk.LEFT, padx=10)

        # 상태
        self.dragging_index = None
        self._overlay_artists = []

        # 이벤트 등록
        self.canvas.mpl_connect('pick_event', self.on_pick)
        self.canvas.mpl_connect('motion_notify_event', self.on_drag)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('button_press_event', self.add_pi)

        self.path = 'c:/temp/data.json'

        #객체관리

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
            self.save_bve()
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
            self.save_bve()
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
        self.save_bve()
    def reset_to_initial(self):
        """화면 초기화: 현재 그려진 모든 객체 제거"""
        # collection은 그대로 두고 화면만 초기화
        for artist in list(self.ax.lines) + list(self.ax.texts) + list(self.ax.collections) + list(self.ax.images):
            artist.remove()

        self._overlay_artists.clear()  # 오버레이도 초기화
        self.ax.set_aspect('equal', adjustable='datalim')
        self.ax.grid(False)
        self.canvas.draw_idle()

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
            self.save_bve()
        except Exception as e:
            messagebox.showerror("PI 추가 오류", str(e))

    # ────────────────────────────────
    # Plot / 지도 관련
    # ────────────────────────────────

    def update_plot(self, title="SegmentCollection",
                    force_xlim=None, force_ylim=None, zoom=None):
        """전체 다시 그림 — 외부에서 force_xlim/ylim/zoom 전달 가능"""
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title(title)

        if self.view_map_mode.get():
            # 전달된 force_* 를 _draw_map_basemap 에서 사용하게 함
            self._draw_map_basemap(zoom=zoom,
                                   force_xlim=force_xlim,
                                   force_ylim=force_ylim)

        self._draw_segments()
        self.canvas.draw_idle()

    def _draw_map_basemap(self, zoom=None, force_xlim=None, force_ylim=None):
        """지도 배경 추가 — force_xlim/ylim 이 주어지면 그걸 우선 사용"""
        if not self.collection.coord_list:
            return

        xs, ys = zip(*[transformer_to_3857.transform(pt.x, pt.y)
                       for pt in self.collection.coord_list])

        # default extent (데이터 기반)
        margin_x = (max(xs) - min(xs)) * 0.15 or 500
        margin_y = (max(ys) - min(ys)) * 0.15 or 500
        default_xlim = (min(xs) - margin_x, max(xs) + margin_x)
        default_ylim = (min(ys) - margin_y, max(ys) + margin_y)

        # force 가 있으면 우선 사용, 없으면 기본 extent 사용
        if force_xlim is not None and force_ylim is not None:
            self.ax.set_xlim(force_xlim)
            self.ax.set_ylim(force_ylim)
        else:
            # 최초 표시나 강제 재계산 시 기본 영역 적용
            self.ax.set_xlim(default_xlim)
            self.ax.set_ylim(default_ylim)

        self.ax.set_aspect('equal', adjustable='datalim')

        # === zoom 결정: 호출자가 줌 전달하면 사용, 아니면 데이터 기반 계산 ===
        import numpy as np
        if zoom is None:
            dx = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]
            dy = self.ax.get_ylim()[1] - self.ax.get_ylim()[0]
            max_dim = max(dx, dy)
            zoom = int(18 - np.log2(max_dim / 500))
            zoom = int(np.clip(zoom, 5, 18))
        else:
            zoom = int(np.clip(zoom, 5, 18))

        try:
            ctx.add_basemap(
                self.ax,
                crs="EPSG:3857",
                source=ctx.providers.OpenStreetMap.Mapnik,
                zoom=zoom
            )
        except Exception as e:
            print(f"[지도 로드 실패]: {e}, zoom={zoom}")

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

    def update_map_zoom(self):
        """현재 뷰 범위 기반으로 지도 타일만 다시 로드"""
        if not self.view_map_mode.get():
            messagebox.showinfo("안내", "지도 보기 모드를 먼저 켜세요.")
            return

        try:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            dx = xlim[1] - xlim[0]
            dy = ylim[1] - ylim[0]
            max_dim = max(dx, dy)

            import numpy as np
            zoom = int(18 - np.log2(max_dim / 500))
            zoom = int(np.clip(zoom, 5, 18))

            # 현재 지도 타일만 다시 추가 (Axes는 그대로 유지)
            # 기존 타일 제거
            for im in list(self.ax.images):
                im.remove()

            # 새 타일 불러오기
            ctx.add_basemap(
                self.ax,
                crs="EPSG:3857",
                source=ctx.providers.OpenStreetMap.Mapnik,
                zoom=zoom
            )

            # 기존 확대/이동 상태 그대로 복원
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)
            self.canvas.draw_idle()

            print(f"[지도 갱신 완료] zoom={zoom}")

        except Exception as e:
            messagebox.showerror("지도 갱신 실패", str(e))

    #----- 출력 ------
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
            self.save_bve()
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
            self.save_bve()
        self.dragging_index = None

    def save_to_json(self):
        """현재 SegmentCollection을 JSON으로 저장"""
        data = []
        for idx, (pt, r) in enumerate(zip(self.collection.coord_list, self.collection.radius_list)):
            data.append({
                "pi_index": idx,
                "pi_coord": [pt.x, pt.y],
                "radius": r
            })
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("저장 완료", f"JSON 저장 완료: {self.path}")

    def load_from_json(self):
        """JSON으로부터 SegmentCollection 불러오기"""
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            coord_list = []
            radius_list = []

            for item in data:
                x, y = item["pi_coord"]
                coord_list.append(Point2d(x, y))
                radius_list.append(item.get("radius"))

            al = Alignment(name="loaded")
            al.create(coord_list, radius_list)
            self.collection = al.collection
            self.update_plot(al.name)
            self.json_export()
            self.save_bve()
            messagebox.showinfo("로드 완료", f"{al.name} SegmentCollection 로드 완료")

        except Exception as e:
            messagebox.showerror("로드 실패", str(e))

    def create_base_txt(self):
        base_txt = ''
        base_txt += 'Options.ObjectVisibility 1\n'
        base_txt += 'With Route\n'
        base_txt += '.comment 세그먼트컬렉션 테스트루트\n'
        base_txt += '.Elevation 0\n'
        base_txt += 'With Train\n'
        base_txt += 'With Structure\n'
        base_txt += '$Include(오브젝트.txt)\n'
        base_txt += '$Include(프리오브젝트.txt)\n'
        base_txt += '$Include(km_index.txt)\n'
        base_txt += '$Include(curve_index.txt)\n'
        base_txt += '$Include(pitch_index.txt)\n'
        base_txt += 'With Track\n'
        base_txt += '$Include(전주.txt)\n'
        base_txt += '$Include(전차선.txt)\n'
        base_txt += '$Include(km_post.txt)\n'
        base_txt += '$Include(curve_post.txt)\n'
        base_txt += '$Include(pitch_post.txt)\n'
        base_txt += '$Include(신호.txt)\n'
        base_txt += '$Include(통신.txt)\n'
        base_txt += '0,.back 0;,.ground 0;,.dike 0;0;2;,.railtype 0;9;\n'
        base_txt += '0,.sta START STATION;\n'
        base_txt += '100,.stop 0;\n'
        return base_txt

    def extract_horizon(self):
        """BVE 수평선형(.bve) 텍스트 추출"""
        csv_txt = []
        for seg in self.collection.segment_list:
            if isinstance(seg, CurveSegment):
                if seg.direction == CurveDirection.LEFT:
                    text = f'{seg.start_sta:.2f},.CURVE -{seg.radius};\n'
                    text2 = f'{seg.end_sta:.2f},.CURVE 0;\n'
                else:
                    text = f'{seg.start_sta:.2f},.CURVE {seg.radius};\n'
                    text2 = f'{seg.end_sta:.2f},.CURVE 0;\n'

                csv_txt.append(text)
                csv_txt.append(text2)

        return csv_txt

    def save_bve(self):
        lines = []
        #lines.append(self.create_base_txt())
        lines.extend(self.extract_horizon())
        txt = '\n'.join(lines)
        with open("c:/temp/평면선형.txt", "w", encoding="utf-8") as f:
            f.write(txt)


# ================= 실행 =================
if __name__ == "__main__":
    app = SegmentVisualizer()
    app.mainloop()
