"""
터널 단면 작도기 (Tunnel Section Designer)
=========================================
기능:
    - 파라미터 기반 터널 단면 실시간 작도
    - FL 자동 맞춤 (brentq 기반)
    - 자동 맞춤 이력 (Treeview, CSV 저장, 더블클릭 복원)
    - DXF 입출력 (캐싱)
    - 현대적 ttk UI (Scale + Entry 양방향 동기화)

구조:
    TunnelParams     : 입력 파라미터 (dataclass)
    TunnelGeometry   : 계산 결과 (dataclass)
    FitHistory       : 자동 맞춤 이력
    DxfCache         : DXF 엔티티 캐시
    compute_geometry : 순수 계산 함수 (테스트 가능)
    compute_fl       : FL 계산 (자동 맞춤용)
    fit_R1_Y_to_FL   : brentq 기반 최적화
    ParamRow         : 슬라이더 + 엔트리 결합 위젯
    TunnelApp        : tkinter 애플리케이션
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass, asdict, replace
from datetime import datetime
from typing import Optional

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Arc, Circle
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import ezdxf
from shapely.geometry import LineString, Polygon
from scipy.optimize import brentq, minimize_scalar

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


# =============================================================================
# 상수
# =============================================================================
FL_TOLERANCE = 0.02
ARC_SAMPLES = 1000
POLYGON_ARC_POINTS = 100
LABEL_Y_MARGIN = 0.5
DXF_DEFAULT_IN = "c:/temp/건축한계.dxf"


# =============================================================================
# 데이터 모델
# =============================================================================
@dataclass
class TunnelParams:
    R1: float = 7.166
    top_angle: float = 90.0
    R2: float = 5.54
    r2_angle: float = 69.0
    R1_Y: float = 1.572
    D: float = 4.4

    # 고정값
    FL: float = 0.0
    RL: float = 0.472
    fl_to_culvert: float = 0.472
    sideL: float = 0.8
    sideR: float = 0.8
    safeheight: float = 2.1

    @property
    def r1_angles(self) -> tuple[float, float]:
        half = self.top_angle / 2.0
        return (90.0 + half, 90.0 - half)


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


@dataclass
class FitHistoryEntry:
    timestamp: str
    target_FL: float
    achieved_FL: float
    R1_Y: float
    dR1_Y: float
    R1: float
    top_angle: float
    R2: float
    r2_angle: float
    D: float
    success: bool

    @property
    def is_ok(self) -> bool:
        return (not math.isnan(self.achieved_FL)
                and abs(self.achieved_FL - self.target_FL) <= FL_TOLERANCE)


# =============================================================================
# 기하 유틸
# =============================================================================
def _polar(center, radius, deg):
    rad = math.radians(deg)
    return (center[0] + radius * math.cos(rad),
            center[1] + radius * math.sin(rad))


def find_side_center(top_center, top_radius, ang_left, ang_right, side_radius):
    left_pt = _polar(top_center, top_radius, ang_left)
    right_pt = _polar(top_center, top_radius, ang_right)

    def unit(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy)
        return dx / n, dy / n

    dx_l, dy_l = unit(top_center, left_pt)
    dx_r, dy_r = unit(top_center, right_pt)

    left_center = (left_pt[0] - dx_l * side_radius, left_pt[1] - dy_l * side_radius)
    right_center = (right_pt[0] - dx_r * side_radius, right_pt[1] - dy_r * side_radius)
    return left_center, right_center


def find_end_point(center, radius, start_point, angle_deg):
    sa = math.degrees(math.atan2(start_point[1] - center[1], start_point[0] - center[0]))
    return _polar(center, radius, sa + angle_deg)


def find_start_point(center, radius, end_point, angle_deg):
    ea = math.degrees(math.atan2(end_point[1] - center[1], end_point[0] - center[0]))
    return _polar(center, radius, ea - angle_deg)


def arc_to_linestring(center, radius, start_deg, end_deg,
                      num_points=POLYGON_ARC_POINTS):
    angs = np.linspace(math.radians(start_deg), math.radians(end_deg), num_points)
    return LineString([(center[0] + radius * math.cos(a),
                        center[1] + radius * math.sin(a)) for a in angs])


def find_extreme_x_on_arc(center, radius, start_deg, end_deg):
    if end_deg < start_deg:
        end_deg += 360.0
    angs = np.radians(np.linspace(start_deg, end_deg, ARC_SAMPLES))
    xs = center[0] + radius * np.cos(angs)
    ys = center[1] + radius * np.sin(angs)
    return (xs.max(), ys[xs.argmax()]), (xs.min(), ys[xs.argmin()])


# =============================================================================
# 계산
# =============================================================================
def compute_geometry(p: TunnelParams) -> TunnelGeometry:
    center_top = (0.0, p.R1_Y)
    a_left, a_right = p.r1_angles

    left_center, right_center = find_side_center(
        center_top, p.R1, a_left, a_right, p.R2)

    top_start = _polar(center_top, p.R1, a_left)
    top_end = _polar(center_top, p.R1, a_right)
    left_end = find_end_point(left_center, p.R2, top_start, p.r2_angle)
    right_end = find_end_point(right_center, p.R2, top_end, -p.r2_angle)

    left_arc = arc_to_linestring(left_center, p.R2, a_left, a_left + p.r2_angle)
    top_arc = arc_to_linestring(center_top, p.R1, a_left, a_right)
    right_arc = arc_to_linestring(right_center, p.R2, a_right, a_right - p.r2_angle)
    bottom = LineString([left_arc.coords[-1], right_arc.coords[-1]])

    coords = (list(left_arc.coords[::-1]) + list(top_arc.coords)
              + list(right_arc.coords) + list(bottom.coords[::-1]))
    polygon = Polygon(coords)

    _, sl_pt = find_extreme_x_on_arc(left_center, p.R2, a_left, a_left + p.r2_angle)

    return TunnelGeometry(
        p=p, center_top=center_top,
        left_center=left_center, right_center=right_center,
        top_start=top_start, top_end=top_end,
        left_end=left_end, right_end=right_end,
        polygon=polygon, area=polygon.area,
        SL=sl_pt[1], A=abs(left_end[0]),
        top_of_tunnel=p.R1_Y + p.R1 - p.FL,
    )


def compute_fl(p: TunnelParams, R1_Y: float) -> float:
    a_left, a_right = p.r1_angles
    center_top = (0.0, R1_Y)
    left_center, _ = find_side_center(center_top, p.R1, a_left, a_right, p.R2)
    top_start = _polar(center_top, p.R1, a_left)
    left_end = find_end_point(left_center, p.R2, top_start, p.r2_angle)
    return left_end[1] - p.fl_to_culvert


def fit_R1_Y_to_FL(p: TunnelParams,
                   tol: float = 1e-4,
                   bounds: tuple[float, float] = (-20.0, 20.0)
                   ) -> tuple[float, bool]:
    target = p.FL

    def f(y):
        return compute_fl(p, y) - target

    lo, hi = bounds
    if f(lo) > 0 or f(hi) < 0:
        return p.R1_Y, False
    try:
        return float(brentq(f, lo, hi, xtol=tol, maxiter=100)), True
    except (ValueError, RuntimeError):
        res = minimize_scalar(lambda y: abs(f(y)), bounds=(lo, hi), method='bounded')
        return float(res.x), bool(res.success)


# =============================================================================
# 이력 / DXF 캐시
# =============================================================================
class FitHistory:
    def __init__(self, max_size: int = 100):
        self.entries: list[FitHistoryEntry] = []
        self.max_size = max_size

    def add(self, p: TunnelParams, R1_Y_prev: float,
            achieved_FL: float, success: bool) -> FitHistoryEntry:
        e = FitHistoryEntry(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            target_FL=p.FL, achieved_FL=achieved_FL,
            R1_Y=p.R1_Y, dR1_Y=p.R1_Y - R1_Y_prev,
            R1=p.R1, top_angle=p.top_angle,
            R2=p.R2, r2_angle=p.r2_angle, D=p.D,
            success=success,
        )
        self.entries.append(e)
        if len(self.entries) > self.max_size:
            self.entries.pop(0)
        return e

    def to_csv(self, path: str):
        if not self.entries:
            raise ValueError("저장할 이력이 없습니다.")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(asdict(self.entries[0]).keys()))
            w.writeheader()
            for e in self.entries:
                w.writerow(asdict(e))


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


# =============================================================================
# 스타일
# =============================================================================
def setup_style(root: tk.Tk):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        style.theme_use("default")

    base = ("Malgun Gothic", 10)
    bold = ("Malgun Gothic", 10, "bold")
    title = ("Malgun Gothic", 12, "bold")
    root.option_add("*Font", base)

    style.configure("TFrame", background="#f5f6f8")
    style.configure("Card.TFrame", background="#ffffff")
    style.configure("TLabel", background="#f5f6f8", font=base)
    style.configure("Card.TLabel", background="#ffffff", font=base)
    style.configure("Unit.TLabel", background="#ffffff",
                    foreground="#888888", font=("Malgun Gothic", 9))
    style.configure("Title.TLabel", background="#f5f6f8",
                    font=title, foreground="#1a1a1a")
    style.configure("Info.TLabel", background="#f5f6f8",
                    foreground="#555555", font=("Malgun Gothic", 9))
    style.configure("Spec.TLabel", background="#eaf1ff", font=bold,
                    foreground="#1a3a70", padding=6)
    style.configure("TLabelframe", background="#f5f6f8",
                    bordercolor="#d0d4da", relief="solid")
    style.configure("TLabelframe.Label", background="#f5f6f8",
                    font=bold, foreground="#333333")
    style.configure("TScale", background="#ffffff", troughcolor="#e0e4ea")
    style.configure("TEntry", fieldbackground="#ffffff", padding=4)
    style.configure("TButton", padding=(10, 6), font=base)
    style.configure("Accent.TButton", font=bold, foreground="white",
                    background="#2f6fed")
    style.map("Accent.TButton",
              background=[("active", "#1e5ad6"), ("disabled", "#a9bce8")])
    style.configure("Danger.TButton", foreground="#b00020")
    style.configure("Treeview", rowheight=26, font=base)
    style.configure("Treeview.Heading", font=bold)
    style.configure("TNotebook", background="#f5f6f8", borderwidth=0)
    style.configure("TNotebook.Tab", padding=(14, 8), font=base)
    style.map("TNotebook.Tab",
              background=[("selected", "#ffffff"), ("!selected", "#e6e9ee")])


# =============================================================================
# 파라미터 위젯 (Scale + Entry)
# =============================================================================
class ParamRow:
    def __init__(self, parent, *, label, attr, lo, hi, res, unit,
                 decimals, on_change, initial):
        self.attr = attr
        self.on_change = on_change
        self.res = res
        self.decimals = decimals
        self.lo = lo
        self.hi = hi

        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text=label, style="Card.TLabel",
                  width=13).grid(row=0, column=0, sticky="w", padx=(6, 8))

        self.var = tk.DoubleVar(value=initial)
        self.scale = ttk.Scale(frame, from_=lo, to=hi, orient="horizontal",
                               variable=self.var, command=self._on_scale)
        self.scale.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        self.entry_var = tk.StringVar(value=f"{initial:.{decimals}f}")
        entry = ttk.Entry(frame, textvariable=self.entry_var,
                          width=9, justify="right")
        entry.grid(row=0, column=2, sticky="e")
        entry.bind("<Return>", self._on_entry)
        entry.bind("<FocusOut>", self._on_entry)

        ttk.Label(frame, text=unit, style="Unit.TLabel",
                  width=3).grid(row=0, column=3, sticky="w", padx=(4, 6))

        self.frame = frame

    def _on_scale(self, _val):
        v = round(self.var.get() / self.res) * self.res
        self.entry_var.set(f"{v:.{self.decimals}f}")
        self.on_change(self.attr, v)

    def _on_entry(self, _evt=None):
        try:
            v = float(self.entry_var.get())
        except ValueError:
            self.entry_var.set(f"{self.var.get():.{self.decimals}f}")
            return
        v = max(self.lo, min(self.hi, v))
        self.var.set(v)
        self.entry_var.set(f"{v:.{self.decimals}f}")
        self.on_change(self.attr, v)

    def set_value(self, v: float):
        self.var.set(v)
        self.entry_var.set(f"{v:.{self.decimals}f}")


# =============================================================================
# 메인 애플리케이션
# =============================================================================
class TunnelApp:
    def __init__(self):
        self.params = TunnelParams()
        self.dxf = DxfCache()
        self.dxf_path = DXF_DEFAULT_IN
        self.history = FitHistory()
        self.rows: dict[str, ParamRow] = {}
        self._suspend = False

        self.root = tk.Tk()
        self.root.title("터널 단면 작도기")
        self.root.geometry("1320x840")
        self.root.minsize(1120, 720)
        setup_style(self.root)

        paned = ttk.PanedWindow(self.root, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=8, pady=8)
        left = ttk.Frame(paned, padding=(4, 4))
        right = ttk.Frame(paned, padding=(4, 4))
        paned.add(left, weight=0)
        paned.add(right, weight=1)

        self._build_controls(left)
        self._build_canvas(right)

        self.update_plot()
        self.root.bind("<Control-s>", lambda e: self.save_dxf())
        self.root.bind("<Control-o>", lambda e: self.open_dxf())
        self.root.bind("<Control-f>", lambda e: self.auto_fit_fl())

    # ---------------------------------------------------------------
    def _build_controls(self, parent):
        header = ttk.Frame(parent)
        header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text="터널 단면 제원",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="슬라이더 또는 값을 직접 입력하세요.",
                  style="Info.TLabel").pack(anchor="w")

        # 단면 형상
        g1 = ttk.LabelFrame(parent, text="  단면 형상  ", padding=8)
        g1.pack(fill="x", pady=(0, 8))
        g1.columnconfigure(0, weight=1)
        shape_specs = [
            ("R1",         "R1",        1.0,  20.0, 0.01, "m", 3),
            ("상단 각도",   "top_angle",  0.0, 180.0, 0.5,  "°", 1),
            ("R2",         "R2",        1.0,  20.0, 0.01, "m", 3),
            ("R2 각도",    "r2_angle",   0.0, 180.0, 0.5,  "°", 1),
        ]
        for i, (label, attr, lo, hi, res, unit, dec) in enumerate(shape_specs):
            row = ParamRow(g1, label=label, attr=attr, lo=lo, hi=hi,
                           res=res, unit=unit, decimals=dec,
                           on_change=self._on_param_change,
                           initial=getattr(self.params, attr))
            row.frame.grid(row=i, column=0, sticky="ew", pady=2)
            self.rows[attr] = row

        # 위치/치수
        g2 = ttk.LabelFrame(parent, text="  위치 · 치수  ", padding=8)
        g2.pack(fill="x", pady=(0, 8))
        g2.columnconfigure(0, weight=1)
        pos_specs = [
            ("선로 중심간격", "D",    0.0,  30.0, 0.01, "m", 2),
            ("R1 중심 Y",    "R1_Y", -10.0, 10.0, 0.01, "m", 3),
            ("목표 FL",      "FL",   -5.0,  5.0,  0.01, "m", 3),
        ]
        for i, (label, attr, lo, hi, res, unit, dec) in enumerate(pos_specs):
            row = ParamRow(g2, label=label, attr=attr, lo=lo, hi=hi,
                           res=res, unit=unit, decimals=dec,
                           on_change=self._on_param_change,
                           initial=getattr(self.params, attr))
            row.frame.grid(row=i, column=0, sticky="ew", pady=2)
            self.rows[attr] = row

        # 실시간 스펙 패널
        self.spec_label = ttk.Label(parent, text="", style="Spec.TLabel",
                                    anchor="w", justify="left")
        self.spec_label.pack(fill="x", pady=(0, 8))

        # 액션
        act = ttk.Frame(parent)
        act.pack(fill="x", pady=(0, 6))
        act.columnconfigure((0, 1), weight=1)

        ttk.Button(act, text="⚡  FL 자동 맞춤  (Ctrl+F)",
                   style="Accent.TButton",
                   command=self.auto_fit_fl
                   ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        ttk.Button(act, text="도면 저장  (Ctrl+S)",
                   command=self.save_dxf
                   ).grid(row=1, column=0, sticky="ew", padx=(0, 3))
        ttk.Button(act, text="DXF 열기  (Ctrl+O)",
                   command=self.open_dxf
                   ).grid(row=1, column=1, sticky="ew", padx=(3, 0))

        ttk.Button(act, text="초기값 복원",
                   command=self.reset_params
                   ).grid(row=2, column=0, sticky="ew", padx=(0, 3), pady=(6, 0))
        ttk.Button(act, text="종료", style="Danger.TButton",
                   command=self.close
                   ).grid(row=2, column=1, sticky="ew", padx=(3, 0), pady=(6, 0))

    # ---------------------------------------------------------------
    def _build_canvas(self, parent):
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True)

        tab_plot = ttk.Frame(nb)
        nb.add(tab_plot, text="  도면  ")

        self.fig, self.ax = plt.subplots(figsize=(7, 6), dpi=100)
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.grid(True, color="#e5e5e5", linewidth=0.6)

        self.canvas = FigureCanvasTkAgg(self.fig, master=tab_plot)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        tb = ttk.Frame(tab_plot)
        tb.pack(fill="x")
        self.toolbar = NavigationToolbar2Tk(self.canvas, tb, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side="left")

        tab_hist = ttk.Frame(nb)
        nb.add(tab_hist, text="  자동 맞춤 이력  ")
        self._build_history_tab(tab_hist)

    # ---------------------------------------------------------------
    def _build_history_tab(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(fill="x", padx=8, pady=6)
        ttk.Button(bar, text="CSV 저장",
                   command=self.save_history_csv).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="초기화",
                   command=self.clear_history).pack(side="left", padx=(0, 6))
        ttk.Label(bar, text="더블클릭으로 파라미터 복원",
                  style="Info.TLabel").pack(side="left", padx=(12, 0))
        self.hist_count = ttk.Label(bar, text="0건")
        self.hist_count.pack(side="right")

        cols = ("timestamp", "target_FL", "achieved_FL", "R1_Y", "dR1_Y",
                "R1", "top_angle", "R2", "r2_angle", "D", "status")
        heads = {
            "timestamp": "시각", "target_FL": "목표 FL", "achieved_FL": "달성 FL",
            "R1_Y": "R1_Y", "dR1_Y": "ΔR1_Y",
            "R1": "R1", "top_angle": "상단°", "R2": "R2",
            "r2_angle": "R2°", "D": "D", "status": "상태",
        }
        widths = {"timestamp": 140, "status": 50}
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.hist_tree = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            self.hist_tree.heading(c, text=heads[c])
            self.hist_tree.column(c, width=widths.get(c, 70), anchor="center")
        self.hist_tree.bind("<Double-1>", self._on_history_dblclick)
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.hist_tree.yview)
        self.hist_tree.configure(yscroll=sb.set)
        self.hist_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    # ---------------------------------------------------------------
    # 파라미터 변경 / 반영
    # ---------------------------------------------------------------
    def _on_param_change(self, attr: str, value: float):
        if self._suspend:
            return
        setattr(self.params, attr, value)
        self.update_plot()

    def _apply_params(self, **kwargs):
        self._suspend = True
        try:
            for k, v in kwargs.items():
                setattr(self.params, k, v)
                if k in self.rows:
                    self.rows[k].set_value(v)
        finally:
            self._suspend = False
        self.update_plot()

    def reset_params(self):
        if not messagebox.askyesno("초기값 복원",
                                   "모든 파라미터를 초기값으로 되돌릴까요?"):
            return
        d = TunnelParams()
        self._apply_params(R1=d.R1, top_angle=d.top_angle,
                           R2=d.R2, r2_angle=d.r2_angle,
                           D=d.D, R1_Y=d.R1_Y, FL=d.FL)

    # ---------------------------------------------------------------
    # 자동 맞춤
    # ---------------------------------------------------------------
    def auto_fit_fl(self):
        p = self.params
        target = simpledialog.askfloat(
            "FL 자동 맞춤",
            f"목표 FL 값을 입력하세요 (현재 {p.FL:.3f}):",
            initialvalue=p.FL)
        if target is None:
            return

        p_target = replace(p, FL=target)
        r1_y_prev = p.R1_Y
        r1_y_opt, ok = fit_R1_Y_to_FL(p_target)

        if not ok:
            self.history.add(p_target, r1_y_prev, float("nan"), success=False)
            self._refresh_history_view()
            messagebox.showwarning(
                "자동 맞춤 실패",
                f"FL={target}을 만족하는 R1_Y를 찾을 수 없습니다.\n"
                f"R1/R2/각도 조합을 확인하세요.")
            return

        self.params.FL = target
        self.params.R1_Y = r1_y_opt
        self._suspend = True
        try:
            self.rows["FL"].set_value(target)
            self.rows["R1_Y"].set_value(r1_y_opt)
        finally:
            self._suspend = False
        self.update_plot()

        achieved = compute_fl(self.params, r1_y_opt)
        entry = self.history.add(self.params, r1_y_prev, achieved, success=True)
        self._refresh_history_view()

        messagebox.showinfo(
            "자동 맞춤 완료",
            f"R1_Y  = {r1_y_opt:.4f}  (Δ {entry.dR1_Y:+.4f})\n"
            f"FL     = {achieved:.4f}  (목표 {target})\n"
            f"이력 {len(self.history.entries)}건")

    # ---------------------------------------------------------------
    # 이력
    # ---------------------------------------------------------------
    def _refresh_history_view(self):
        for i in self.hist_tree.get_children():
            self.hist_tree.delete(i)
        for e in self.history.entries:
            status = "✅" if e.is_ok else ("⚠️" if e.success else "❌")
            self.hist_tree.insert("", "end", values=(
                e.timestamp,
                f"{e.target_FL:.4f}",
                f"{e.achieved_FL:.4f}" if e.success else "-",
                f"{e.R1_Y:.4f}", f"{e.dR1_Y:+.4f}",
                f"{e.R1:.2f}", f"{e.top_angle:.1f}",
                f"{e.R2:.2f}", f"{e.r2_angle:.1f}", f"{e.D:.2f}",
                status))
        self.hist_count.config(text=f"{len(self.history.entries)}건")

    def _on_history_dblclick(self, _evt):
        sel = self.hist_tree.selection()
        if not sel:
            return
        idx = self.hist_tree.index(sel[0])
        e = self.history.entries[idx]
        if not messagebox.askyesno(
                "이력 복원",
                f"{e.timestamp} 값으로 파라미터를 복원할까요?"):
            return
        self._apply_params(R1=e.R1, top_angle=e.top_angle, R2=e.R2,
                           r2_angle=e.r2_angle, D=e.D,
                           R1_Y=e.R1_Y, FL=e.target_FL)

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
        except Exception as ex:
            messagebox.showerror("저장 실패", str(ex))

    def clear_history(self):
        if not self.history.entries:
            return
        if messagebox.askyesno("이력 초기화",
                               f"{len(self.history.entries)}건을 삭제할까요?"):
            self.history.entries.clear()
            self._refresh_history_view()

    # ---------------------------------------------------------------
    # 렌더링
    # ---------------------------------------------------------------
    def update_plot(self):
        p = self.params
        geom = compute_geometry(p)
        ax = self.ax
        ax.clear()
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, color="#e5e5e5", linewidth=0.6)

        self._draw_cad(translate_x=-p.D / 2, translate_y=+p.RL)
        self._draw_cad(translate_x=+p.D / 2, translate_y=+p.RL)
        self._draw_tunnel(geom)
        self._draw_haunch_bottom(geom)
        self._draw_centerlines(p, geom)
        self._draw_dimension_lines(geom)
        self._draw_angles(geom)
        self._draw_safe_box(geom)
        self._draw_sl_line(geom)
        self._update_spec_panel(geom)

        self.canvas.draw_idle()

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

        def arc(c, r, s, e, color):
            if e < s:
                e += 360.0
            ax.add_patch(Arc(c, 2 * r, 2 * r, angle=0,
                             theta1=s, theta2=e, color=color, lw=1.8))

        arc(g.center_top, p.R1, a_right, a_left, '#d64545')
        arc(g.left_center, p.R2, a_left, a_left + p.r2_angle, '#2f6fed')
        arc(g.right_center, p.R2, a_right - p.r2_angle, a_right, '#2b8a3e')

    def _draw_haunch_bottom(self, g: TunnelGeometry):
        p, ax = g.p, self.ax
        for end, side, sign in ((g.left_end, p.sideL, +1),
                                (g.right_end, p.sideR, -1)):
            x = [end[0], end[0] + sign * side,
                 end[0] + sign * side, 0]
            y = [end[1], end[1],
                 end[1] - p.fl_to_culvert, end[1] - p.fl_to_culvert]
            ax.plot(x, y, 'k-', lw=1.2)

    def _draw_centerlines(self, p: TunnelParams, g: TunnelGeometry):
        ax = self.ax
        y_text = g.top_of_tunnel + LABEL_Y_MARGIN
        for x, label in ((-p.D / 2, 'CL of 하선'),
                         (0, 'CL of 터널'),
                         (p.D / 2, 'CL of 상선')):
            ax.axvline(x, color='gray', linestyle='--', linewidth=0.9)
            ax.text(x, y_text, label, ha='center', fontsize=9, color='#555555')

    def _draw_dimension_lines(self, g: TunnelGeometry):
        p, ax = g.p, self.ax
        for c, e in ((g.center_top, g.top_end),
                     (g.center_top, g.top_start),
                     (g.left_center, g.left_end),
                     (g.right_center, g.right_end)):
            ax.plot([c[0], e[0]], [c[1], e[1]],
                    linestyle='--', color='#888888', lw=0.8)

        a_left, a_right = p.r1_angles
        for c, e, ang in ((g.center_top, g.top_end, a_right),
                          (g.center_top, g.top_start, a_left)):
            m = ((c[0] + e[0]) / 2, (c[1] + e[1]) / 2)
            ax.text(m[0] - 0.25, m[1] + 0.25, f'R1={p.R1 * 1000:.0f}',
                    rotation=ang, fontsize=9)
        for c, e in ((g.left_center, g.left_end),
                     (g.right_center, g.right_end)):
            m = ((c[0] + e[0]) / 2, (c[1] + e[1]) / 2)
            rot = math.degrees(math.atan2(e[1] - c[1], e[0] - c[0]))
            ax.text(m[0], m[1], f'R2={p.R2 * 1000:.0f}',
                    rotation=rot, fontsize=9)

    def _draw_angles(self, g: TunnelGeometry):
        self._draw_angle_annotation(g.top_start, g.center_top, g.top_end)
        self._draw_angle_annotation(g.left_end, g.left_center, g.top_start)
        self._draw_angle_annotation(g.top_end, g.right_center, g.right_end)

    def _draw_angle_annotation(self, p1, p2, p3, radius=1.0):
        v1 = np.array(p1) - np.array(p2)
        v2 = np.array(p3) - np.array(p2)
        cos = np.clip(v1 @ v2 / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1, 1)
        angle_deg = math.degrees(math.acos(cos))
        a1 = math.degrees(math.atan2(v1[1], v1[0]))
        a2 = math.degrees(math.atan2(v2[1], v2[0]))
        if a2 < a1:
            a2 += 360.0
        self.ax.add_patch(Arc(p2, 2 * radius, 2 * radius, angle=0,
                              theta1=a1, theta2=a2, color='#333333'))
        mid = math.radians((a1 + a2) / 2.0)
        self.ax.text(p2[0] + radius * 0.7 * math.cos(mid),
                     p2[1] + radius * 0.7 * math.sin(mid),
                     f'{angle_deg:.1f}°', fontsize=11, ha='center',
                     color='#333333')

    def _draw_safe_box(self, g: TunnelGeometry):
        p, ax = g.p, self.ax
        h = p.safeheight
        for end, side, sign in ((g.left_end, p.sideL, +1),
                                (g.right_end, p.sideR, -1)):
            x0, y0 = end
            x1 = x0 + sign * side
            ax.plot([x0, x0, x1, x1], [y0, y0 + h, y0 + h, y0],
                    color='#9aa0a6', linestyle='--', lw=0.9)
            ax.plot([x0, x1], [y0 + h, y0],
                    color='#9aa0a6', linestyle='--', lw=0.9)
            ax.plot([x1, x0], [y0 + h, y0],
                    color='#9aa0a6', linestyle='--', lw=0.9)

    def _draw_sl_line(self, g: TunnelGeometry):
        ax = self.ax
        ax.axhline(g.SL, color='#9aa0a6', linestyle='--', linewidth=0.9)
        ax.text(g.left_end[0] - 0.6, g.SL, 'SL',
                fontsize=9, color='#555555', va='center')

    def _update_spec_panel(self, g: TunnelGeometry):
        p = g.p
        new_fl = compute_fl(p, p.R1_Y)
        ok = abs(new_fl - p.FL) <= FL_TOLERANCE
        mark = "✅" if ok else "⚠️"
        self.spec_label.config(text=(
            f"면적 {g.area:.2f}㎡   |   A {g.A:.2f}m   |   "
            f"SL {g.SL:.2f}m   |   편평률 {g.top_of_tunnel / (g.A * 2):.2f}\n"
            f"R2/R1 {p.R2 / p.R1:.2f}   |   "
            f"FL {new_fl:.3f}m (목표 {p.FL:.3f}m)   {mark}"))

    # ---------------------------------------------------------------
    # DXF 입출력
    # ---------------------------------------------------------------
    def open_dxf(self):
        path = filedialog.askopenfilename(
            title="DXF 파일 선택",
            filetypes=[("DXF", "*.dxf"), ("All files", "*.*")])
        if not path:
            return
        self.dxf_path = path
        if self.dxf.load(path, force=True) is not None:
            self.update_plot()

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
                msp.add_line(start=(xs[i], ys[i]),
                             end=(xs[i + 1], ys[i + 1]))
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

    # ---------------------------------------------------------------
    def close(self):
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# =============================================================================
if __name__ == "__main__":
    TunnelApp().run()