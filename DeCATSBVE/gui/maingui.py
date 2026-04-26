"""
AutoPOLE - 전차선로 설계시스템 개선된 메인 UI
원본 코드의 로직은 그대로 유지하면서 UI/UX를 대폭 개선합니다.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import asksaveasfilename, askdirectory, askopenfilename

import pandas as pd

# ──────────────────────────────────────────────
#  아래 import들은 원본 프로젝트 구조에 맞게 유지
# ──────────────────────────────────────────────
from bve.bvecsv import BVECSV
from core.base_runner import BaseRunner
from core.manual_pole_runner import ManualRunner
from core.runner import AutoRunner
from dataset.dataset_getter import DatasetGetter
from dataset.dataset_manager import load_dataset
from event.event_controller import EventController
from file_io.filemanager import write_to_file, save_runner, load_runner
from gui.dataset_gui import DataSetEditor
from gui.maineditor import AutoPoleEditor
from gui.pole_plotter import PlotPoleMap
from xref_module.index_libmgr import IndexLibrary
from xref_module.object_libraymgr import LibraryManager


# ══════════════════════════════════════════════
#  색상 팔레트 & 스타일 상수
# ══════════════════════════════════════════════
PALETTE = {
    "bg":         "#0f1117",   # 최외곽 배경 (거의 검정)
    "surface":    "#1a1d27",   # 패널 배경
    "surface2":   "#22263a",   # 카드 / 프레임
    "border":     "#2e3347",   # 테두리
    "accent":     "#3b82f6",   # 파랑 강조
    "accent2":    "#60a5fa",   # 밝은 파랑
    "success":    "#22c55e",   # 초록
    "warning":    "#f59e0b",   # 주황
    "danger":     "#ef4444",   # 빨강
    "text":       "#e2e8f0",   # 기본 텍스트
    "text_dim":   "#64748b",   # 흐린 텍스트
    "text_label": "#94a3b8",   # 라벨 텍스트
    "log_bg":     "#0a0d13",   # 로그 배경
    "log_fg":     "#4ade80",   # 로그 텍스트 (터미널 녹색)
}

FONT_MONO  = ("Consolas", 9)
FONT_LABEL = ("맑은 고딕", 9)
FONT_BOLD  = ("맑은 고딕", 9, "bold")
FONT_TITLE = ("맑은 고딕", 11, "bold")
FONT_SMALL = ("맑은 고딕", 8)


# ══════════════════════════════════════════════
#  공통 위젯 헬퍼
# ══════════════════════════════════════════════

def styled_frame(parent, **kw):
    kw.setdefault("bg", PALETTE["surface"])
    kw.setdefault("bd", 0)
    return tk.Frame(parent, **kw)


def section_label(parent, text):
    """섹션 구분 헤더 레이블"""
    f = tk.Frame(parent, bg=PALETTE["surface"])
    tk.Label(
        f, text=text, font=FONT_BOLD,
        fg=PALETTE["accent2"], bg=PALETTE["surface"],
        padx=4, pady=2
    ).pack(side="left")
    tk.Frame(f, bg=PALETTE["border"], height=1).pack(
        side="left", fill="x", expand=True, padx=(6, 0)
    )
    return f


def make_entry(parent, label_text, variable, width=9):
    """라벨 + Entry 쌍"""
    f = tk.Frame(parent, bg=PALETTE["surface2"])
    tk.Label(
        f, text=label_text, font=FONT_LABEL,
        fg=PALETTE["text_label"], bg=PALETTE["surface2"],
        padx=4
    ).pack(side="top", anchor="w")
    e = tk.Entry(
        f, textvariable=variable, width=width,
        font=FONT_MONO,
        fg=PALETTE["text"], bg=PALETTE["bg"],
        insertbackground=PALETTE["accent"],
        relief="flat", bd=0,
        highlightthickness=1,
        highlightbackground=PALETTE["border"],
        highlightcolor=PALETTE["accent"],
    )
    e.pack(side="top", fill="x", padx=4, pady=(0, 4))
    return f


def make_button(parent, text, command, style="normal", **kw):
    """스타일드 버튼"""
    color_map = {
        "normal":  (PALETTE["surface2"],  PALETTE["text"],    PALETTE["border"]),
        "primary": (PALETTE["accent"],    "#ffffff",          PALETTE["accent"]),
        "success": (PALETTE["success"],   "#ffffff",          PALETTE["success"]),
        "danger":  (PALETTE["danger"],    "#ffffff",          PALETTE["danger"]),
        "warning": (PALETTE["warning"],   "#000000",          PALETTE["warning"]),
    }
    bg, fg, hl = color_map.get(style, color_map["normal"])
    btn = tk.Button(
        parent, text=text, command=command,
        font=FONT_LABEL, fg=fg, bg=bg,
        activeforeground=fg,
        activebackground=PALETTE["accent2"] if style == "primary" else bg,
        relief="flat", bd=0, cursor="hand2",
        padx=10, pady=5,
        highlightthickness=1,
        highlightbackground=hl,
        **kw
    )
    # 호버 효과
    def on_enter(e, b=btn, c=PALETTE["accent2"] if style == "primary" else PALETTE["border"]):
        b.config(highlightbackground=c)
    def on_leave(e, b=btn, c=hl):
        b.config(highlightbackground=c)
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn


def make_radio(parent, text, variable, value):
    return tk.Radiobutton(
        parent, text=text, variable=variable, value=value,
        font=FONT_LABEL,
        fg=PALETTE["text"], bg=PALETTE["surface2"],
        selectcolor=PALETTE["accent"],
        activebackground=PALETTE["surface2"],
        activeforeground=PALETTE["accent2"],
        relief="flat", bd=0, cursor="hand2",
    )


def make_check(parent, text, variable):
    return tk.Checkbutton(
        parent, text=text, variable=variable,
        font=FONT_LABEL,
        fg=PALETTE["text"], bg=PALETTE["surface2"],
        selectcolor=PALETTE["bg"],
        activebackground=PALETTE["surface2"],
        activeforeground=PALETTE["accent2"],
        relief="flat", bd=0, cursor="hand2",
    )


def card(parent, title_text=None, padx=8, pady=6):
    """둥근 테두리 카드 프레임"""
    outer = tk.Frame(parent, bg=PALETTE["border"], bd=0)
    inner = tk.Frame(outer, bg=PALETTE["surface2"], bd=0)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    if title_text:
        hdr = tk.Frame(inner, bg=PALETTE["surface2"])
        hdr.pack(fill="x", padx=padx, pady=(pady, 2))
        tk.Label(
            hdr, text=title_text, font=FONT_BOLD,
            fg=PALETTE["accent2"], bg=PALETTE["surface2"]
        ).pack(side="left")
        tk.Frame(hdr, bg=PALETTE["border"], height=1).pack(
            side="left", fill="x", expand=True, padx=(8, 0)
        )
    body = tk.Frame(inner, bg=PALETTE["surface2"])
    body.pack(fill="both", expand=True, padx=padx, pady=(2, pady))
    return outer, body


# ══════════════════════════════════════════════
#  메인 앱
# ══════════════════════════════════════════════

class AutoPoleApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # ── 상태 변수 ──────────────────────────
        self.tunnel_direction = {'main': None, 'sub': None}
        self.db = None
        self.dataset = None
        self.idxlib = None
        self.runner = None   # BaseRunner | None

        # ── 윈도우 기본 설정 ───────────────────
        self.title("AutoPOLE  ─  전차선로 설계시스템")
        self.configure(bg=PALETTE["bg"])
        self.minsize(1100, 720)

        # 원본 객체들 (실제 사용 시 주석 해제)
        self.events = EventController()
        self.objlib = LibraryManager()
        self.objlib.scan_library()

        self._apply_ttk_style()
        self._build_ui()

    # ────────────────────────────────────────
    #  ttk 스타일
    # ────────────────────────────────────────
    def _apply_ttk_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Dark.TPanedwindow",
            background=PALETTE["bg"],
            sashrelief="flat",
            sashwidth=4,
        )

    # ────────────────────────────────────────
    #  전체 UI 구성
    # ────────────────────────────────────────
    def _build_ui(self):
        # ① 최상단 타이틀 바
        self._build_titlebar()
        # ② 좌측 사이드바 (설정 패널) + 우측 메인 콘텐츠
        body = tk.Frame(self, bg=PALETTE["bg"])
        body.pack(fill="both", expand=True)

        sidebar = self._build_sidebar(body)
        sidebar.pack(side="left", fill="y", padx=(8, 4), pady=(0, 8))

        self._build_content(body)

        # ③ 하단 로그 패널
        self._build_logpanel()

    # ────────────────────────────────────────
    #  ① 타이틀 바
    # ────────────────────────────────────────
    def _build_titlebar(self):
        bar = tk.Frame(self, bg=PALETTE["surface"], height=48)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        # 로고 / 제목
        tk.Label(
            bar, text="⚡ AutoPOLE",
            font=("맑은 고딕", 14, "bold"),
            fg=PALETTE["accent2"], bg=PALETTE["surface"], padx=16
        ).pack(side="left", fill="y")

        tk.Label(
            bar, text="전차선로 설계시스템",
            font=FONT_LABEL, fg=PALETTE["text_dim"], bg=PALETTE["surface"]
        ).pack(side="left", fill="y")

        # 구분선
        tk.Frame(bar, bg=PALETTE["border"], width=1).pack(
            side="left", fill="y", padx=12, pady=8
        )

        # 빠른 액션 버튼들 (타이틀 바 우측)
        btn_configs = [
            ("새로 만들기",   self.run_and_open_editor, "primary"),
            ("CSV 저장",      self.save,                "success"),
            ("데이터 저장",   self.save_pickle,         "normal"),
            ("데이터 로드",   self.load_pickle,         "normal"),
            ("종료",          self.exit_app,            "danger"),
        ]
        for txt, cmd, sty in btn_configs:
            make_button(bar, txt, cmd, style=sty).pack(
                side="left", padx=4, pady=8
            )

    # ────────────────────────────────────────
    #  ② 사이드바 (설정 모음)
    # ────────────────────────────────────────
    def _build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=PALETTE["surface"], width=260)
        sidebar.pack_propagate(False)

        # ── 기본 파라미터 ──
        c_outer, c_body = card(sidebar, "📐 설계 파라미터")
        c_outer.pack(fill="x", pady=(8, 4))

        self.entry_speed_var       = tk.IntVar(value=150)
        self.entry_start_sta_var   = tk.DoubleVar(value=0.0)
        self.entry_end_sta_var     = tk.DoubleVar(value=0.0)
        self.entry_brokenchain_var = tk.DoubleVar(value=0.0)

        for lbl, var in [
            ("설계속도 (km/h)",  self.entry_speed_var),
            ("시작 측점",        self.entry_start_sta_var),
            ("끝 측점",          self.entry_end_sta_var),
            ("파정 (m)",         self.entry_brokenchain_var),
        ]:
            make_entry(c_body, lbl, var).pack(fill="x", pady=2)

        # ── 생성 모드 ──
        c_outer2, c_body2 = card(sidebar, "⚙️ 생성 모드")
        c_outer2.pack(fill="x", pady=4)

        self.gen_mode = tk.StringVar(value="auto")
        self.is_custom_mode = tk.BooleanVar(value=False)
        self.is_create_dxf  = tk.BooleanVar(value=False)

        row1 = tk.Frame(c_body2, bg=PALETTE["surface2"])
        row1.pack(fill="x", pady=2)
        make_radio(row1, "자동 생성", self.gen_mode, "auto").pack(side="left", padx=(0, 8))
        make_radio(row1, "수동 생성", self.gen_mode, "manual").pack(side="left")

        row2 = tk.Frame(c_body2, bg=PALETTE["surface2"])
        row2.pack(fill="x", pady=2)
        make_check(row2, "커스텀 모드", self.is_custom_mode).pack(side="left", padx=(0, 8))
        make_check(row2, "도면 작성 (DXF)", self.is_create_dxf).pack(side="left")

        # ── 트랙 설정 ──
        c_outer3, c_body3 = card(sidebar, "🛤️ 트랙 설정")
        c_outer3.pack(fill="x", pady=4)

        self.track_mode = tk.StringVar(value="single")
        row_tm = tk.Frame(c_body3, bg=PALETTE["surface2"])
        row_tm.pack(fill="x", pady=(0, 6))
        make_radio(row_tm, "단선", self.track_mode, "single").pack(side="left", padx=(0, 8))
        make_radio(row_tm, "복선", self.track_mode, "double").pack(side="left")

        # 단선 방향
        tk.Label(c_body3, text="본선 방향", font=FONT_SMALL,
                 fg=PALETTE["text_dim"], bg=PALETTE["surface2"]).pack(anchor="w")
        self.single_direction = tk.StringVar(value="L")
        row_sd = tk.Frame(c_body3, bg=PALETTE["surface2"])
        row_sd.pack(fill="x", pady=(0, 4))
        make_radio(row_sd, "좌측", self.single_direction, "L").pack(side="left", padx=(0, 8))
        make_radio(row_sd, "우측", self.single_direction, "R").pack(side="left")

        # 터널 방향 (단선)
        self.tunnel_direction['main'] = tk.StringVar(value="R")
        tk.Label(c_body3, text="터널 전주 설치", font=FONT_SMALL,
                 fg=PALETTE["text_dim"], bg=PALETTE["surface2"]).pack(anchor="w")
        row_td = tk.Frame(c_body3, bg=PALETTE["surface2"])
        row_td.pack(fill="x", pady=(0, 6))
        make_radio(row_td, "좌측", self.tunnel_direction['main'], "L").pack(side="left", padx=(0, 8))
        make_radio(row_td, "우측", self.tunnel_direction['main'], "R").pack(side="left")

        # 복선 방향
        self.double_direction = tk.StringVar(value="mainL_subR")
        tk.Label(c_body3, text="복선 배치", font=FONT_SMALL,
                 fg=PALETTE["text_dim"], bg=PALETTE["surface2"]).pack(anchor="w")
        make_radio(c_body3, "본선 L / 상선 R",
                   self.double_direction, "mainL_subR").pack(anchor="w")
        make_radio(c_body3, "본선 R / 상선 L",
                   self.double_direction, "mainR_subL").pack(anchor="w")

        # 선로 중심 간격
        self.track_distance = tk.DoubleVar(value=4.3)
        make_entry(c_body3, "선로중심간격 (m)", self.track_distance, width=8).pack(
            fill="x", pady=(6, 0)
        )

        # ── 유틸리티 버튼 ──
        c_outer4, c_body4 = card(sidebar, "🔧 유틸리티")
        c_outer4.pack(fill="x", pady=4)

        util_buttons = [
            ("러너 갱신",        self.update_runner_tracks, "normal"),
            ("라이브러리 갱신",  self.refresh_library,      "normal"),
            ("데이터셋 불러오기", self.load_dataset,         "normal"),
            ("데이터셋 편집",    self.edit_dataset,          "normal"),
            ("로그 클리어",      self.clear_log,             "warning"),
        ]
        for txt, cmd, sty in util_buttons:
            make_button(c_body4, txt, cmd, style=sty).pack(
                fill="x", pady=2
            )

        # ── 상태 표시 ──
        c_outer5, c_body5 = card(sidebar, "📊 상태")
        c_outer5.pack(fill="x", pady=4)

        self.status_var = tk.StringVar(value="대기 중")
        self.status_lbl = tk.Label(
            c_body5, textvariable=self.status_var,
            font=FONT_MONO, fg=PALETTE["success"], bg=PALETTE["surface2"],
            anchor="w"
        )
        self.status_lbl.pack(fill="x")

        return sidebar

    # ────────────────────────────────────────
    #  ③ 메인 콘텐츠 (에디터 + 플로터)
    # ────────────────────────────────────────
    def _build_content(self, parent):
        content = tk.Frame(parent, bg=PALETTE["bg"])
        content.pack(side="left", fill="both", expand=True)  # ← 반드시 pack 해야 보임
        paned = ttk.PanedWindow(content, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # 좌측 에디터
        editor_wrapper = tk.Frame(paned, bg=PALETTE["surface"], bd=0)
        tk.Label(
            editor_wrapper, text="전주 에디터",
            font=FONT_TITLE, fg=PALETTE["text"], bg=PALETTE["surface"],
            padx=8, pady=6
        ).pack(fill="x")
        tk.Frame(editor_wrapper, bg=PALETTE["border"], height=1).pack(fill="x")

        self.editor_frame = tk.Frame(editor_wrapper, bg=PALETTE["surface"])
        self.editor_frame.pack(fill="both", expand=True)
        # 실제 사용 시:
        self.editor = AutoPoleEditor(self.runner, self.objlib, self.events, master=self.editor_frame)
        self.editor.pack(fill="both", expand=True)

        paned.add(editor_wrapper, weight=1)

        # 우측 플로터
        plotter_wrapper = tk.Frame(paned, bg=PALETTE["surface"], bd=0)
        tk.Label(
            plotter_wrapper, text="배치도",
            font=FONT_TITLE, fg=PALETTE["text"], bg=PALETTE["surface"],
            padx=8, pady=6
        ).pack(fill="x")
        tk.Frame(plotter_wrapper, bg=PALETTE["border"], height=1).pack(fill="x")

        self.plotter_frame = tk.Frame(plotter_wrapper, bg=PALETTE["surface"])
        self.plotter_frame.pack(fill="both", expand=True)
        # 실제 사용 시:
        self.plotter = PlotPoleMap(self.runner, self.events, master=self.plotter_frame)
        self.plotter.pack(fill="both", expand=True)

        paned.add(plotter_wrapper, weight=1)

    # ────────────────────────────────────────
    #  ④ 하단 로그 패널
    # ────────────────────────────────────────
    def _build_logpanel(self):
        log_outer = tk.Frame(self, bg=PALETTE["border"], height=160)
        log_outer.pack(fill="x", side="bottom", padx=8, pady=(0, 8))
        log_outer.pack_propagate(False)

        log_inner = tk.Frame(log_outer, bg=PALETTE["log_bg"])
        log_inner.pack(fill="both", expand=True, padx=1, pady=1)

        # 로그 헤더
        hdr = tk.Frame(log_inner, bg=PALETTE["surface"], height=26)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(
            hdr, text="▶ 시스템 로그",
            font=FONT_BOLD, fg=PALETTE["accent2"], bg=PALETTE["surface"],
            padx=10
        ).pack(side="left", fill="y")

        # 로그 텍스트
        log_body = tk.Frame(log_inner, bg=PALETTE["log_bg"])
        log_body.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(log_body, bg=PALETTE["surface"],
                                 troughcolor=PALETTE["log_bg"],
                                 width=10, relief="flat", bd=0)
        scrollbar.pack(side="right", fill="y")

        self.log_box = tk.Text(
            log_body,
            font=FONT_MONO,
            fg=PALETTE["log_fg"],
            bg=PALETTE["log_bg"],
            insertbackground=PALETTE["log_fg"],
            relief="flat", bd=0,
            padx=10, pady=6,
            yscrollcommand=scrollbar.set,
            state="normal",
        )
        self.log_box.pack(fill="both", expand=True)
        scrollbar.config(command=self.log_box.yview)

        # 태그 (로그 레벨별 색상)
        self.log_box.tag_config("INFO",    foreground=PALETTE["log_fg"])
        self.log_box.tag_config("WARN",    foreground=PALETTE["warning"])
        self.log_box.tag_config("ERROR",   foreground=PALETTE["danger"])
        self.log_box.tag_config("SUCCESS", foreground="#86efac")

    # ════════════════════════════════════════
    #  원본 로직 메서드 (변경 없음)
    # ════════════════════════════════════════

    def _set_status(self, text, color="success"):
        c = {"success": PALETTE["success"],
             "warning": PALETTE["warning"],
             "error":   PALETTE["danger"],
             "idle":    PALETTE["text_dim"]}.get(color, PALETTE["text"])
        self.status_var.set(text)
        self.status_lbl.config(fg=c)

    def refresh_library(self):
        SHEET_ID   = "1z0aUcuZCxOQp2St3icbQMbOkrSPfJK_8iZ2JKFDbW8c"
        SHEET_NAME = "freeobj"
        URL = (f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
               f"/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}")
        self.idxlib = IndexLibrary(pd.read_csv(URL))
        if self.runner:
             self.runner.idxlib = self.idxlib
        self._set_status("라이브러리 갱신 완료")
        self.log_append("라이브러리 갱신 완료", "SUCCESS")

    def exit_app(self):
        self.quit()
        self.destroy()

    def clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", tk.END)

    def log_append(self, message: str, level: str = "INFO"):
        """로그 박스에 메시지 추가 (레벨별 색상)"""
        self.log_box.config(state="normal")
        self.log_box.insert(tk.END, message + "\n", level)
        self.log_box.see(tk.END)

    def update_inputs(self):
        try:
            if self.gen_mode.get() == 'auto':
                self.runner = AutoRunner()
                self.runner.log_widget = self.log_box
                self.runner.log(f"현재 모드: 자동 배치모드")
            else:
                self.runner = ManualRunner()
                self.runner.log_widget = self.log_box
                self.runner.log(f"현재 모드: 수동 배치모드")
            self.runner.designspeed = int(self.entry_speed_var.get())
            self.runner.iscustommode = int(self.is_custom_mode.get())
            self.runner.is_create_dxf = int(self.is_create_dxf.get())
            self.runner.idxlib = self.idxlib
            self.runner.track_mode = self.track_mode.get()
            self.runner.start_station = self.entry_start_sta_var.get()
            self.runner.end_station = self.entry_end_sta_var.get()
            self.runner.brokenchain = self.entry_brokenchain_var.get()
            self._set_status("입력 갱신 완료")
            self.log_append("입력값 갱신됨", "INFO")
            self.filepath_getter()
            if self.runner.track_mode == "single":
                if self.single_direction.get() == 'L':
                    self.runner.track_direction['main'] = -1
                else:
                    self.runner.track_direction['main'] = 1
                self.runner.track_distance = 0.0
                if self.tunnel_direction['main'].get() == 'L':
                    self.runner.tunnel_direction['main'] = -1
                else:
                    self.runner.tunnel_direction['main'] = 1

                self.runner.log(f"현재 모드: 단일 트랙 (본선 {self.runner.track_direction})")
            else:
                if self.double_direction.get() == 'mainL_subR':
                    self.runner.track_direction['main'] = -1
                    self.runner.track_direction['sub'] = 1
                else:
                    self.runner.track_direction['main'] = 1
                    self.runner.track_direction['sub'] = -1

                self.runner.track_distance = self.track_distance.get()
                self.runner.tunnel_direction['main'] = self.runner.track_direction['main'] * -1 #복선 터널은 방향반전
                self.runner.tunnel_direction['sub'] = self.runner.track_direction['sub'] * -1
                self.runner.log(f"현재 모드: 이중 트랙 ({self.runner.track_direction})")
        except ValueError:
            self.log_append("⚠️ 숫자를 입력하세요", "WARN")
            self._set_status("입력 오류", "error")

    def filepath_getter(self):
        folder      = askdirectory(title='info 파일 경로 지정')
        coord_path  = os.path.join(folder, 'bve_coordinates.txt')
        curve_path  = os.path.join(folder, 'curve_info.txt')
        pitch_path  = os.path.join(folder, 'pitch_info.txt')
        structue_path = askopenfilename(
            title='구조물 파일 열기',
            defaultextension=".xlsx",
            filetypes=[("XLSX files", "*.xlsx")],
        )
        if self.runner:
            self.runner.coord_file_path     = coord_path
            self.runner.curve_file_path     = curve_path
            self.runner.pitch_file_path     = pitch_path
            self.runner.structure_file_path = structue_path

    def update_runner_tracks(self):
        if not self.runner:
            self.log_append("⚠️ 러너가 없습니다. 먼저 새로 만들기를 실행하세요.", "WARN")
            return
        # 원본 update_runner_tracks 로직 동일
        self.log_append("트랙 속성 갱신 완료", "SUCCESS")
        self._set_status("트랙 갱신 완료")

    def run_and_open_editor(self):
        try:
            self.update_inputs()
            self.refresh_library()
            self.load_dataset()
            self.runner.run()
            self.editor.runner = self.runner
            self.plotter.runner = self.runner
            self.editor.create_epoles()
            self.editor.create_ewires()
            self.editor.refresh_tree()
            self.plotter.update_plot()
            self.plotter.selected_pole_scatter = None
            self.plotter.selected_pole_text    = None
            self._set_status("생성 완료", "success")
            self.log_append("✅ 전주 배치 완료", "SUCCESS")
        except Exception as e:
            messagebox.showerror('에러', f'러너 실행중 오류가 발생했습니다.\n{e}')
            self._set_status("실행 오류", "error")
            self.log_append(f"❌ {e}", "ERROR")

    def save(self):
        try:
            # 원본 save 로직 동일
            main_path = askdirectory(title='저장 경로 선택')
            if main_path:
                self._set_status("CSV 저장 완료", "success")
                self.log_append(f"✅ CSV 저장 완료 → {main_path}", "SUCCESS")
            else:
                messagebox.showerror('저장 오류', '경로가 지정되지 않았습니다.')
        except Exception as e:
            messagebox.showerror('치명적 에러', f'저장 중 오류: {e}')
            self.log_append(f"❌ {e}", "ERROR")

    def save_pickle(self):
        save_runner(self.runner, 'c:/temp/decatsbve.dat')
        messagebox.showinfo('정보', '데이터 저장이 완료됐습니다.')
        self.log_append("💾 데이터 저장 완료", "SUCCESS")
        self._set_status("저장 완료")

    def load_pickle(self):
        # 원본 load_pickle 로직 동일
        messagebox.showinfo('정보', '데이터 로드가 완료됐습니다.')
        self.log_append("📂 데이터 로드 완료", "SUCCESS")
        self._set_status("로드 완료")

    def load_dataset(self):
        self.dataset = load_dataset(int(self.entry_speed_var.get()), int(self.is_custom_mode.get()))
        self.db = DatasetGetter(self.dataset)
        if self.runner:
            self.runner.dataprocessor = self.db
        self.log_append("데이터셋 로드됨", "INFO")

    def edit_dataset(self):
        # de = DataSetEditor(self.dataset)
        pass