"""
터널 단면 작도 프로그램 (리팩토링 버전)

구조:
    - TunnelParams   : 모든 입력 파라미터 (dataclass)
    - TunnelGeometry : 계산된 기하 결과 (dataclass)
    - compute_geometry() : 순수 계산 (테스트 가능)
    - draw_*         : 렌더링 함수 (ax만 받음)
    - TunnelApp      : tkinter UI
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Optional

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Arc, Circle
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import ezdxf
from shapely.geometry import LineString, Polygon
from scipy.optimize import minimize

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
FL_TOLERANCE = 0.02          # FL 검토 허용오차
ARC_SAMPLES = 1000           # 아크 샘플링 개수
POLYGON_ARC_POINTS = 100     # 폴리곤 근사용 아크 점 개수
LABEL_Y_MARGIN = 0.5         # CL 라벨 상단 여유
DXF_DEFAULT_IN = "c:/temp/건축한계.dxf"
DXF_DEFAULT_OUT = "C:/TEMP/TUNNEL_output.dxf"


# ---------------------------------------------------------------------------
# 파라미터 / 기하 결과
# ---------------------------------------------------------------------------
@dataclass
class TunnelParams:
    R1: float = 7.166
    top_angle: float = 90.0
    R2: float = 5.54
    r2_angle: float = 69.0
    R1_Y: float = 1.572
    D: float = 4.4

    # 고정값 (초기에는 상수였던 항목들)
    FL: float = 0.0
    RL: float = 0.472              # FL + rail offset
    fl_to_culvert: float = 0.472   # 공동구 상단 ~ FL
    sideL: float = 0.8
    sideR: float = 0.8
    safeheight: float = 2.1

    @property
    def r1_angles(self) -> tuple[float, float]:
        half = self.top_angle / 2.0
        return (90.0 + half, 90.0 - half)   # (좌, 우)


@dataclass
class TunnelGeometry:
    p: TunnelParams
    center_top: tuple[float, float]
    left_center: tuple[float, float]
    right_center: tuple[float, float]
    top_start: tuple[float, float]
    top_end: tuple[float, float]
    left_end: tuple[float, float]
    right_end: tuple[float, float]
    polygon: Polygon
    area: float
    SL: float
    A: float
    top_of_tunnel: float

from dataclasses import dataclass, field, asdict
from datetime import datetime
import csv

@dataclass
class FitHistoryEntry:
    timestamp: str
    target_FL: float
    achieved_FL: float
    R1_Y: float
    dR1_Y: float           # 이전 R1_Y 대비 변화량
    R1: float
    top_angle: float
    R2: float
    r2_angle: float
    D: float
    success: bool

    @property
    def is_ok(self) -> bool:
        return abs(self.achieved_FL - self.target_FL) <= FL_TOLERANCE

class FitHistory:
    def __init__(self, max_size: int = 100):
        self.entries: list[FitHistoryEntry] = []
        self.max_size = max_size

    def add(self, p: TunnelParams, R1_Y_prev: float,
            achieved_FL: float, success: bool) -> FitHistoryEntry:
        entry = FitHistoryEntry(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            target_FL=p.FL,
            achieved_FL=achieved_FL,
            R1_Y=p.R1_Y,
            dR1_Y=p.R1_Y - R1_Y_prev,
            R1=p.R1, top_angle=p.top_angle,
            R2=p.R2, r2_angle=p.r2_angle,
            D=p.D,
            success=success,
        )
        self.entries.append(entry)
        if len(self.entries) > self.max_size:
            self.entries.pop(0)
        return entry

    def to_csv(self, path: str):
        if not self.entries:
            raise ValueError("저장할 이력이 없습니다.")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(asdict(self.entries[0]).keys()))
            w.writeheader()
            for e in self.entries:
                w.writerow(asdict(e))

# ---------------------------------------------------------------------------
# 기하 유틸
# ---------------------------------------------------------------------------
def _polar(center, radius, deg):
    rad = math.radians(deg)
    return (center[0] + radius * math.cos(rad),
            center[1] + radius * math.sin(rad))


def find_side_center(top_center, top_radius, ang_left, ang_right, side_radius):
    """상단 아크의 좌/우 끝점에서 접선 방향으로 side_radius만큼 이동한 원 중심."""
    left_pt = _polar(top_center, top_radius, ang_left)
    right_pt = _polar(top_center, top_radius, ang_right)

    def unit(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy)
        return dx / n, dy / n

    dx_l, dy_l = unit(top_center, left_pt)
    dx_r, dy_r = unit(top_center, right_pt)

    left_center = (left_pt[0] - dx_l * side_radius,
                   left_pt[1] - dy_l * side_radius)
    right_center = (right_pt[0] - dx_r * side_radius,
                    right_pt[1] - dy_r * side_radius)
    return left_center, right_center


def find_end_point(center, radius, start_point, angle_deg):
    start_ang = math.degrees(math.atan2(start_point[1] - center[1],
                                        start_point[0] - center[0]))
    return _polar(center, radius, start_ang + angle_deg)


def find_start_point(center, radius, end_point, angle_deg):
    end_ang = math.degrees(math.atan2(end_point[1] - center[1],
                                      end_point[0] - center[0]))
    return _polar(center, radius, end_ang - angle_deg)


def arc_to_linestring(center, radius, start_deg, end_deg,
                      num_points=POLYGON_ARC_POINTS):
    angs = np.linspace(math.radians(start_deg), math.radians(end_deg), num_points)
    pts = [(center[0] + radius * math.cos(a),
            center[1] + radius * math.sin(a)) for a in angs]
    return LineString(pts)


def find_extreme_x_on_arc(center, radius, start_deg, end_deg):
    """start→end(반시계 기준) 아크 위 x최대/최소 점. end<start여도 안전."""
    if end_deg < start_deg:
        end_deg += 360.0
    angs = np.radians(np.linspace(start_deg, end_deg, ARC_SAMPLES))
    xs = center[0] + radius * np.cos(angs)
    ys = center[1] + radius * np.sin(angs)
    return (xs.max(), ys[xs.argmax()]), (xs.min(), ys[xs.argmin()])


# ---------------------------------------------------------------------------
# 계산 (순수 함수)
# ---------------------------------------------------------------------------
def compute_geometry(p: TunnelParams) -> TunnelGeometry:
    center_top = (0.0, p.R1_Y)
    a_left, a_right = p.r1_angles

    left_center, right_center = find_side_center(
        center_top, p.R1, a_left, a_right, p.R2)

    top_start = _polar(center_top, p.R1, a_left)
    top_end = _polar(center_top, p.R1, a_right)

    left_end = find_end_point(left_center, p.R2, top_start, p.r2_angle)
    right_end = find_end_point(right_center, p.R2, top_end, -p.r2_angle)

    # 폴리곤
    left_arc = arc_to_linestring(left_center, p.R2, a_left, a_left + p.r2_angle)
    top_arc = arc_to_linestring(center_top, p.R1, a_left, a_right)
    right_arc = arc_to_linestring(right_center, p.R2, a_right, a_right - p.r2_angle)
    bottom = LineString([left_arc.coords[-1], right_arc.coords[-1]])

    coords = (list(left_arc.coords[::-1]) + list(top_arc.coords)
              + list(right_arc.coords) + list(bottom.coords[::-1]))
    polygon = Polygon(coords)

    _, sl_point = find_extreme_x_on_arc(left_center, p.R2, a_left, a_left + p.r2_angle)

    return TunnelGeometry(
        p=p,
        center_top=center_top,
        left_center=left_center,
        right_center=right_center,
        top_start=top_start,
        top_end=top_end,
        left_end=left_end,
        right_end=right_end,
        polygon=polygon,
        area=polygon.area,
        SL=sl_point[1],
        A=abs(left_end[0] - 0.0),          # 원점 기준 좌측 반폭
        top_of_tunnel=p.R1_Y + p.R1 - p.FL,
    )


# ---------------------------------------------------------------------------
# 렌더링 헬퍼
# ---------------------------------------------------------------------------
def draw_arc(ax, center, radius, start_deg, end_deg, color='b'):
    """start → end (반시계) 아크. end < start면 +360."""
    if end_deg < start_deg:
        end_deg += 360.0
    ax.add_patch(Arc(center, 2 * radius, 2 * radius,
                     angle=0, theta1=start_deg, theta2=end_deg, color=color))


def draw_line(ax, start, end, linestyle='--', color='gray', lw=1):
    ax.plot([start[0], end[0]], [start[1], end[1]],
            linestyle=linestyle, color=color, linewidth=lw)


def draw_angle_annotation(ax, p1, p2, p3, radius=1.0, color='black'):
    """p2를 중심으로 p1-p2-p3 사이 각도 호 및 라벨."""
    v1 = np.array(p1) - np.array(p2)
    v2 = np.array(p3) - np.array(p2)
    cos = np.clip(v1 @ v2 / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1, 1)
    angle_deg = math.degrees(math.acos(cos))

    a1 = math.degrees(math.atan2(v1[1], v1[0]))
    a2 = math.degrees(math.atan2(v2[1], v2[0]))

    # 반시계 방향으로 두 각 사이를 정렬
    if a2 < a1:
        a2 += 360.0
    ax.add_patch(Arc(p2, 2 * radius, 2 * radius, angle=0,
                     theta1=a1, theta2=a2, color=color))

    mid = math.radians((a1 + a2) / 2.0)
    ax.text(p2[0] + radius * 0.7 * math.cos(mid),
            p2[1] + radius * 0.7 * math.sin(mid),
            f'{angle_deg:.1f}°', color=color, fontsize=12, ha='center')


def _mid(p1, p2):
    return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)


def _bearing(p1, p2):
    return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))

def compute_fl(p: TunnelParams, R1_Y: float) -> float:
    """주어진 R1_Y에 대해 좌측 하단 수평부(FL)의 Y좌표를 계산."""
    a_left, a_right = p.r1_angles
    center_top = (0.0, R1_Y)

    left_center, _ = find_side_center(
        center_top, p.R1, a_left, a_right, p.R2)
    top_start = _polar(center_top, p.R1, a_left)
    left_end = find_end_point(left_center, p.R2, top_start, p.r2_angle)

    return left_end[1] - p.fl_to_culvert

from scipy.optimize import minimize_scalar, brentq

def fit_R1_Y_to_FL(p: TunnelParams,
                   tol: float = 1e-4,
                   bounds: tuple[float, float] = (-20.0, 20.0)
                   ) -> tuple[float, bool]:
    """
    FL 조건을 만족하는 R1_Y를 찾는다.

    Returns:
        (R1_Y_opt, success)
    """
    target = p.FL

    def f(R1_Y):
        return compute_fl(p, R1_Y) - target

    lo, hi = bounds
    f_lo, f_hi = f(lo), f(hi)

    # 해가 범위 안에 있는지 확인 (단조 증가 가정)
    if f_lo > 0 or f_hi < 0:
        return p.R1_Y, False

    try:
        r1_y = brentq(f, lo, hi, xtol=tol, maxiter=100)
        return r1_y, True
    except (ValueError, RuntimeError):
        # fallback: |f| 최소화
        res = minimize_scalar(lambda y: abs(f(y)),
                              bounds=(lo, hi), method='bounded')
        return float(res.x), res.success
# ---------------------------------------------------------------------------
# DXF 캐시
# ---------------------------------------------------------------------------
class DxfCache:
    def __init__(self):
        self.path: Optional[str] = None
        self.entities: Optional[list] = None

    def load(self, path: str, force: bool = False):
        if not force and path == self.path and self.entities is not None:
            return self.entities
        try:
            doc = ezdxf.readfile(path)
        except (FileNotFoundError, IOError) as e:
            messagebox.showwarning("DXF 로드 실패", f"{path}\n{e}")
            self.path, self.entities = None, None
            return None
        self.path = path
        self.entities = list(doc.modelspace())
        return self.entities


# ---------------------------------------------------------------------------
# 메인 애플리케이션
# ---------------------------------------------------------------------------
class TunnelApp:
    def __init__(self):
        self.params = TunnelParams()
        self.dxf = DxfCache()
        self.dxf_path = DXF_DEFAULT_IN
        self.history = FitHistory()

        self._build_ui()
        self.update_plot()

    # ----- UI 구성 ----------------------------------------------------------
    def _build_ui(self):
        self.root = tk.Tk()
        self.root.title("터널 단면 작도")
        self.root.geometry("220x780")

        self.plot_win = tk.Toplevel(self.root)
        self.plot_win.title("터널 단면")
        self.plot_win.geometry("900x780")

        self.fig, self.ax = plt.subplots()
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.grid(True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_win)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        tb_frame = tk.Frame(self.plot_win)
        tb_frame.pack(side=tk.BOTTOM, fill=tk.X)
        NavigationToolbar2Tk(self.canvas, tb_frame).update()

        # 슬라이더 (라벨, 속성명, from, to, resolution)
        self.scales: dict[str, tk.Scale] = {}
        specs = [
            ("R1",           "R1",           1.0, 20.0, 0.1),
            ("TOP_ANGLE",    "top_angle",    0.0, 180.0, 1.0),
            ("R2",           "R2",           1.0, 20.0, 0.1),
            ("R2_ANGLE",     "r2_angle",     0.0, 180.0, 1.0),
            ("선로중심간격",  "D",            0.0, 30.0, 0.1),
            ("R1_Y",         "R1_Y",        -10.0, 10.0, 0.01),
        ]
        for label, attr, lo, hi, res in specs:
            s = tk.Scale(self.root, label=label, from_=lo, to=hi,
                         resolution=res, orient=tk.HORIZONTAL)
            s.set(getattr(self.params, attr))
            s.pack(fill=tk.X, padx=5, pady=3)
            s.config(command=lambda _v, a=attr: self._on_slider(a))
            self.scales[attr] = s

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="FL 자동 맞춤",
                  command=self.auto_fit_fl,
                  bg="#d0e8ff").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="도면 저장", command=self.save_dxf).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="DXF 열기", command=self.open_dxf).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="종료", command=self.close).pack(side=tk.LEFT, padx=5)

        btn_frame2 = tk.Frame(self.root)
        btn_frame2.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame2, text="이력 보기",
                  command=self.show_history).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame2, text="이력 CSV 저장",
                  command=self.save_history_csv).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame2, text="이력 초기화",
                  command=self.clear_history).pack(side=tk.LEFT, padx=3)

    # ----- 이벤트 -----------------------------------------------------------
    def _on_slider(self, attr: str):
        setattr(self.params, attr, self.scales[attr].get())
        self.update_plot()

    def open_dxf(self):
        path = filedialog.askopenfilename(
            title="DXF 파일 선택",
            filetypes=[("DXF", "*.dxf"), ("All files", "*.*")])
        if not path:
            return
        self.dxf_path = path
        if self.dxf.load(path, force=True) is not None:
            self.update_plot()

    # ----- 그리기 -----------------------------------------------------------
    def update_plot(self):
        p = self.params
        geom = compute_geometry(p)
        ax = self.ax
        ax.clear()
        ax.set_aspect('equal', adjustable='box')
        ax.grid(True)

        self._draw_cad(translate_x=-p.D / 2, translate_y=+p.RL)
        self._draw_cad(translate_x=+p.D / 2, translate_y=+p.RL)

        self._draw_tunnel(geom)
        self._draw_haunch_bottom(geom)
        self._draw_centerlines(p, geom)
        self._draw_dimension_lines(geom)
        self._draw_angles(geom)
        self._draw_safe_box(geom)
        self._draw_sl_line(geom)
        self._draw_history_overlay(geom)  # ← 추가
        self._print_spec(geom)

        self.canvas.draw()

    # ----- 세부 그리기 ------------------------------------------------------
    def _draw_cad(self, translate_x, translate_y):
        ents = self.dxf.load(self.dxf_path)
        if not ents:
            return
        ax = self.ax
        for e in ents:
            t = e.dxftype()
            if t == 'LINE':
                s, en = e.dxf.start, e.dxf.end
                ax.plot([s.x + translate_x, en.x + translate_x],
                        [s.y + translate_y, en.y + translate_y], 'k-', lw=0.8)
            elif t == 'CIRCLE':
                c, r = e.dxf.center, e.dxf.radius
                ax.add_patch(Circle((c.x + translate_x, c.y + translate_y),
                                    r, color='r', fill=False))
            elif t == 'ARC':
                c, r = e.dxf.center, e.dxf.radius
                ax.add_patch(Arc((c.x + translate_x, c.y + translate_y),
                                 2 * r, 2 * r, angle=0,
                                 theta1=e.dxf.start_angle,
                                 theta2=e.dxf.end_angle, color='g'))

    def _draw_tunnel(self, g: TunnelGeometry):
        p, ax = g.p, self.ax
        a_left, a_right = p.r1_angles
        draw_arc(ax, g.center_top, p.R1, a_right, a_left, color='r')
        draw_arc(ax, g.left_center, p.R2, a_left, a_left + p.r2_angle, color='b')
        draw_arc(ax, g.right_center, p.R2, a_right - p.r2_angle, a_right, color='g')

    def _draw_haunch_bottom(self, g: TunnelGeometry):
        """좌/우 하단 수직+수평 라인."""
        p, ax = g.p, self.ax
        for end, side, sign in ((g.left_end, p.sideL, +1),
                                (g.right_end, p.sideR, -1)):
            x = [end[0], end[0] + sign * side, end[0] + sign * side, 0]
            y = [end[1], end[1], end[1] - p.fl_to_culvert, end[1] - p.fl_to_culvert]
            ax.plot(x, y, 'k-', lw=1)

    def _draw_centerlines(self, p: TunnelParams, g: TunnelGeometry):
        ax = self.ax
        y_text = g.top_of_tunnel + LABEL_Y_MARGIN
        for x, label in ((-p.D / 2, 'CL of 하선'), (0, 'CL of 터널'), (p.D / 2, 'CL of 상선')):
            ax.axvline(x, color='gray', linestyle='--', linewidth=1)
            ax.text(x, y_text, label, ha='center')

    def _draw_dimension_lines(self, g: TunnelGeometry):
        p, ax = g.p, self.ax
        for center, end in ((g.center_top, g.top_end), (g.center_top, g.top_start)):
            draw_line(ax, center, end, linestyle='-', color='gray')
        draw_line(ax, g.left_center, g.left_end, linestyle='-', color='gray')
        draw_line(ax, g.right_center, g.right_end, linestyle='-', color='gray')

        a_left, a_right = p.r1_angles
        for center, end, ang in ((g.center_top, g.top_end, a_right),
                                 (g.center_top, g.top_start, a_left)):
            m = _mid(center, end)
            ax.text(m[0] - 0.25, m[1] + 0.25, f'R1 = {p.R1 * 1000:.0f}',
                    rotation=ang, fontsize=9)

        for center, end in ((g.left_center, g.left_end),
                            (g.right_center, g.right_end)):
            m = _mid(center, end)
            ax.text(m[0], m[1], f'R2 = {p.R2 * 1000:.0f}',
                    rotation=_bearing(center, end), fontsize=9)

    def _draw_angles(self, g: TunnelGeometry):
        draw_angle_annotation(self.ax, g.top_start, g.center_top, g.top_end)
        draw_angle_annotation(self.ax, g.left_end, g.left_center, g.top_start)
        draw_angle_annotation(self.ax, g.top_end, g.right_center, g.right_end)

    def _draw_safe_box(self, g: TunnelGeometry):
        """좌/우 안전박스(X표시) — 좌표 오타 수정 버전."""
        p, ax = g.p, self.ax
        h = p.safeheight
        for end, side, sign in ((g.left_end, p.sideL, +1),
                                (g.right_end, p.sideR, -1)):
            x0, y0 = end
            x1 = x0 + sign * side
            # 외곽 박스
            ax.plot([x0, x0, x1, x1], [y0, y0 + h, y0 + h, y0],
                    color='gray', linestyle='--', lw=0.8)
            # X 표시
            ax.plot([x0, x1], [y0 + h, y0], color='gray', linestyle='--', lw=0.8)
            ax.plot([x1, x0], [y0 + h, y0], color='gray', linestyle='--', lw=0.8)

    def _draw_sl_line(self, g: TunnelGeometry):
        ax = self.ax
        ax.axhline(y=g.SL, color='gray', linestyle='--', linewidth=1)
        ax.text(g.left_end[0] - 0.5, g.SL, 'SL', fontsize=9)

    # ----- 콘솔 스펙 --------------------------------------------------------
    def _print_spec(self, g: TunnelGeometry):
        p = g.p
        new_FL = compute_fl(p, p.R1_Y)

        print('------------------ 터널 제원 출력 ----------------')
        print(f'내공단면적 {g.area:.2f} m²')
        print(f'R1 : {p.R1:.2f}')
        print(f'Top Angle : {p.top_angle}')
        print(f'R2 : {p.R2}')
        print(f'R2 Angle : {p.r2_angle}')
        print(f'A : {g.A:.2f}')
        print(f'SL : {g.SL:.2f}')
        print(f'R2/R1 비 : {p.R2 / p.R1:.2f}')
        print(f'편평률 : {g.top_of_tunnel / (g.A * 2):.2f}')
        print(f'현재 FL : {new_FL:.4f}  (목표 {p.FL})')
        if abs(new_FL - p.FL) <= FL_TOLERANCE:
            print('검토결과 : OK  ✅')
        elif new_FL > p.FL:
            print('검토결과 : FL을 내려야 함 (→ R1_Y 감소)')
        else:
            print('검토결과 : FL을 올려야 함 (→ R1_Y 증가)')
        print(f'자동 맞춤 이력: {len(self.history.entries)}건')
        if self.history.entries:
            last = self.history.entries[-1]
            print(f'  최근: {last.timestamp}  ΔR1_Y={last.dR1_Y:+.4f}')
        print('------------------------------------------------')

    # ----- DXF 저장 ---------------------------------------------------------
    def save_dxf(self):
        path = filedialog.asksaveasfilename(
            title="DXF 저장", defaultextension=".dxf",
            initialfile="TUNNEL_output.dxf",
            filetypes=[("DXF", "*.dxf")])
        if not path:
            return
        try:
            self._write_dxf(path)
            messagebox.showinfo("저장 완료", path)
        except Exception as e:
            messagebox.showerror("저장 실패", str(e))

    def _write_dxf(self, path: str):
        doc = ezdxf.new()
        msp = doc.modelspace()

        for line in self.ax.lines:
            xs, ys = line.get_data()
            for i in range(len(xs) - 1):
                msp.add_line(start=(xs[i], ys[i]), end=(xs[i + 1], ys[i + 1]))

        for patch in self.ax.patches:
            if isinstance(patch, Circle):
                msp.add_circle(center=patch.center, radius=patch.radius)
            elif isinstance(patch, Arc):
                r = patch.width / 2
                s, e = patch.theta1 % 360, patch.theta2 % 360
                if e <= s:
                    e += 360
                msp.add_arc(center=patch.center, radius=r,
                            start_angle=s, end_angle=e)

        doc.saveas(path)

    # ----- 종료 ------------------------------------------------------------
    def close(self):
        self.root.destroy()

    def run(self):
        self.root.mainloop()

    def auto_fit_fl(self):
        p = self.params
        target = simpledialog.askfloat(
            "FL 자동 맞춤",
            f"목표 FL 값을 입력하세요 (현재 {p.FL}):",
            initialvalue=p.FL,
        )
        if target is None:
            return

        p_target = replace(p, FL=target)
        r1_y_prev = p.R1_Y
        r1_y_opt, ok = fit_R1_Y_to_FL(p_target)

        if not ok:
            self.history.add(p_target, r1_y_prev, achieved_FL=float('nan'), success=False)
            messagebox.showwarning(
                "자동 맞춤 실패",
                f"FL={target}을 만족하는 R1_Y를 찾을 수 없습니다.")
            return

        p.FL = target
        p.R1_Y = r1_y_opt
        self.scales["R1_Y"].set(r1_y_opt)
        self.update_plot()

        achieved = compute_fl(p, r1_y_opt)
        entry = self.history.add(p, r1_y_prev, achieved, success=True)

        messagebox.showinfo(
            "자동 맞춤 완료",
            f"R1_Y = {r1_y_opt:.4f}  (Δ {entry.dR1_Y:+.4f})\n"
            f"FL    = {achieved:.4f}  (목표 {target})\n"
            f"이력 {len(self.history.entries)}건 저장됨")

    def show_history(self):
        if not self.history.entries:
            messagebox.showinfo("이력", "저장된 이력이 없습니다.")
            return

        win = tk.Toplevel(self.root)
        win.title(f"자동 맞춤 이력 ({len(self.history.entries)}건)")
        win.geometry("900x400")

        cols = ("timestamp", "target_FL", "achieved_FL", "R1_Y", "dR1_Y",
                "R1", "top_angle", "R2", "r2_angle", "D", "status")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=15)
        headers = {
            "timestamp": "시각", "target_FL": "목표 FL", "achieved_FL": "달성 FL",
            "R1_Y": "R1_Y", "dR1_Y": "ΔR1_Y",
            "R1": "R1", "top_angle": "Top°",
            "R2": "R2", "r2_angle": "R2°", "D": "D",
            "status": "상태",
        }
        widths = {"timestamp": 140, "status": 60}
        for c in cols:
            tree.heading(c, text=headers[c])
            tree.column(c, width=widths.get(c, 70), anchor="center")

        for e in self.history.entries:
            status = "✅" if e.is_ok else ("⚠️" if e.success else "❌")
            tree.insert("", "end", values=(
                e.timestamp,
                f"{e.target_FL:.4f}",
                f"{e.achieved_FL:.4f}" if e.success else "-",
                f"{e.R1_Y:.4f}", f"{e.dR1_Y:+.4f}",
                f"{e.R1:.2f}", f"{e.top_angle:.0f}",
                f"{e.R2:.2f}", f"{e.r2_angle:.0f}", f"{e.D:.1f}",
                status,
            ))


        sb = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
        tree.configure(yscroll=sb.set)
        tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        sb.pack(side="right", fill="y", pady=5)

    def save_history_csv(self):
        if not self.history.entries:
            messagebox.showinfo("이력", "저장할 이력이 없습니다.")
            return
        path = filedialog.asksaveasfilename(
            title="이력 CSV 저장", defaultextension=".csv",
            initialfile=f"fit_history_{datetime.now():%Y%m%d_%H%M%S}.csv",
            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            self.history.to_csv(path)
            messagebox.showinfo("저장 완료", path)
        except Exception as e:
            messagebox.showerror("저장 실패", str(e))

    def clear_history(self):
        if not self.history.entries:
            return
        if messagebox.askyesno("이력 초기화",
                               f"{len(self.history.entries)}건을 삭제할까요?"):
            self.history.entries.clear()

    def _draw_history_overlay(self, g: TunnelGeometry):
        if not self.history.entries:
            return
        ax = self.ax
        recent = self.history.entries[-3:]
        x0, y0 = g.right_end[0] + 1.5, g.top_of_tunnel
        lines = ["최근 자동 맞춤:"]
        for e in recent:
            mark = "✅" if e.is_ok else ("⚠️" if e.success else "❌")
            lines.append(f"{mark} FL={e.target_FL:.3f} → R1_Y={e.R1_Y:.3f}")
        ax.text(x0, y0, "\n".join(lines), fontsize=8, va="top",
                bbox=dict(boxstyle="round", facecolor="white",
                          edgecolor="gray", alpha=0.85))
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    TunnelApp().run()