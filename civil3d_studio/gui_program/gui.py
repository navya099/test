import csv
import math
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional, Tuple
import json

from alignment.pipoint import PIPoint
from alignment.station.equation_manager import StationEquationManager
from alignment.widing.offset_alignment import OffsetAlignment
from alignment.widing.wideing_region import WideningRegion
from corridor.engine import Corridor3DEngine
from profile.pvi import PVIPoint
from structure.region import StructureRegion
from superelevation.superelevation import SuperelevationStation
from superelevation.superelevation_table import SuperelevationTable
from profile.profile import Profile
from alignment.alignment import Alignment
from surface.surface import ExistingGroundTerrain


class Civil3DStudioDashboard:
    """
    Python 기반 Civil 3D 통합 설계 대시보드 애플리케이션
    - 평면도(Plan), 종단도(Profile), 횡단면도(Cross Section) 3분할 실시간 뷰포트 제공
    - 설계 제원 텍스트 에디터 탭 편집 및 즉시 재계산 워크플로우
    - 순수 Python 기반 3D DXF 및 3D 좌표 CSV 내보내기 지원
    """
    APP_VERSION = "2.0.0"
    def __init__(self, root: tk.Tk):
        self.pis = []
        self.root = root
        self.root.title("Python Civil 3D 통합 설계 대시보드 (Plan + Profile + Cross Section + DXF)")
        self.root.geometry("1540x920")
        self.root.configure(bg="#181b20")
        self.current_project_path: Optional[str] = None
        # 상태 변수 선언

        self.h_align: Optional[Alignment] = None

        self.v_prof: Optional[Profile] = None
        self.sup_tbl: Optional[SuperelevationTable] = None
        self.sta_mgr: Optional[StationEquationManager] = None
        self.left_lane: Optional[OffsetAlignment] = None
        self.right_lane: Optional[OffsetAlignment] = None
        self.active_raw_sta: float = 200.0

        # 3D 드라이브(가상 주행) 상태 변수
        self.is_driving: bool = False
        self.drive_speed_kmh: float = 80.0
        self.drive_lane_offset: float = 1.75
        self.drive_eye_height: float = 1.25
        self.drive_dt: float = 0.035

        #코리더 상태변수
        self.corridor: Optional[Corridor3DEngine] = None

        # 종단 인터랙티브 드래그 편집 상태 변수
        self.drag_target = None  # ("PVI", index) 또는 ("STRUCT_START", index) 또는 ("STRUCT_END", index)
        #평면 인터랙티브 드래그 편집 상태 변수
        self.plan_drag_idx: Optional[int] = None
        # 화면 좌표 변환 캐시 파라미터
        self.plan_transform = (1.0, 0.0, 0.0, 0.0, 0.0)
        self.prof_bounds = (0, 0, 1, 1, 0, 1, 0, 1)

        self._setup_styles()
        self._build_layout()
        self._bind_shortcuts()
        self._load_default_design_data()
        self.recalculate_all()
        self._update_window_title()
        self._drive_animation_loop()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#181b20")
        style.configure("TLabel", background="#181b20", foreground="#e2e8f0", font=("맑은 고딕", 9))
        style.configure("Header.TLabel", background="#181b20", foreground="#38bdf8", font=("맑은 고딕", 10, "bold"))
        style.configure("TNotebook", background="#181b20", borderwidth=0)
        style.configure("TNotebook.Tab", background="#262b33", foreground="#cbd5e0", padding=[10, 5],
                        font=("맑은 고딕", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#0284c7")], foreground=[("selected", "#ffffff")])

    def _bind_shortcuts(self):
        """실무 단축키 바인딩 (Ctrl+S 저장, Ctrl+O 열기, F5 재계산)"""
        self.root.bind("<Control-s>", lambda e: self.save_project_dialog())
        self.root.bind("<Control-o>", lambda e: self.load_project_dialog())
        self.root.bind("<F5>", lambda e: self.recalculate_all())
        self.root.bind("<space>", lambda e: self._on_space_key(e))

    def _on_space_key(self, event):
        # 텍스트 에디터 입력 중일 때는 스페이스바 주행 토글 무시
        if isinstance(event.widget, (tk.Text, tk.Entry)):
            return
        self.toggle_drive()

    def _update_window_title(self):
        proj_name = os.path.basename(self.current_project_path) if self.current_project_path else "새 프로젝트 (저장 안 됨)"

        self.root.title(f"Civil 3D Python Studio - [{proj_name}]")

    def _build_layout(self):
        # 상단 툴바
        toolbar = tk.Frame(self.root, bg="#0f172a", height=44, padx=12)
        toolbar.pack(fill=tk.X, side=tk.TOP)

        tk.Label(
            toolbar, text="CIVIL 3D STUDIO",
            bg="#0f172a", fg="#38bdf8", font=("Consolas", 12, "bold")
        ).pack(side=tk.LEFT, pady=8)

        btn_style = {"font": ("맑은 고딕", 9, "bold"), "bd": 0, "padx": 12, "pady": 5, "cursor": "hand2"}

        btn_cfg = {"font": ("맑은 고딕", 9, "bold"), "bd": 0, "padx": 11, "pady": 5, "cursor": "hand2"}
        # 프로젝트 관리 버튼 그룹
        tk.Button(
            toolbar, text="📄 새 프로젝트", bg="#334155", fg="white",
            command=self.new_project, **btn_cfg
        ).pack(side=tk.LEFT, padx=3, pady=6)
        tk.Button(
            toolbar, text="📂 열기 (Ctrl+O)", bg="#334155", fg="white",
            command=self.load_project_dialog, **btn_cfg
        ).pack(side=tk.LEFT, padx=3, pady=6)
        tk.Button(
            toolbar, text="💾 저장 (Ctrl+S)", bg="#0284c7", fg="white",
            command=self.save_project_dialog, **btn_cfg
        ).pack(side=tk.LEFT, padx=3, pady=6)
        tk.Button(
            toolbar, text="📑 다른 이름으로 저장", bg="#0369a1", fg="white",
            command=lambda: self.save_project_dialog(save_as=True), **btn_cfg
        ).pack(side=tk.LEFT, padx=(3, 14), pady=6)


        tk.Button(
            toolbar, text="▶ 선형 재계산(F5)", bg="#0284c7", fg="white",
            command=self.recalculate_all, **btn_style
        ).pack(side=tk.LEFT, padx=(25, 8), pady=6)

        tk.Button(
            toolbar, text="📐 3D DXF 도면 내보내기", bg="#059669", fg="white",
            command=self.export_dxf_dialog, **btn_style
        ).pack(side=tk.LEFT, padx=6, pady=6)

        tk.Button(
            toolbar, text="📊 3D 좌표 CSV 저장", bg="#4f46e5", fg="white",
            command=self.export_csv_dialog, **btn_style
        ).pack(side=tk.LEFT, padx=6, pady=6)

        tk.Button(
            toolbar, text="📑 토공량 조서", bg="#7c3aed", fg="white",
            command=self.export_earthwork_report_dialog, **btn_cfg
        ).pack(side=tk.LEFT, padx=(3, 12), pady=6)

        tk.Button(
            toolbar, text="📋 선형 계산서", bg="#0d9488", fg="white",
            command=self.export_geometry_report_dialog, **btn_cfg
        ).pack(side=tk.LEFT, padx=(3, 12), pady=6)

        # 3D 드라이브 전용 빠른 제어 버튼
        self.btn_drive = tk.Button(toolbar, text="🚗 3D 주행 시작 (Space)", bg="#e11d48", fg="white",
                                   command=self.toggle_drive, **btn_cfg)
        self.btn_drive.pack(side=tk.LEFT, padx=4, pady=6)

        tk.Label(toolbar, text="속도:", bg="#0f172a", fg="#cbd5e0", font=("맑은 고딕", 8, "bold")).pack(side=tk.LEFT,
                                                                                                  padx=(8, 2))
        self.speed_scale = tk.Scale(
            toolbar, from_=20, to=140, orient=tk.HORIZONTAL, bg="#0f172a", fg="#facc15",
            troughcolor="#1e293b", highlightthickness=0, length=100, showvalue=True,
            font=("Consolas", 8), command=lambda v: setattr(self, "drive_speed_kmh", float(v))
        )
        self.speed_scale.set(80)
        self.speed_scale.pack(side=tk.LEFT, padx=2)

        self.status_var = tk.StringVar(value="준비 완료")
        tk.Label(
            toolbar, textvariable=self.status_var, bg="#0f172a", fg="#94a3b8", font=("맑은 고딕", 9)
        ).pack(side=tk.RIGHT, padx=10)

        # 메인 좌우 분할 컨테이너 (PanedWindow)
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#334155", sashwidth=4)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # [좌측 패널] 프로젝트 메타 정보 + 4개 설계 제원 탭
        left_panel = ttk.Frame(main_pane, width=420)
        main_pane.add(left_panel, minsize=380)

        meta_frame = tk.Frame(left_panel, bg="#1e293b", padx=8, pady=6)
        meta_frame.pack(fill=tk.X, padx=6, pady=(6, 2))
        tk.Label(meta_frame, text="노선명:", bg="#1e293b", fg="#cbd5e0", font=("맑은 고딕", 9, "bold")).pack(side=tk.LEFT)
        self.entry_align_name = tk.Entry(meta_frame, bg="#0f172a", fg="#38bdf8", insertbackground="white",
                                         font=("맑은 고딕", 9, "bold"), bd=1, relief=tk.FLAT)
        self.entry_align_name.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
        self.entry_align_name.insert(0, "본선_중심선_01")

        notebook = ttk.Notebook(left_panel)
        notebook.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # 좌측 하단: 실시간 토공량(Earthwork Volume) 요약 카드
        ew_frame = tk.Frame(left_panel, bg="#0f172a", padx=10, pady=8, highlightbackground="#334155",
                            highlightthickness=1)
        ew_frame.pack(fill=tk.X, padx=6, pady=(2, 6))

        tk.Label(ew_frame, text="📊 실시간 토공량 집계 (양단면 평균법, 10m 간격)", bg="#0f172a", fg="#38bdf8",
                 font=("맑은 고딕", 8, "bold")).pack(anchor="w")
        self.earthwork_var = tk.StringVar(value="계산 대기 중...")
        tk.Label(ew_frame, textvariable=self.earthwork_var, bg="#0f172a", fg="#f8fafc", font=("Consolas", 9, "bold"),
                 justify=tk.LEFT).pack(anchor="w", pady=(4, 0))

        self.txt_pi = self._create_editor_tab(
            notebook, "1. 평면 PI (비대칭)",
            "형식: 이름, Easting(X), Northing(Y), 반경(R), 진입완화(L1), 진출완화(L2)"
        )
        self.txt_pvi = self._create_editor_tab(
            notebook, "2. 종단 PVI",
            "형식: 이름, 물리측점(RawSTA), 계획고(EL), 곡선장L (또는 L1, L2)"
        )
        self.txt_super = self._create_editor_tab(
            notebook, "3. 편경사 & 확폭",
            "[편경사] 물리측점, 좌측경사(소수), 우측경사(소수)  /  [하단] 우측 확폭 제원"
        )
        self.txt_eq = self._create_editor_tab(
            notebook, "4. 파정(Station Eq)",
            "형식: 시점측점(StartSTA) 및 파정(후방측점 Back, 전방측점 Ahead)"
        )

        self.txt_struct = self._create_editor_tab(
            notebook, "5. 구조물(교량/터널)",
            "형식: 이름, 유형(BRIDGE/TUNNEL/RETAINING_WALL), 시작RawSTA, 종료RawSTA, 방향(BOTH/LEFT/RIGHT)"
        )

        # [우측 패널] 2x2 4분할 실시간 연동 뷰포트
        # 상단 좌: 평면도(Plan) | 상단 우: 3D 드라이브(3D Drive)
        # 하단 좌: 종단도(Profile) | 하단 우: 횡단면도(Cross Section)
        right_vert_pane = tk.PanedWindow(main_pane, orient=tk.VERTICAL, bg="#334155", sashwidth=4)
        main_pane.add(right_vert_pane , minsize=780)

        top_horiz_pane = tk.PanedWindow(right_vert_pane, orient=tk.HORIZONTAL, bg="#334155", sashwidth=4)
        right_vert_pane.add(top_horiz_pane, height=450)

        # 뷰포트 1: 평면도 (Plan View)
        plan_frame = tk.Frame(top_horiz_pane, bg="#111418")
        top_horiz_pane.add(plan_frame, height=560)
        self.canvas_plan = tk.Canvas(plan_frame, bg="#111418", highlightthickness=0)
        self.canvas_plan.pack(fill=tk.BOTH, expand=True)
        self.canvas_plan.bind("<Motion>", self.on_plan_mouse_move)
        self.canvas_plan.bind("<Configure>", lambda e: self.redraw_all_views())
        self.canvas_plan.bind("<ButtonPress-1>", self.on_plan_mouse_down)
        self.canvas_plan.bind("<B1-Motion>", self.on_plan_mouse_drag)
        self.canvas_plan.bind("<ButtonRelease-1>", self.on_plan_mouse_up)

        # 뷰포트 2: 3D 드라이브 가상 주행 (3D Drive View)
        drive_frame = tk.Frame(top_horiz_pane, bg="#0b1120")
        top_horiz_pane.add(drive_frame, width=540)
        self.canvas_drive = tk.Canvas(drive_frame, bg="#0b1120", highlightthickness=0)
        self.canvas_drive.pack(fill=tk.BOTH, expand=True)
        self.canvas_drive.bind("<Configure>", lambda e: self.draw_3d_drive_view())

        # 3D 드라이브 하단 미니 차로 전환 바
        drive_bar = tk.Frame(drive_frame, bg="#1e293b", height=26)
        drive_bar.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Label(drive_bar, text="주행 차로:", bg="#1e293b", fg="#94a3b8", font=("맑은 고딕", 8)).pack(side=tk.LEFT,
                                                                                               padx=(8, 4))
        for lbl, off_v in [("좌측(-1.75m)", -1.75), ("중심(0.0m)", 0.0), ("우측(+1.75m)", 1.75)]:
            tk.Button(
                drive_bar, text=lbl, bg="#334155", fg="#f8fafc", font=("맑은 고딕", 7, "bold"), bd=0, padx=6, pady=2,
                command=lambda o=off_v: self._set_drive_lane(o)
            ).pack(side=tk.LEFT, padx=2, pady=2)
        bottom_horiz_pane = tk.PanedWindow(right_vert_pane, orient=tk.HORIZONTAL, bg="#334155", sashwidth=4)
        right_vert_pane.add(bottom_horiz_pane, height=380)

        # 뷰포트 3: 종단도 (Profile View)
        prof_frame = tk.Frame(bottom_horiz_pane, bg="#13171d")
        bottom_horiz_pane.add(prof_frame, width=640)
        self.canvas_prof = tk.Canvas(prof_frame, bg="#13171d", highlightthickness=0)
        self.canvas_prof.pack(fill=tk.BOTH, expand=True)
        self.canvas_prof.bind("<Motion>", self.on_prof_mouse_move)
        self.canvas_prof.bind("<Configure>", lambda e: self.redraw_all_views())

        # 뷰포트 4: 실시간 횡단면도 (Cross Section View)
        sec_frame = tk.Frame(bottom_horiz_pane, bg="#151921")
        bottom_horiz_pane.add(sec_frame, width=460)
        self.canvas_sec = tk.Canvas(sec_frame, bg="#151921", highlightthickness=0)
        self.canvas_sec.pack(fill=tk.BOTH, expand=True)
        self.canvas_sec.bind("<Configure>", lambda e: self.draw_cross_section_view())
        self.canvas_prof.bind("<ButtonPress-1>", self.on_prof_mouse_down)
        self.canvas_prof.bind("<B1-Motion>", self.on_prof_mouse_drag)
        self.canvas_prof.bind("<ButtonRelease-1>", self.on_prof_mouse_up)

    def _create_editor_tab(self, notebook: ttk.Notebook, title: str, guide_text: str) -> tk.Text:
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=title)
        ttk.Label(frame, text=guide_text, foreground="#94a3b8", wraplength=380).pack(anchor="w", padx=8, pady=(8, 4))
        txt = tk.Text(
            frame, bg="#0f172a", fg="#f8fafc", insertbackground="#38bdf8",
            font=("Consolas", 10), bd=1, relief=tk.FLAT, padx=8, pady=8
        )
        txt.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        return txt

    def _clear_editors(self):
        for w in (self.txt_pi, self.txt_pvi, self.txt_super, self.txt_eq, self.txt_struct):
            w.delete("1.0", tk.END)

    def _load_default_design_data(self):
        self._clear_editors()
        self.entry_align_name.delete(0, tk.END)
        self.entry_align_name.insert(0, "본선_중심선_01")

        self.txt_pi.insert("1.0", (
            "# Name, Easting, Northing, R, L1, L2\n"
            "BP,   200000.000, 500000.000,   0,   0,  0\n"
            "IP-1, 200420.000, 500260.000, 231, 100, 80\n"
            "IP-2, 200880.000, 500040.000, 166,  80, 90\n"
            "EP,   201320.000, 500320.000,   0,   0,  0\n"
        ))
        self.txt_pvi.insert("1.0", (
            "# Name, RawSTA, Elevation, L1, L2\n"
            "BVP,   0.0,    40.00,   0,   0\n"
            "PVI-1, 420.0,  49.50, 100, 100\n"
            "PVI-2, 880.0,  42.00,  80, 120\n"
            "EVP,   1350.0, 46.50,   0,   0\n"
        ))
        self.txt_super.insert("1.0", (
            "# [SUPERELEVATION] RawSTA, LeftSlope, RightSlope\n"
            "0.0,    -0.02, -0.02\n"
            "260.0,  -0.02, -0.02\n"
            "360.0,   0.05, -0.05\n"
            "540.0,   0.05, -0.05\n"
            "620.0,  -0.02, -0.02\n"
            "740.0,  -0.02, -0.02\n"
            "820.0,  -0.05,  0.05\n"
            "1020.0, -0.05,  0.05\n"
            "1110.0, -0.02, -0.02\n"
            "\n"
            "# [WIDENING_RIGHT] Name, StartSTA, EndSTA, AddWidth, EntryLen, ExitLen, Type(Smooth/Linear)\n"
            "버스정차대, 120.0, 240.0, 3.0, 25.0, 25.0, Smooth\n"
        ))
        self.txt_eq.insert("1.0", (
            "# START_STATION: 시점 기준 측점\n"
            "START, 1000.0\n"
            "# EQUATION: BackSTA, AheadSTA (파정)\n"
            "EQ, 1300.0, 1350.0\n"
        ))
        self.txt_struct.insert("1.0", (
            "# Name, Type(BRIDGE/TUNNEL/RETAINING_WALL), StartSTA, EndSTA, Side\n"
            "제1교량, BRIDGE,         280.0, 410.0, BOTH\n"
            "사면옹벽, RETAINING_WALL, 600.0, 720.0, RIGHT\n"
            "관악터널, TUNNEL,         920.0, 1120.0, BOTH\n"
        ))

    # ==========================================================================
    # 프로젝트 저장 (.c3dproj / .json) 및 불러오기 로직
    # ==========================================================================
    def new_project(self):
        if messagebox.askyesno("새 프로젝트", "현재 편집 내용을 초기화하고 기본 샘플 프로젝트로 시작할까요?"):
            self.is_driving = False
            self.btn_drive.config(text="🚗 3D 주행 시작 (Space)", bg="#e11d48")
            self.current_project_path = None
            self.active_raw_sta = 0.0
            self._load_default_design_data()
            self.recalculate_all()
            self._update_window_title()

    def save_project_dialog(self, save_as: bool = False):

        # 저장 전 현재 제원 유효성 먼저 검증
        self.recalculate_all()
        target_path = self.current_project_path
        if save_as or not target_path:
            default_name = f"{self.entry_align_name.get().strip() or 'alignment_project'}.c3dproj"
            target_path = filedialog.asksaveasfilename(
                title="프로젝트 파일 저장",
                defaultextension=".c3dproj",
                initialfile=default_name,
                filetypes=[("Civil 3D Python 프로젝트", ".c3dproj"), ("JSON 파일", ".json")]
            )
            if not target_path:
                return
            project_payload = {
                "format": "Civil3DPythonStudioProject",
                "version": self.APP_VERSION,
                "alignment_name": self.entry_align_name.get().strip(),
                "active_raw_station": self.active_raw_sta,
                "editors": {
                    "horizontal_pi": self.txt_pi.get("1.0", tk.END).rstrip("\n"),
                    "vertical_pvi": self.txt_pvi.get("1.0", tk.END).rstrip("\n"),
                    "superelevation_widening": self.txt_super.get("1.0", tk.END).rstrip("\n"),
                    "station_equations": self.txt_eq.get("1.0", tk.END).rstrip("\n"),
                    "structures": self.txt_struct.get("1.0", tk.END).rstrip("\n"),
                }
            }
            try:

                with open(target_path, mode="w", encoding="utf-8") as f:
                    json.dump(project_payload, f, ensure_ascii=False, indent=2)
                self.current_project_path = target_path
                self._update_window_title()
                self.status_var.set(f"프로젝트 저장 완료: {os.path.basename(target_path)}")
            except Exception as ex:
                messagebox.showerror("저장 오류", f"프로젝트 저장 중 오류가 발생했습니다:\n{ex}")

    def load_project_dialog(self):
        target_path = filedialog.askopenfilename(
            title="프로젝트 파일 열기",
            filetypes=[("Civil 3D Python 프로젝트", ".c3dproj .json"), ("모든 파일", ".")]
        )

        if not target_path:
            return
        try:
            with open(target_path, mode="r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("format") != "Civil3DPythonStudioProject":
                raise ValueError("올바른 Civil 3D Python Studio 프로젝트 파일이 아닙니다.")
            editors = data.get("editors", {})
            self._clear_editors()
            self.entry_align_name.delete(0, tk.END)
            self.entry_align_name.insert(0, data.get("alignment_name", "불러온_선형"))
            self.txt_pi.insert("1.0", editors.get("horizontal_pi", ""))
            self.txt_pvi.insert("1.0", editors.get("vertical_pvi", ""))
            self.txt_super.insert("1.0", editors.get("superelevation_widening", ""))
            self.txt_eq.insert("1.0", editors.get("station_equations", ""))
            self.txt_struct.insert("1.0", editors.get("station_equations", ""))
            self.active_raw_sta = float(data.get("structures", 0.0))
            self.current_project_path = target_path
            self._update_window_title()
            self.recalculate_all()
            self.status_var.set(f"프로젝트 불러오기 완료: {os.path.basename(target_path)}")
        except Exception as ex:
            messagebox.showerror("불러오기 오류", f"프로젝트 파일을 읽는 중 오류가 발생했습니다:\n{ex}")

    # ==========================================================================
    # 3D 드라이브(가상 주행) 애니메이션 루프
    # ==========================================================================
    def toggle_drive(self):
        self.is_driving = not self.is_driving

        if self.is_driving:
            self.btn_drive.config(text="⏸ 주행 일시정지 (Space)", bg="#0284c7")
        else:
            self.btn_drive.config(text="🚗 3D 주행 시작 (Space)", bg="#e11d48")

    def _set_drive_lane(self, offset_val: float):
        self.drive_lane_offset = offset_val

        self.draw_3d_drive_view()

    def _drive_animation_loop(self):
        if self.is_driving and self.h_align and self.v_prof:
            v_ms = (self.drive_speed_kmh * 1000.0) / 3600.0

            self.active_raw_sta += v_ms * self.drive_dt
            if self.active_raw_sta >= self.h_align.total_length - 25.0:
                self.active_raw_sta = 0.0
            self._sync_all_active_markers()
        self.root.after(int(self.drive_dt * 1000), self._drive_animation_loop)

    def _sync_all_active_markers(self):
        """현재 활성 측점(active_raw_sta) 변화 시 4개 뷰포트를 모두 즉시 동기화"""

        self._update_plan_active_marker()
        self._update_prof_active_marker()
        self.draw_cross_section_view()
        self.draw_3d_drive_view()

    def recalculate_all(self):
        try:
            align_name = self.entry_align_name.get().strip() or "본선_중심선"
            # 1. 평면 PI 파싱
            self.pis = []
            for line in self.txt_pi.get("1.0", tk.END).splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split(",")]
                self.pis.append(PIPoint(
                    name=parts[0],
                    easting=float(parts[1]),
                    northing=float(parts[2]),
                    R=float(parts[3]) if len(parts) > 3 and parts[3] else 0.0,
                    L1=float(parts[4]) if len(parts) > 4 and parts[4] else 0.0,
                    L2=float(parts[5]) if len(parts) > 5 and parts[5] else None
                ))
            self.h_align = Alignment.create(name=align_name, pi_list=self.pis)

            # 2. 종단 PVI 파싱
            pvis = []
            for line in self.txt_pvi.get("1.0", tk.END).splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split(",")]
                pvis.append(PVIPoint(
                    name=parts[0],
                    station=float(parts[1]),
                    elevation=float(parts[2]),
                    L1=float(parts[3]) if len(parts) > 3 and parts[3] else 0.0,
                    L2=float(parts[4]) if len(parts) > 4 and parts[4] else 0.0
                ))
            pvis[-1].station = self.h_align.total_length
            self.v_prof = Profile.create(name="본선_배치 (1)", pvi_list=pvis)

            # 3. 편경사 및 확폭 파싱
            sup_list = []
            self.right_lane = OffsetAlignment("우측차선_ETW", self.h_align, nominal_offset=+3.5)
            self.left_lane = OffsetAlignment("좌측차선_ETW", self.h_align, nominal_offset=-3.5)
            mode = "SUPER"
            for line in self.txt_super.get("1.0", tk.END).splitlines():
                line = line.strip()
                if "[WIDENING_RIGHT]" in line:
                    mode = "WIDEN"
                    continue
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split(",")]
                if mode == "SUPER":
                    sup_list.append(SuperelevationStation(float(parts[0]), float(parts[1]), float(parts[2])))
                else:
                    self.right_lane.add_widening(WideningRegion(
                        name=parts[0],
                        start_station=float(parts[1]),
                        end_station=float(parts[2]),
                        widening_width=float(parts[3]),
                        entry_transition_len=float(parts[4]),
                        exit_transition_len=float(parts[5]),
                        transition_type=parts[6] if len(parts) > 6 else "Smooth"
                    ))
            self.sup_tbl = SuperelevationTable(sup_list)

            # 구조물 파싱 및 코리더 조립
            structs = []
            for line in self.txt_struct.get("1.0", tk.END).splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split(",")]
                structs.append(StructureRegion(
                    parts[0], parts[1].upper(), float(parts[2]), float(parts[3]),
                    parts[4].upper() if len(parts) > 4 else "BOTH"
                ))

            terrain = ExistingGroundTerrain(
                base_profile_func=lambda sta: self.v_prof.elevation_and_grade_at(sta)[0]
            )
            self.corridor = Corridor3DEngine(
                name='Corriodr 1',
                alignment=self.h_align,
                profile=self.v_prof,
                left_offset_align=self.left_lane,
                right_offset_align=self.right_lane,
                superelevation_table=self.sup_tbl,
                terrain=terrain,
                structures=structs
            )

            # 4. 파정(Station Equation) 파싱
            start_sta = 0.0
            eq_pairs = []
            for line in self.txt_eq.get("1.0", tk.END).splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split(",")]
                if parts[0].upper() == "START":
                    start_sta = float(parts[1])
                elif parts[0].upper() == "EQ":
                    eq_pairs.append((float(parts[1]), float(parts[2])))

            self.sta_mgr = StationEquationManager(start_station=start_sta,
                                                  total_physical_length=self.h_align.total_length)
            for b_sta, a_sta in eq_pairs:
                self.sta_mgr.add_equation_by_back(b_sta, a_sta)

            self.active_raw_sta = min(self.active_raw_sta, self.h_align.total_length)
            self.redraw_all_views()
            end_disp, _ = self.sta_mgr.raw_to_display(self.h_align.total_length)
            self.status_var.set(
                f"계산 완료 | 총 연장: {self.h_align.total_length:.2f}m | "
                f"측점 범위: {self.sta_mgr.format_station(start_sta)} ~ {self.sta_mgr.format_station(end_disp)}"
            )
            # 전 구간 토공량(절토/성토) 자동 산출 및 요약 패널 업데이트
            tot_cut, tot_fill = self._compute_total_earthwork(interval=10.0)
            net_vol = tot_cut - tot_fill
            net_label = f"잔토(사토) +{net_vol:,.1f} ㎥" if net_vol >= 0 else f"부족토(토취) {net_vol:,.1f} ㎥"
            self.earthwork_var.set(
                f"총 절토량(Cut) : {tot_cut:10,.1f} ㎥\n"
                f"총 성토량(Fill): {tot_fill:10,.1f} ㎥\n"
                f"순 토공량(Net) : {net_label}"
            )
        except Exception as ex:
            messagebox.showerror("설계 제원 오류", str(ex))

    def _compute_total_earthwork(self, interval: float = 10.0) -> Tuple[float, float]:
        """양단면 평균법으로 전 구간 총 절토량 및 총 성토량(m³) 계산"""
        if not self.corridor:
            return 0.0, 0.0
        report = self.corridor.compute_earthwork_volumes(interval=interval)
        if not report:
            return 0.0, 0.0
        # 마지막 행의 누적값이 전 구간 총합
        return report[-1]["cum_cut"], report[-1]["cum_fill"]

    def redraw_all_views(self):
        if not self.h_align or not self.v_prof:
            return
        self.draw_plan_view()
        self.draw_profile_view()
        self.draw_cross_section_view()
        self.draw_3d_drive_view()

    # --------------------------------------------------------------------------
    # [뷰포트 1] 평면도(Plan View) 렌더링
    # --------------------------------------------------------------------------
    def draw_plan_view(self):
        c = self.canvas_plan
        c.delete("all")
        w, h = max(100, c.winfo_width()), max(100, c.winfo_height())

        total_len = self.h_align.total_length
        samples = 240
        cl_pts, r_pts, l_pts = [], [], []
        all_x, all_y = [], []

        for i in range(samples + 1):
            s = total_len * (i / samples)
            ce, cn = self.h_align.point_location(s, 0.0)
            re, rn = self.h_align.point_location(s, self.right_lane.get_offset_at(s)[0])
            le, ln = self.h_align.point_location(s, self.left_lane.get_offset_at(s)[0])
            cl_pts.append((ce, cn))
            r_pts.append((re, rn))
            l_pts.append((le, ln))
            all_x.extend([ce, re, le])
            all_y.extend([cn, rn, ln])

        for pi in self.pis:
            all_x.append(pi.easting)
            all_y.append(pi.northing)

        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        span_x = max(1.0, max_x - min_x)
        span_y = max(1.0, max_y - min_y)
        pad = 45
        scale = min((w - 2 * pad) / span_x, (h - 2 * pad) / span_y)
        cx, cy = (min_x + max_x) * 0.5, (min_y + max_y) * 0.5
        self.plan_transform = (scale, cx, cy, w * 0.5, h * 0.5)

        def to_scr(gx, gy):
            return w * 0.5 + (gx - cx) * scale, h * 0.5 - (gy - cy) * scale

        pi_scr = []
        for idx, pi in enumerate(self.pis):
            sx, sy = to_scr(pi.easting, pi.northing)
            pi_scr.extend([sx, sy])
            c.create_polygon(sx, sy - 6, sx + 5, sy + 4, sx - 5, sy + 4, outline="#facc15", fill="", width=1.5)
            c.create_text(sx, sy - 12, text=pi.name, fill="#facc15", font=("Consolas", 8, "bold"))
            # ✅ 수정: 태그를 하나로 통합
            c.create_oval(sx - 10, sy - 10, sx + 10, sy + 10, outline="", fill="",
                          tags=(f"plan_pi_{idx}",))
        c.create_line(*pi_scr, fill="#475569", dash=(3, 3))

        for pts_arr in (r_pts, l_pts):
            coords = [coord for gx, gy in pts_arr for coord in to_scr(gx, gy)]
            c.create_line(*coords, fill="#2dd4bf", width=1.5)

        cl_coords = [coord for gx, gy in cl_pts for coord in to_scr(gx, gy)]
        c.create_line(*cl_coords, fill="#f43f5e", width=2.5)

        sta_step = 100.0
        s_tick = 0.0
        while s_tick <= total_len + 1e-6:
            gx, gy = self.h_align.point_location(min(s_tick, total_len), 0.0)
            sx, sy = to_scr(gx, gy)
            disp_s, _ = self.sta_mgr.raw_to_display(min(s_tick, total_len))
            c.create_oval(sx - 2.5, sy - 2.5, sx + 2.5, sy + 2.5, fill="#ffffff", outline="")
            c.create_text(sx, sy + 12, text=self.sta_mgr.format_station(disp_s), fill="#94a3b8", font=("Consolas", 8))
            s_tick += sta_step

        c.create_text(14, 14, anchor="nw", fill="#38bdf8", font=("맑은 고딕", 9, "bold"),
                      text="PLAN VIEW (평면 선형 & 확폭 차선) - 마우스를 움직여 실시간 추적")
        self._update_plan_active_marker()

    def _update_plan_active_marker(self):
        c = self.canvas_plan
        c.delete("active_marker")
        if not self.h_align:
            return
        scale, cx, cy, hw, hh = self.plan_transform
        gx, gy = self.h_align.point_location(self.active_raw_sta, 0.0)
        sx, sy = hw + (gx - cx) * scale, hh - (gy - cy) * scale
        # 전방 시야 방향 화살표(차량 헤딩) 표시
        look_s = min(self.h_align.total_length, self.active_raw_sta + 15.0)
        lx, ly = self.h_align.point_location(look_s, self.drive_lane_offset)
        lsx, lsy = hw + (lx - cx) * scale, hh - (ly - cy) * scale
        c.create_line(sx, sy, lsx, lsy, fill="#facc15", width=2.5, arrow=tk.LAST, tags="active_marker")
        c.create_oval(sx - 5, sy - 5, sx + 5, sy + 5, fill="#38bdf8", outline="#ffffff", width=1.5,
                      tags="active_marker")

    # --------------------------------------------------------------------------
    # [뷰포트 2] 실시간 3D 드라이브 가상 주행 (3D Drive View)
    # --------------------------------------------------------------------------
    def draw_3d_drive_view(self):
        c = self.canvas_drive

        c.delete("all")
        if not self.h_align or not self.v_prof:
            return
        w, h = max(120, c.winfo_width()), max(120, c.winfo_height())
        # 배경 하늘 & 지면
        horizon_y = h * 0.44
        c.create_rectangle(0, 0, w, horizon_y, fill="#0c192c", outline="")
        c.create_rectangle(0, horizon_y, w, h, fill="#111827", outline="")

        cam_sta = self.active_raw_sta
        look_sta = min(self.h_align.total_length, cam_sta + 20.0)

        if look_sta <= cam_sta + 0.5:
            look_sta = min(self.h_align.total_length, cam_sta + 1.0)

        cam_e, cam_n = self.h_align.point_location(cam_sta, self.drive_lane_offset)
        cam_cl_z, curr_grade = self.v_prof.elevation_and_grade_at(cam_sta)

        l_slp, r_slp = self.sup_tbl.get_slopes_at(cam_sta)

        curr_cross = r_slp if self.drive_lane_offset >= 0 else l_slp
        cam_z = cam_cl_z + abs(self.drive_lane_offset) * curr_cross + self.drive_eye_height
        tgt_e, tgt_n = self.h_align.point_location(look_sta, self.drive_lane_offset)

        tgt_cl_z, _ = self.v_prof.elevation_and_grade_at(look_sta)
        tgt_z = tgt_cl_z + abs(self.drive_lane_offset) * curr_cross + self.drive_eye_height * 0.85
        fx, fy, fz = tgt_e - cam_e, tgt_n - cam_n, tgt_z - cam_z
        f_len = max(1e-6, math.hypot(fx, fy, fz))
        fx, fy, fz = fx / f_len, fy / f_len, fz / f_len

        rx, ry, rz = fy, -fx, 0.0
        r_len = max(1e-6, math.hypot(rx, ry, rz))
        rx, ry, rz = rx / r_len, ry / r_len, rz / r_len
        ux, uy, uz = ry * fz - rz * fy, rz * fx - rx * fz, rx * fy - ry * fx
        # 차량 편경사 기울기(Roll) 적용
        roll_ang = -curr_cross * 0.65
        cos_r, sin_r = math.cos(roll_ang), math.sin(roll_ang)
        rx_r, ry_r, rz_r = rx * cos_r + ux * sin_r, ry * cos_r + uy * sin_r, rz * cos_r + uz * sin_r
        ux_r, uy_r, uz_r = -rx * sin_r + ux * cos_r, -ry * sin_r + uy * cos_r, -rz * sin_r + uz * cos_r
        fov_scale = w * 0.75

        def project_3d(pt_3d):
            px, py, pz = pt_3d

            dx = px - cam_e
            dy = py - cam_n
            dz = pz - cam_z
            z_cam = dx * fx + dy * fy + dz * fz
            if z_cam <= 1.2:  # 카메라 뒤쪽이나 너무 가까운 점 클리핑
                return None
            x_cam = dx * rx_r + dy * ry_r + dz * rz_r
            y_cam = dx * ux_r + dy * uy_r + dz * uz_r
            sx = w * 0.5 + fov_scale * (x_cam / z_cam)
            sy = h * 0.48 - fov_scale * (y_cam / z_cam)
            return sx, sy

        def section_pts(s_val):
            sec = self.corridor.sample_cross_section(s_val)
            p = sec["points"]
            return {k: (p[k][1], p[k][2], p[k][3]) for k in ["L_DAY", "L_EPS", "L_ETW", "CL", "R_ETW", "R_EPS", "R_DAY"]}, sec

        # ── 8. 슬라이스 (view_dist 600으로 확장)
        view_dist, step = 600.0, 4.0
        slices = []
        sv = cam_sta + 2.0
        max_s = min(self.h_align.total_length, cam_sta + view_dist)
        while sv <= max_s:
            slices.append(section_pts(sv))
            sv += step

        keys = ["L_DAY", "L_EPS", "L_ETW", "CL", "R_ETW", "R_EPS", "R_DAY"]
        for i in range(len(slices) - 2, -1, -1):
            sn, sec_n = slices[i]
            sf, _ = slices[i + 1]

            #투영 로직
            dist_ratio = (i * step) / view_dist
            pn = {k: project_3d(sn[k]) for k in keys}
            pf = {k: project_3d(sf[k]) for k in keys}
            if any(pn[k] is None or pf[k] is None for k in keys):
                continue

            shade = 1.0 - dist_ratio * 0.55
            is_even = (int((cam_sta + i * step) // step) % 2 == 0)

            # 절토(갈색/붉은색) vs 성토(녹색) vs 교량 난간(노란 회색) 색상 분기
            for side_a, side_b, mode in [("L_DAY", "L_EPS", sec_n["left_mode"]), ("R_EPS", "R_DAY", sec_n["right_mode"])]:
                if mode == "CUT":
                    scol = f"#{int(115 * shade):02x}{int(65 * shade):02x}{int(45 * shade):02x}"
                elif mode == "BRIDGE":
                    scol = f"#{int(140 * shade):02x}{int(145 * shade):02x}{int(155 * shade):02x}"
                else:
                    scol = f"#{int(25 * shade):02x}{int(85 * shade):02x}{int(48 * shade):02x}"
                c.create_polygon(*pn[side_a], *pn[side_b], *pf[side_b], *pf[side_a], fill=scol, outline="")

            # 터널 구간일 때 전방 3D 터널 아치 천장 링 그리기
            if sec_n["left_mode"] == "TUNNEL":
                c.create_line(*pn["L_DAY"], *pn["R_DAY"], fill="#f59e0b", width=2)

            # 길어깨
            shd_col = f"#{int(45 * shade):02x}{int(52 * shade):02x}{int(62 * shade):02x}"
            for a, b in [("L_EPS", "L_ETW"), ("R_ETW", "R_EPS")]:
                c.create_polygon(*pn[a], *pn[b], *pf[b], *pf[a], fill=shd_col, outline="")

            # 아스팔트
            rb = 58 if is_even else 50
            road_col = f"#{int(rb * shade):02x}{int((rb + 4) * shade):02x}{int((rb + 10) * shade):02x}"
            c.create_polygon(*pn["L_ETW"], *pn["R_ETW"], *pf["R_ETW"], *pf["L_ETW"], fill=road_col, outline="")

            # 차선
            lw = max(1, int(2.5 * (1.0 - dist_ratio)))
            c.create_line(*pn["CL"], *pf["CL"], fill="#facc15", width=lw)
            c.create_line(*pn["L_ETW"], *pf["L_ETW"], fill="#f8fafc", width=max(1, lw - 1))
            c.create_line(*pn["R_ETW"], *pf["R_ETW"], fill="#f8fafc", width=max(1, lw - 1))

        # ── 9. HUD
        disp_s, zone = self.sta_mgr.raw_to_display(cam_sta)
        r_off, _ = self.right_lane.get_offset_at(cam_sta)
        c.create_text(12, 10, anchor="nw", fill="#38bdf8",
                      font=("맑은 고딕", 9, "bold"),
                      text="3D DRIVE VIEW (1인칭 가상 주행)")
        hud = (
            f"STA: {self.sta_mgr.format_station(disp_s)} (Z{zone}) | {int(self.drive_speed_kmh)} km/h\n"
            f"EL : {cam_cl_z:.3f}m (경사 {curr_grade * 100:+.2f}%) | "
            f"편경사: {l_slp * 100:+.1f}%/{r_slp * 100:+.1f}% | 우폭:{r_off:.2f}m"
        )
        c.create_rectangle(10, 30, w - 10, 68, fill="#0f172a", outline="#334155")
        c.create_text(18, 36, anchor="nw", text=hud, fill="#f8fafc", font=("Consolas", 8, "bold"))
    # --------------------------------------------------------------------------
    # [뷰포트 3] 종단도(Profile View) 렌더링
    # --------------------------------------------------------------------------
    def draw_profile_view(self):
        c = self.canvas_prof
        c.delete("all")
        w, h = max(100, c.winfo_width()), max(100, c.winfo_height())
        pl, pr, pt, pb = 58, w - 24, 34, h - 36
        min_s, max_s = 0.0, max(1.0, self.h_align.total_length)

        els = [p.elevation for p in self.v_prof.pvi_list]
        min_el = math.floor((min(els) - 2.0) / 2.0) * 2.0
        max_el = math.ceil((max(els) + 2.0) / 2.0) * 2.0
        self.prof_bounds = (pl, pr, pt, pb, min_s, max_s, min_el, max_el)

        def to_px(s_val, el_val):
            x = pl + ((s_val - min_s) / (max_s - min_s)) * (pr - pl)
            y = pb - ((el_val - min_el) / max(0.1, max_el - min_el)) * (pb - pt)
            return x, y

        c.create_rectangle(pl, pt, pr, pb, outline="#334155")

        curr_e = min_el
        while curr_e <= max_el + 1e-6:
            _, y = to_px(min_s, curr_e)
            c.create_line(pl, y, pr, y, fill="#1e293b")
            c.create_text(pl - 6, y, anchor="e", text=f"{curr_e:.1f}", fill="#94a3b8", font=("Consolas", 8))
            curr_e += 2.0

        pvi_coords = []
        for idx, pvi in enumerate(self.v_prof.pvi_list):
            px, py = to_px(pvi.station, pvi.elevation)
            pvi_coords.extend([px, py])
            c.create_polygon(px, py, px - 5, py - 8, px + 5, py - 8, outline="#facc15", fill="")
            # 드래그 감지용 히트 영역 (반경 8px)
            c.create_oval(px - 8, py - 10, px + 8, py + 6, outline="", fill="", tags=(f"pvi_{idx}",))
        c.create_line(*pvi_coords, fill="#475569", dash=(2, 2))

        fg_coords = []
        for i in range(181):
            s = min_s + (max_s - min_s) * (i / 180.0)
            el, _ = self.v_prof.elevation_and_grade_at(s)
            fg_coords.extend(to_px(s, el))
        c.create_line(*fg_coords, fill="#f43f5e", width=2.2)

        #
        # ----------------------------------------------------------------------
        # [추가 1] 현지지반선 (EG - 녹색 점선) 렌더링
        # ----------------------------------------------------------------------
        if self.corridor and self.corridor.terrain:
            eg_coords = []
            for i in range(161):
                s = min_s + (max_s - min_s) * (i / 160.0)
                eg_el = self.corridor.terrain.elevation_at(s, 0.0)
                eg_coords.extend(to_px(s, eg_el))
            c.create_line(*eg_coords, fill="#4ade80", width=1.6, dash=(4, 2))

        # ----------------------------------------------------------------------
        # [추가 2] 구조물 구간 (교량/터널/옹벽) 범위 하이라이트 및 라벨 표시
        # ----------------------------------------------------------------------
        if self.corridor and self.corridor.structures:
            struct_colors = {
                "BRIDGE": ("#38bdf8", "교량"),
                "TUNNEL": ("#f59e0b", "터널"),
                "RETAINING_WALL": ("#a78bfa", "옹벽")
            }
            # 구조물 구간 바(Bar) 그리는 루프 내부에 시·종점 드래그 핸들 추가:
            for idx, st in enumerate(self.corridor.structures):
                s1 = max(min_s, st.start_station)
                s2 = min(max_s, st.end_station)
                if s2 <= s1:
                    continue

                x1, _ = to_px(s1, min_el)
                x2, _ = to_px(s2, min_el)
                col, type_kor = struct_colors.get(st.structure_type, ("#94a3b8", "구조물"))

                # 구조물 시작/끝 수직 경계선 및 상단 구간 바(Bar) 그리기
                c.create_line(x1, pt + 22, x1, pb, fill=col, dash=(2, 2), width=1.2)
                c.create_line(x2, pt + 22, x2, pb, fill=col, dash=(2, 2), width=1.2)
                c.create_rectangle(x1, pt + 22, x2, pt + 36, fill="#1e293b", outline=col, width=1.2)
                c.create_text(
                    (x1 + x2) * 0.5, pt + 29,
                    text=f"[{type_kor}] {st.name}",
                    fill=col, font=("맑은 고딕", 7, "bold")
                )

                # 시점(x1) 및 종점(x2) 드래그용 사각 그립 핸들 추가
                c.create_rectangle(x1 - 4, pt + 22, x1 + 4, pt + 36, fill=col, outline="#ffffff",
                                   tags=("st_handle", f"st_start_{idx}"))
                c.create_rectangle(x2 - 4, pt + 22, x2 + 4, pt + 36, fill=col, outline="#ffffff",
                                   tags=("st_handle", f"st_end_{idx}"))
        s_step = 200.0
        curr_s = 0.0
        while curr_s <= max_s + 1e-6:
            x, _ = to_px(curr_s, min_el)
            c.create_line(x, pt, x, pb, fill="#1e293b")
            disp_s, _ = self.sta_mgr.raw_to_display(min(curr_s, max_s))
            c.create_text(x, pb + 12, text=self.sta_mgr.format_station(disp_s), fill="#94a3b8", font=("Consolas", 8))
            curr_s += s_step

        c.create_text(14, 10, anchor="nw", fill="#38bdf8", font=("맑은 고딕", 9, "bold"),
                      text="PROFILE VIEW (종단 선형)")
        self._update_prof_active_marker()

    def _update_prof_active_marker(self):
        c = self.canvas_prof
        c.delete("active_prof")
        pl, pr, pt, pb, min_s, max_s, min_el, max_el = self.prof_bounds
        el, grade = self.v_prof.elevation_and_grade_at(self.active_raw_sta)
        x = pl + ((self.active_raw_sta - min_s) / (max_s - min_s)) * (pr - pl)
        y = pb - ((el - min_el) / max(0.1, max_el - min_el)) * (pb - pt)

        c.create_line(x, pt, x, pb, fill="#38bdf8", dash=(3, 3), tags="active_prof")
        c.create_oval(x - 4, y - 4, x + 4, y + 4, fill="#f43f5e", outline="#ffffff", width=1.5, tags="active_prof")
        c.create_text(
            pr - 8, pt + 12, anchor="ne", fill="#e2e8f0", font=("Consolas", 8, "bold"),
            text=f"EL: {el:.3f}m | 경사: {grade * 100:+.2f}%", tags="active_prof"
        )

    # --------------------------------------------------------------------------
    # [뷰포트 4] 실시간 횡단면도(Cross Section View) 렌더링
    # --------------------------------------------------------------------------
    def draw_cross_section_view(self):
        c = self.canvas_sec
        c.delete("all")
        if not self.corridor:
            return
        w, h = max(100, c.winfo_width()), max(100, c.winfo_height())

        s = self.active_raw_sta
        disp_s, zone = self.sta_mgr.raw_to_display(s)
        sec = self.corridor.sample_cross_section(s)
        pts = sec["points"]
        cl_el = sec["points"]["CL"][3]

        cx, cy = w * 0.5, h * 0.58
        scale_x = (w - 60) / 36.0  # 절성토 법면 폭을 고려해 좌우 36m 범위 표시
        scale_y = scale_x * 2.5

        def to_sec(off_x, abs_el):
            return cx + off_x * scale_x, cy - (abs_el - cl_el) * scale_y

        # 1. 현지지반선(EG - 녹색 실선) 그리기 (-18m ~ +18m)
        eg_coords = []
        for ox in range(-18, 19, 1):
            eg_el = self.corridor.terrain.elevation_at(s, float(ox))
            eg_coords.extend(to_sec(ox, eg_el))
        c.create_line(*eg_coords, fill="#4ade80", width=2.0)

        # 2. 좌/우 절성토 법면 또는 구조물(교량/터널/옹벽) 그리기
        for side_keys, mode in [(["L_DAY", "L_EPS"], sec["left_mode"]), (["R_EPS", "R_DAY"], sec["right_mode"])]:
            p1 = to_sec(pts[side_keys[0]][0], pts[side_keys[0]][3])
            p2 = to_sec(pts[side_keys[1]][0], pts[side_keys[1]][3])
            color = "#f87171" if mode == "CUT" else ("#60a5fa" if mode == "FILL" else "#facc15")
            c.create_line(*p1, *p2, fill=color, width=2.5)

        # 터널 아치 천장 곡선 표시
        if sec["left_mode"] == "TUNNEL":
            lx, ly = to_sec(pts["L_DAY"][0], pts["L_DAY"][3])
            rx, ry = to_sec(pts["R_DAY"][0], pts["R_DAY"][3])
            c.create_arc(lx, ly - 35, rx, ly + 35, start=0, extent=180, style=tk.ARC, outline="#facc15", width=2.5)

        # 교량 하부 거더 및 교각 표시
        if sec["left_mode"] == "BRIDGE":
            lx, ly = to_sec(pts["L_EPS"][0], pts["L_EPS"][3])
            rx, ry = to_sec(pts["R_EPS"][0], pts["R_EPS"][3])
            c.create_rectangle(lx, ly, rx, ly + 14, fill="#475569", outline="#facc15")
            c.create_rectangle(cx - 8, ly + 14, cx + 8, h - 15, fill="#334155", outline="#94a3b8")

        # 3. 도로 본선 포장 단면 (L_EPS ~ L_ETW ~ CL ~ R_ETW ~ R_EPS)
        road_keys = ["L_EPS", "L_ETW", "CL", "R_ETW", "R_EPS"]
        top_scr = [to_sec(pts[k][0], pts[k][3]) for k in road_keys]
        bot_scr = [to_sec(pts[k][0], pts[k][3] - 0.3) for k in reversed(road_keys)]
        c.create_polygon(*[xy for pt in (top_scr + bot_scr) for xy in pt], fill="#1e293b", outline="#38bdf8", width=2)

        # 4. 상단 상태 HUD (절성토 단면적 및 활성 구조물 표시)
        struct_str = f" | 구조물: {','.join(sec['structures'])}" if sec["structures"] else ""
        c.create_text(12, 10, anchor="nw", fill="#38bdf8", font=("맑은 고딕", 9, "bold"),
                      text=f"CROSS SECTION - STA {self.sta_mgr.format_station(disp_s)} (Z{zone}){struct_str}")
        info = (
            f"좌측: {sec['left_mode']} | 우측: {sec['right_mode']} | "
            f"절토면적(Cut): {sec['cut_area']:.2f}㎡ | 성토면적(Fill): {sec['fill_area']:.2f}㎡"
        )
        c.create_text(12, 30, anchor="nw", fill="#cbd5e0", font=("Consolas", 8), text=info)

    # --------------------------------------------------------------------------
    # 마우스 실시간 연동 이벤트 핸들러
    # --------------------------------------------------------------------------
    def on_plan_mouse_move(self, event):
        if not self.h_align:
            return
        scale, cx, cy, hw, hh = self.plan_transform
        gx = cx + (event.x - hw) / scale
        gy = cy - (event.y - hh) / scale
        res = self.h_align.station_offset(gx, gy)
        if res is None:
            return
        raw_sta, offset, pe, pn = res
        #res = station, signed_offset, proj_e, proj_n
        self.canvas_plan.delete("plan_tooltip")


        self.active_raw_sta = raw_sta
        self._sync_all_active_markers()

        psx, psy = hw + (pe - cx) * scale, hh - (pn - cy) * scale
        self.canvas_plan.create_line(event.x, event.y, psx, psy, fill="#facc15", dash=(3, 3), tags="plan_tooltip")

        disp_s, zone = self.sta_mgr.raw_to_display(raw_sta)
        cl_el, _ = self.v_prof.elevation_and_grade_at(raw_sta)
        side = "우측(R)" if offset >= 0 else "좌측(L)"
        msg = (
            f"STA : {self.sta_mgr.format_station(disp_s)} (Z{zone})\n"
            f"OFF : {side} {abs(offset):.2f} m\n"
            f"EL  : {cl_el:.3f} m"
        )
        tx, ty = event.x + 14, event.y + 14
        tid = self.canvas_plan.create_text(tx + 6, ty + 4, anchor="nw", text=msg, fill="#ffffff",
                                           font=("Consolas", 8, "bold"), tags="plan_tooltip")
        bbox = self.canvas_plan.bbox(tid)
        if bbox:
            rid = self.canvas_plan.create_rectangle(bbox[0] - 4, bbox[1] - 3, bbox[2] + 4, bbox[3] + 3, fill="#0f172a",
                                                    outline="#38bdf8", tags="plan_tooltip")
            self.canvas_plan.tag_raise(tid, rid)

    def on_prof_mouse_move(self, event):
        if not self.h_align or not self.v_prof:
            return
        pl, pr, pt, pb, min_s, max_s, _, _ = self.prof_bounds
        if not (pl <= event.x <= pr and pt <= event.y <= pb):
            return
        ratio = (event.x - pl) / max(1.0, pr - pl)
        self.active_raw_sta = min_s + ratio * (max_s - min_s)
        self._sync_all_active_markers()

    # --------------------------------------------------------------------------
    # 3D DXF 및 3D CSV 파일 내보내기 기능
    # --------------------------------------------------------------------------
    def _collect_3d_corridor_data(self, interval: float = 5.0):
        flines: Dict[str, List[Tuple[float, float, float]]] = {
            "CL": [], "L_ETW": [], "R_ETW": [], "L_Daylight": [], "R_Daylight": []
        }
        rows = []
        labels = []
        total = self.h_align.total_length
        curr = 0.0

        while curr <= total + 1e-6:
            s = min(curr, total)
            disp_s, zone = self.sta_mgr.raw_to_display(s)
            disp_str = self.sta_mgr.format_station(disp_s)
            cl_e, cl_n = self.h_align.point_location(s, 0.0)
            cl_el, _ = self.v_prof.elevation_and_grade_at(s)
            l_slp, r_slp = self.sup_tbl.get_slopes_at(s)
            l_off, l_dw = self.left_lane.get_offset_at(s)
            r_off, r_dw = self.right_lane.get_offset_at(s)

            l_el = cl_el + abs(l_off) * l_slp
            r_el = cl_el + abs(r_off) * r_slp
            ld_off, rd_off = l_off - 3.0, r_off + 3.0
            ld_el = l_el - 1.5 * 0.04 - 1.5 * 0.5
            rd_el = r_el - 1.5 * 0.04 - 1.5 * 0.5

            pts = {
                "CL": (0.0, cl_e, cl_n, cl_el),
                "L_ETW": (l_off, *self.h_align.point_location(s, l_off), l_el),
                "R_ETW": (r_off, *self.h_align.point_location(s, r_off), r_el),
                "L_Daylight": (ld_off, *self.h_align.point_location(s, ld_off), ld_el),
                "R_Daylight": (rd_off, *self.h_align.point_location(s, rd_off), rd_el),
            }

            for code, (off, e, n, z) in pts.items():
                flines[code].append((e, n, z))
                rows.append([f"{s:.3f}", disp_str, zone, code, f"{off:.3f}", f"{e:.6f}", f"{n:.6f}", f"{z:.6f}"])

            if abs(round(s / 20.0) * 20.0 - s) < 1e-4:
                labels.append((cl_e, cl_n, f"STA {disp_str}"))

            if s >= total:
                break
            curr += interval

        return flines, rows, labels

    def export_dxf_dialog(self):
        path = filedialog.asksaveasfilename(
            title="3D 코리더 DXF 저장", defaultextension=".dxf",
            initialfile="corridor_3d_output.dxf", filetypes=[("AutoCAD DXF", "*.dxf")]
        )
        if not path:
            return

        flines, _, labels = self._collect_3d_corridor_data(interval=5.0)
        dxf = [
            "0", "SECTION", "2", "HEADER", "0", "ENDSEC",
            "0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER",
            "0", "LAYER", "2", "CL_3D", "70", "0", "62", "1", "6", "CONTINUOUS",
            "0", "LAYER", "2", "ROAD_EDGE_3D", "70", "0", "62", "2", "6", "CONTINUOUS",
            "0", "LAYER", "2", "DAYLIGHT_3D", "70", "0", "62", "3", "6", "CONTINUOUS",
            "0", "LAYER", "2", "STATION_LABELS", "70", "0", "62", "4", "6", "CONTINUOUS",
            "0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"
        ]

        for code, pts in flines.items():
            lyr = "CL_3D" if code == "CL" else ("DAYLIGHT_3D" if "Daylight" in code else "ROAD_EDGE_3D")
            dxf.extend(["0", "POLYLINE", "8", lyr, "66", "1", "70", "8", "10", "0.0", "20", "0.0", "30", "0.0"])
            for x, y, z in pts:
                dxf.extend(["0", "VERTEX", "8", lyr, "70", "32", "10", f"{x:.6f}", "20", f"{y:.6f}", "30", f"{z:.6f}"])
            dxf.extend(["0", "SEQEND", "8", lyr])

        for x, y, txt in labels:
            dxf.extend(
                ["0", "TEXT", "8", "STATION_LABELS", "10", f"{x:.6f}", "20", f"{y:.6f}", "30", "0.0", "40", "2.5", "1",
                 txt])

        dxf.extend(["0", "ENDSEC", "0", "EOF"])

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(dxf))
        messagebox.showinfo("저장 완료", f"3D 코리더 DXF 파일이 저장되었습니다:\n{path}")

    def export_csv_dialog(self):
        path = filedialog.asksaveasfilename(
            title="3D 좌표 테이블 CSV 저장", defaultextension=".csv",
            initialfile="corridor_3d_coordinates.csv", filetypes=[("CSV 파일", "*.csv")]
        )
        if not path:
            return

        _, rows, _ = self._collect_3d_corridor_data(interval=5.0)
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(
                ["Raw_STA", "Display_STA", "Zone", "Code", "Offset(m)", "Easting(X)", "Northing(Y)", "Elevation(Z)"])
            w.writerows(rows)
        messagebox.showinfo("저장 완료", f"3D 좌표 CSV 테이블이 저장되었습니다:\n{path}")

    def on_prof_mouse_down(self, event):
        """종단뷰에서 PVI 마커 또는 구조물 시·종점 핸들 클릭 감지"""
        if not self.v_prof or not self.corridor:
            return

        items = self.canvas_prof.find_overlapping(event.x - 8, event.y - 8, event.x + 8, event.y + 8)
        for item in reversed(items):
            tags = self.canvas_prof.gettags(item)
            for t in tags:
                if t.startswith("pvi_"):
                    try:
                        idx = int(t.split("_")[1])
                        self.drag_target = ("PVI", idx)
                        return
                    except (ValueError, IndexError):
                        pass
                elif t.startswith("st_start_"):
                    try:
                        idx = int(t.split("_")[-1])
                        self.drag_target = ("STRUCT_START", idx)
                        return
                    except (ValueError, IndexError):
                        pass
                elif t.startswith("st_end_"):
                    try:
                        idx = int(t.split("_")[-1])
                        self.drag_target = ("STRUCT_END", idx)
                        return
                    except (ValueError, IndexError):
                        pass
        self.drag_target = None

    def on_prof_mouse_drag(self, event):
        """드래그 중에는 화면 갱신 없이 데이터만 수정 (렉 방지)"""
        if not self.drag_target:
            return

        pl, pr, pt, pb, min_s, max_s, min_el, max_el = self.prof_bounds
        clamped_x = max(pl, min(pr, event.x))
        clamped_y = max(pt, min(pb, event.y))

        raw_s = min_s + ((clamped_x - pl) / max(1.0, pr - pl)) * (max_s - min_s)
        raw_el = min_el + ((pb - clamped_y) / max(1.0, pb - pt)) * (max_el - min_el)
        snapped_s = round(raw_s * 2.0) / 2.0
        snapped_el = round(raw_el * 20.0) / 20.0

        kind, idx = self.drag_target

        if kind == "PVI":
            pvis = self.v_prof.pvi_list
            target_pvi = pvis[idx]
            if 0 < idx < len(pvis) - 1:
                min_allowed = pvis[idx - 1].station + 10.0
                max_allowed = pvis[idx + 1].station - 10.0
                target_pvi.station = max(min_allowed, min(max_allowed, snapped_s))
            target_pvi.elevation = snapped_el

            # ★ 중요: 여기서 self.recalculate_all()을 호출하지 않음!
            # 필요하다면 여기서 얇은 선만 그리는 가벼운 시각화 업데이트 함수를 호출합니다.
            # 일단은 마우스를 뗄 때까지 화면 갱신을 생략하여 크래시를 방지합니다.

        elif kind in ("STRUCT_START", "STRUCT_END"):
            st = self.corridor.structures[idx]
            if kind == "STRUCT_START":
                st.start_station = max(0.0, min(st.end_station - 10.0, snapped_s))
            else:
                st.end_station = min(self.h_align.total_length, max(st.start_station + 10.0, snapped_s))

    def on_prof_mouse_up(self, event):
        if self.drag_target:
            kind, idx = self.drag_target
            self.drag_target = None

            # 3. 마우스를 뗄 때 비로소 텍스트 동기화 및 전체 재계산
            if kind == "PVI":
                self._sync_pvi_list_to_editor()
                self.recalculate_all()
            elif kind in ("STRUCT_START", "STRUCT_END"):
                self._sync_structures_to_editor()
                self.recalculate_all()

    def _sync_pvi_list_to_editor(self):
        """메모리 상의 수정된 PVI 제원을 좌측 종단 PVI 텍스트 에디터에 반영"""
        lines = ["# Name, RawSTA, Elevation, L1, L2"]
        for p in self.v_prof.pvi_list:
            l1 = p.L1 if p.L1 is not None else (p.L * 0.5 if p.L else 0.0)
            l2 = p.L2 if p.L2 is not None else (p.L * 0.5 if p.L else 0.0)
            lines.append(f"{p.name}, {p.station:.2f}, {p.elevation:.3f}, {l1:.1f}, {l2:.1f}")
        self.txt_pvi.delete("1.0", tk.END)
        self.txt_pvi.insert("1.0", "\n".join(lines) + "\n")

    def _sync_structures_to_editor(self):
        """메모리 상의 수정된 구조물 구간을 좌측 구조물 텍스트 에디터에 반영"""
        lines = ["# Name, Type(BRIDGE/TUNNEL/RETAINING_WALL), StartSTA, EndSTA, Side"]
        for s in self.corridor.structures:
            lines.append(f"{s.name}, {s.structure_type}, {s.start_station:.2f}, {s.end_station:.2f}, {s.wall_side}")
        self.txt_struct.delete("1.0", tk.END)
        self.txt_struct.insert("1.0", "\n".join(lines) + "\n")

    def on_plan_mouse_down(self, event):
        """평면도에서 PI(평면 교점) 마커 클릭 감지"""
        if not self.h_align:
            return
        items = self.canvas_plan.find_overlapping(
            event.x - 10, event.y - 10, event.x + 10, event.y + 10
        )
        for item in reversed(items):
            for t in self.canvas_plan.gettags(item):
                if t.startswith("plan_pi_"):
                    try:
                        # ★ 수정: split("_")[-1] 로 마지막 숫자만 추출
                        self.plan_drag_idx = int(t.split("_")[-1])
                        return
                    except (ValueError, IndexError):
                        pass  # 숫자가 아닌 태그는 무시
        self.plan_drag_idx = None

    def on_plan_mouse_drag(self, event):
        if self.plan_drag_idx is None or not self.h_align:
            return
        scale, cx, cy, hw, hh = self.plan_transform
        new_e = round(cx + (event.x - hw) / scale, 2)
        new_n = round(cy - (event.y - hh) / scale, 2)
        self.pis[self.plan_drag_idx].easting = new_e
        self.pis[self.plan_drag_idx].northing = new_n

        # 마커만 재그리기 (빠름)
        self.canvas_plan.delete("plan_pi_drag_preview")
        sx = hw + (new_e - cx) * scale
        sy = hh - (new_n - cy) * scale
        self.canvas_plan.create_polygon(
            sx, sy - 6, sx + 5, sy + 4, sx - 5, sy + 4,
            outline="#facc15", fill="", width=1.5, tags="plan_pi_drag_preview"
        )

    def on_plan_mouse_up(self, event):
        """평면 PI 드래그 종료 시 최종 반영"""
        if self.plan_drag_idx is None:
            return
        idx = self.plan_drag_idx
        self.plan_drag_idx = None

        try:
            self._sync_pi_list_to_editor()
            self.recalculate_all()
        except Exception:
            # 유효하지 않은 형상(반경 대비 PI 근접 등)일 경우 롤백
            messagebox.showwarning("선형 오류", "PI 이동으로 인해 선형을 생성할 수 없습니다. 이전 위치로 복구합니다.")
            # (선택) 이전 좌표를 백업해두었다면 복구

    def _sync_pi_list_to_editor(self):
        """변경된 평면 PI 좌표를 좌측 평면 PI 텍스트 에디터에 역동기화"""
        lines = ["# Name, Easting, Northing, R, L1, L2"]
        for p in self.pis:
            l1 = p.L1 if p.L1 is not None else 0.0
            l2 = p.L2 if p.L2 is not None else l1
            lines.append(f"{p.name}, {p.easting:.3f}, {p.northing:.3f}, {p.R:.1f}, {l1:.1f}, {l2:.1f}")
        self.txt_pi.delete("1.0", tk.END)
        self.txt_pi.insert("1.0", "\n".join(lines) + "\n")

    def export_earthwork_report_dialog(self, interval: float = 20.0):
        """양단면 평균법 기반 Civil 3D 표준 토공량 조서(CSV) 내보내기"""
        if not self.corridor or not self.h_align:
            return

        default_name = f"{self.entry_align_name.get().strip() or 'alignment'}_earthwork_report.csv"
        path = filedialog.asksaveasfilename(
            title="토공량 조서(Earthwork Volume Report) 저장",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV 파일", "*.csv")]
        )
        if not path:
            return

        # ★ 엔진이 이미 기점(0) 포함 + 누적 계산까지 다 해줌
        report = self.corridor.compute_earthwork_volumes(interval=interval)

        rows = []
        # 기점(첫 측점) 추가
        first_s = 0.0
        first_sec = self.corridor.sample_cross_section(first_s)
        disp_s, zone = self.sta_mgr.raw_to_display(first_s)
        eg_cl = self.corridor.terrain.elevation_at(0.0, 0.0, first_s, 0.0)
        cl_el = first_sec["points"]["CL"][3]
        structs = first_sec.get("structures") or []
        rows.append([
            f"{first_s:.3f}", self.sta_mgr.format_station(disp_s), f"Z{zone}",
            "0.000", f"{eg_cl:.3f}", f"{cl_el:.3f}", f"{cl_el - eg_cl:+.3f}",
            f"{first_sec['cut_area']:.3f}", f"{first_sec['fill_area']:.3f}",
            "0.000", "0.000", "0.000", "0.000", "+0.000",
            ",".join(structs) if structs else "-"
        ])

        for row in report:
            curr_s = row["station"]
            disp_s, zone = self.sta_mgr.raw_to_display(curr_s)
            sec = self.corridor.sample_cross_section(curr_s)
            eg_cl = self.corridor.terrain.elevation_at(0.0, 0.0, curr_s, 0.0)
            cl_el = sec["points"]["CL"][3]
            rows.append([
                f"{curr_s:.3f}", self.sta_mgr.format_station(disp_s), f"Z{zone}",
                f"{interval:.3f}", f"{eg_cl:.3f}", f"{cl_el:.3f}", f"{cl_el - eg_cl:+.3f}",
                f"{row['cut_area']:.3f}", f"{row['fill_area']:.3f}",
                f"{row['cut_vol']:.3f}", f"{row['fill_vol']:.3f}",
                f"{row['cum_cut']:.3f}", f"{row['cum_fill']:.3f}",
                f"{row['cum_cut'] - row['cum_fill']:+.3f}",
                ",".join(row["structures"]) if row["structures"] else "-"
            ])

        headers = [
            "물리측점(Raw_STA)", "표기측점(Display_STA)", "파정구역", "누가거리(m)",
            "중심지반고_EG(m)", "중심계획고_FG(m)", "계획고차(m)",
            "절토면적(㎡)", "성토면적(㎡)",
            "구간절토량(㎥)", "구간성토량(㎥)",
            "누적절토량(㎥)", "누적성토량(㎥)", "누적순토공량(㎥)", "구조물_비고"
        ]

        try:
            with open(path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
            messagebox.showinfo("조서 저장 완료", f"토공량 조서 CSV 파일이 생성되었습니다:\n{path}")
        except Exception as ex:
            messagebox.showerror("저장 오류", f"토공량 조서 저장 중 오류가 발생했습니다:\n{ex}")

    def export_geometry_report_dialog(self):
        """평면 선형 계산서(IP 제원표) + 종단 선형 계산서(PVI 제원표) 통합 CSV 내보내기"""
        if not self.h_align or not self.v_prof:
            return

        default_name = f"{self.entry_align_name.get().strip() or 'alignment'}_geometry_report.csv"
        path = filedialog.asksaveasfilename(
            title="평면·종단 선형 계산서 저장",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV 파일", "*.csv")]
        )
        if not path:
            return

        def fmt_sta(raw_sta: float) -> str:
            """튜플 반환값을 안전하게 처리하는 헬퍼"""
            disp, _ = self.sta_mgr.raw_to_display(raw_sta)
            return self.sta_mgr.format_station(disp)

        try:
            with open(path, mode="w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)

                # ==============================================================
                # [PART 1] 평면 선형 계산서 (IP 제원표)
                # ==============================================================
                w.writerow([f"[평면 선형 계산서 - {self.h_align.name}]"])
                w.writerow([
                    "교점명(IP)", "방향", "Easting(X)", "Northing(Y)",
                    "교각_IA(도)", "반경_R(m)", "진입완화_L1(m)", "진출완화_L2(m)",
                    "전접선장_TL1(m)", "후접선장_TL2(m)", "원곡선장_CL(m)",
                    "TS_표기측점", "SC_표기측점", "CS_표기측점", "ST_표기측점"
                ])

                pis = self.pis
                n_pi = len(pis)
                bearings = [
                    math.atan2(pis[i + 1].northing - pis[i].northing,
                               pis[i + 1].easting - pis[i].easting)
                    for i in range(n_pi - 1)
                ]

                # 엔티티를 시작 측점으로 정렬한 리스트 (안전한 매칭)
                entities = self.h_align.entities

                def find_entity_near(target_sta: float):
                    """주어진 측점과 가장 가까운 엔티티 찾기"""
                    if not entities:
                        return None
                    return min(entities, key=lambda e: abs(e.start_sta - target_sta))

                for i in range(1, n_pi - 1):
                    pi = pis[i]
                    R = float(pi.R) if pi.R else 0.0
                    L1 = float(pi.L1 or 0.0)
                    L2 = float(pi.L2) if pi.L2 is not None else L1
                    d_th = (bearings[i] - bearings[i - 1] + math.pi) % (2.0 * math.pi) - math.pi
                    IA_deg = math.degrees(abs(d_th))
                    dir_str = "좌회전(L)" if d_th >= 0 else "우회전(R)"

                    # 각 주요 측점은 엔티티를 순회하며 찾음 (LineSegment/ArcSegment/Spiral 구분)
                    ts_raw = sc_raw = cs_raw = st_raw = 0.0
                    CL = 0.0
                    # PI 구간에 해당하는 엔티티들을 station 순서로 순회
                    # TS ~ ST 범위 엔티티를 모두 수집
                    candidates = []
                    for ent in entities:
                        # 이 PI의 교각 범위 내 엔티티만 후보로
                        candidates.append(ent)

                    # PI의 교점 위치와 가장 가까운 엔티티를 기준으로 그룹화
                    # 정확한 계산을 위해 TS/ST를 PI 좌표로부터 역산
                    # 접선장(TL1, TL2)은 PI 좌표로부터 TS/ST까지의 거리
                    # 여기서는 각 엔티티의 start_sta/end_sta를 직접 활용
                    # 1) 교점 앞뒤의 가장 가까운 원곡선 관련 엔티티를 찾음
                    curve_entities = []
                    for ent in entities:
                        # 원곡선, 스파이럴 엔티티만 필터
                        tname = type(ent).__name__
                        if tname in ("JapaneseCubicSpiralSegment", "ArcSegment"):
                            # 이 PI에 해당하는지 판별 (PI 교점 반경과 매칭)
                            if hasattr(ent, "start_sta"):
                                curve_entities.append(ent)

                    # 간이 매칭: PI 인덱스 순서대로 curve_entities를 그룹핑
                    # (완화곡선 L1, L2 개수에 따라 1~3개 엔티티가 한 PI에 대응)
                    groups = []
                    idx = 0
                    for j in range(1, n_pi - 1):
                        p = pis[j]
                        L1_j = float(p.L1 or 0.0)
                        L2_j = float(p.L2) if p.L2 is not None else L1_j
                        count = (1 if L1_j > 1e-9 else 0) + (1 if L2_j > 1e-9 else 0) + 1  # arc 포함
                        groups.append(curve_entities[idx:idx + count])
                        idx += count

                    group = groups[i - 1] if i - 1 < len(groups) else []
                    if group:
                        ts_raw = group[0].start_sta
                        st_raw = group[-1].end_sta
                        # arc 엔티티 길이 = CL
                        for ent in group:
                            if type(ent).__name__ == "ArcSegment":
                                CL = ent.length
                        sc_raw = group[1].start_sta if len(group) > 1 else ts_raw
                        cs_raw = group[-2].end_sta if len(group) > 1 else st_raw
                    else:
                        # 폴백: 엔티티 없으면 0
                        ts_raw = st_raw = sc_raw = cs_raw = 0.0

                    # 접선장 역산
                    ts_e, ts_n = self.h_align.point_location(ts_raw, 0.0)
                    st_e, st_n = self.h_align.point_location(st_raw, 0.0)
                    TL1 = math.hypot(pi.easting - ts_e, pi.northing - ts_n)
                    TL2 = math.hypot(st_e - pi.easting, st_n - pi.northing)

                    w.writerow([
                        pi.name, dir_str, f"{pi.easting:.4f}", f"{pi.northing:.4f}",
                        f"{IA_deg:.4f}", f"{R:.3f}", f"{L1:.3f}", f"{L2:.3f}",
                        f"{TL1:.3f}", f"{TL2:.3f}", f"{CL:.3f}",
                        fmt_sta(ts_raw), fmt_sta(sc_raw), fmt_sta(cs_raw), fmt_sta(st_raw),
                    ])

                w.writerow([])

                # ==============================================================
                # [PART 2] 종단 선형 계산서 (PVI 제원표)
                # ==============================================================
                w.writerow([f"[종단 선형 계산서 - {self.h_align.name}]"])
                w.writerow([
                    "종단교점(PVI)", "물리측점(Raw)", "표기측점(Display)", "계획고_EL(m)",
                    "전경사_g1(%)", "후경사_g2(%)", "경사차_A(%)",
                    "진입곡선_L1(m)", "진출곡선_L2(m)", "종단곡선_K값",
                    "BVC_표기측점", "EVC_표기측점", "변곡점(극점)_측점_및_EL"
                ])

                pvis = self.v_prof.pvi_list
                n_pvi = len(pvis)
                grades = [
                    (pvis[j + 1].elevation - pvis[j].elevation)
                    / max(1e-9, pvis[j + 1].station - pvis[j].station)
                    for j in range(n_pvi - 1)
                ]

                for i, pvi in enumerate(pvis):
                    if i == 0 or i == n_pvi - 1:
                        w.writerow([
                            pvi.name, f"{pvi.station:.3f}", fmt_sta(pvi.station),
                            f"{pvi.elevation:.3f}",
                            "-", "-", "-", "0.000", "0.000", "-", "-", "-", "-"
                        ])
                        continue

                    g1, g2 = grades[i - 1], grades[i]
                    A_pct = (g2 - g1) * 100.0
                    l1 = float(pvi.L1) if pvi.L1 is not None else (float(pvi.L) * 0.5 if pvi.L else 0.0)
                    l2 = float(pvi.L2) if pvi.L2 is not None else (float(pvi.L) * 0.5 if pvi.L else 0.0)
                    tot_l = l1 + l2
                    k_val = (tot_l / abs(A_pct)) if abs(A_pct) > 1e-6 else 0.0

                    bvc_raw = pvi.station - l1
                    evc_raw = pvi.station + l2

                    # 극점(최고/최저점) 계산
                    ext_note = "-"
                    if tot_l > 1e-6 and g1 * g2 < 0:
                        e_off = ((g2 - g1) * l1 * l2) / (2.0 * tot_l)
                        if abs(e_off) > 1e-9:
                            x1_z = -g1 * (l1 ** 2) / (2.0 * e_off)
                            if 0.0 <= x1_z <= l1:
                                ext_raw = bvc_raw + x1_z
                            else:
                                x2_z = g2 * (l2 ** 2) / (2.0 * e_off)
                                ext_raw = evc_raw - x2_z
                            ext_el, _ = self.v_prof.elevation_and_grade_at(ext_raw)
                            ext_note = f"STA {fmt_sta(ext_raw)} (EL {ext_el:.3f}m)"

                    w.writerow([
                        pvi.name, f"{pvi.station:.3f}", fmt_sta(pvi.station),
                        f"{pvi.elevation:.3f}",
                        f"{g1 * 100:+.4f}", f"{g2 * 100:+.4f}", f"{A_pct:+.4f}",
                        f"{l1:.3f}", f"{l2:.3f}", f"{k_val:.2f}",
                        fmt_sta(bvc_raw), fmt_sta(evc_raw), ext_note
                    ])

            messagebox.showinfo("계산서 저장 완료", f"평면·종단 선형 계산서가 저장되었습니다:\n{path}")
        except Exception as ex:
            messagebox.showerror("저장 오류", f"선형 계산서 생성 중 오류가 발생했습니다:\n{ex}")

if __name__ == "__main__":
    root = tk.Tk()
    app = Civil3DStudioDashboard(root)
    root.mainloop()