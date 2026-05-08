import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont


# ── 색상 팔레트 ───────────────────────────────────────────────────────────
COLORS = {
    "bg":          "#1C1C1E",   # 배경 (다크 차콜)
    "panel":       "#2C2C2E",   # 패널 배경
    "surface":     "#3A3A3C",   # 입력 필드 배경
    "border":      "#48484A",   # 테두리
    "accent":      "#0A84FF",   # 포인트 (애플 블루)
    "accent_dim":  "#0060D0",   # 버튼 호버
    "danger":      "#FF453A",   # 종료 버튼
    "danger_dim":  "#CC3830",
    "text":        "#FFFFFF",   # 기본 텍스트
    "text_muted":  "#8E8E93",   # 보조 텍스트
    "text_label":  "#AEAEB2",   # 레이블 텍스트
    "log_bg":      "#141416",   # 로그 배경
    "log_text":    "#32D74B",   # 로그 텍스트 (터미널 그린)
    "success":     "#30D158",   # 성공 강조
    "section":     "#0A84FF22", # 섹션 헤더 배경 (반투명)
}


class GUIWidget:
    def __init__(self, master, controller):
        self.master = master
        self.controller = controller
        self._setup_window()
        self._setup_style()

    # ── 창 기본 설정 ──────────────────────────────────────────────────────
    def _setup_window(self):
        self.master.configure(bg=COLORS["bg"])
        self.master.resizable(True, True)
        self.master.minsize(820, 640)

    # ── ttk 스타일 정의 ───────────────────────────────────────────────────
    def _setup_style(self):
        style = ttk.Style(self.master)
        style.theme_use("clam")

        # 공통 배경
        for widget in ("TFrame", "TLabelframe", "TLabelframe.Label"):
            style.configure(widget, background=COLORS["bg"], foreground=COLORS["text"])

        # 레이블
        style.configure("TLabel",
            background=COLORS["bg"],
            foreground=COLORS["text_label"],
            font=("Helvetica Neue", 10),
        )
        style.configure("SectionTitle.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["text_muted"],
            font=("Helvetica Neue", 9, "bold"),
        )
        style.configure("AppTitle.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["text"],
            font=("Helvetica Neue", 14, "bold"),
        )
        style.configure("AppSubtitle.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["text_muted"],
            font=("Helvetica Neue", 10),
        )

        # 입력 필드
        style.configure("TEntry",
            fieldbackground=COLORS["surface"],
            foreground=COLORS["text"],
            insertcolor=COLORS["text"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            font=("Helvetica Neue", 11),
            padding=(8, 6),
        )
        style.map("TEntry",
            bordercolor=[("focus", COLORS["accent"])],
            lightcolor=[("focus", COLORS["accent"])],
        )

        # 기본 버튼 (액션)
        style.configure("Action.TButton",
            background=COLORS["accent"],
            foreground=COLORS["text"],
            font=("Helvetica Neue", 10, "bold"),
            padding=(12, 8),
            borderwidth=0,
            relief="flat",
        )
        style.map("Action.TButton",
            background=[("active", COLORS["accent_dim"]), ("pressed", COLORS["accent_dim"])],
        )

        # 보조 버튼 (설정류)
        style.configure("Secondary.TButton",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=("Helvetica Neue", 10),
            padding=(12, 8),
            borderwidth=1,
            relief="flat",
        )
        style.map("Secondary.TButton",
            background=[("active", COLORS["border"]), ("pressed", COLORS["border"])],
        )

        # 종료 버튼
        style.configure("Danger.TButton",
            background=COLORS["danger"],
            foreground=COLORS["text"],
            font=("Helvetica Neue", 10, "bold"),
            padding=(12, 8),
            borderwidth=0,
            relief="flat",
        )
        style.map("Danger.TButton",
            background=[("active", COLORS["danger_dim"]), ("pressed", COLORS["danger_dim"])],
        )

        # 체크버튼
        style.configure("TCheckbutton",
            background=COLORS["bg"],
            foreground=COLORS["text_label"],
            font=("Helvetica Neue", 10),
        )
        style.map("TCheckbutton",
            background=[("active", COLORS["bg"])],
            foreground=[("active", COLORS["text"])],
        )

        # Separator
        style.configure("TSeparator", background=COLORS["border"])

    # ── 위젯 생성 (외부 호출 진입점) ──────────────────────────────────────
    def create_widgets(self):
        self._build_header()
        ttk.Separator(self.master, orient="horizontal").pack(fill="x", padx=0, pady=0)
        self._build_body()
        ttk.Separator(self.master, orient="horizontal").pack(fill="x", padx=0, pady=0)
        self._build_log()
        self.controller.set_logger(self.write_log)

    # ── 헤더 영역 ─────────────────────────────────────────────────────────
    def _build_header(self):
        header = tk.Frame(self.master, bg=COLORS["panel"], pady=14)
        header.pack(fill="x")

        tk.Label(
            header,
            text="표지판 생성 프로그램",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Helvetica Neue", 15, "bold"),
        ).pack(side="left", padx=20)

        tk.Label(
            header,
            text="Sign Generator v1.0",
            bg=COLORS["panel"],
            fg=COLORS["text_muted"],
            font=("Helvetica Neue", 10),
        ).pack(side="left", padx=4)

    # ── 본문 (설정 + 버튼) ────────────────────────────────────────────────
    def _build_body(self):
        body = tk.Frame(self.master, bg=COLORS["bg"])
        body.pack(fill="x", padx=20, pady=16)

        # 좌측: 측점 설정
        left = tk.Frame(body, bg=COLORS["bg"])
        left.pack(side="left", fill="both", expand=True)

        self._section_label(left, "📍 측점 설정")
        station_grid = tk.Frame(left, bg=COLORS["bg"])
        station_grid.pack(fill="x", pady=(6, 0))

        self.start_station_var = tk.DoubleVar(value=79500)
        self.end_station_var   = tk.DoubleVar(value=90158)
        self.brokenchain_var   = tk.DoubleVar(value=0.0)
        self.reverse_start_station_var = tk.DoubleVar(value=45683)
        self.start_index_var   = tk.IntVar(value=4025)

        self._field_row(station_grid, 0, "시작 측점",      self.start_station_var)
        self._field_row(station_grid, 1, "끝 측점",        self.end_station_var)
        self._field_row(station_grid, 2, "파정 값",        self.brokenchain_var)
        self._field_row(station_grid, 3, "역방향 시작 측점", self.reverse_start_station_var)
        self._field_row(station_grid, 4, "시작 인덱스",    self.start_index_var)

        # 구분선
        tk.Frame(body, bg=COLORS["border"], width=1).pack(
            side="left", fill="y", padx=20
        )

        # 우측: 옵션 + 작업
        right = tk.Frame(body, bg=COLORS["bg"])
        right.pack(side="left", fill="both")

        # ─ 옵션 ─
        self._section_label(right, "⚙️ 옵션")
        opt_frame = tk.Frame(right, bg=COLORS["bg"])
        opt_frame.pack(fill="x", pady=(6, 0))

        self.is_reverse_var    = tk.BooleanVar(value=False)
        self.is_brokenchain_var = tk.BooleanVar(value=False)

        chk1 = ttk.Checkbutton(opt_frame, text="역방향", variable=self.is_reverse_var)
        chk1.state(["!alternate"])
        chk1.pack(anchor="w", pady=3)

        chk2 = ttk.Checkbutton(opt_frame, text="파정 사용", variable=self.is_brokenchain_var)
        chk2.state(["!alternate"])
        chk2.pack(anchor="w", pady=3)

        # ─ 파일/경로 설정 ─
        tk.Frame(right, bg=COLORS["border"], height=1).pack(fill="x", pady=12)
        self._section_label(right, "📁 파일 및 경로")

        file_frame = tk.Frame(right, bg=COLORS["bg"])
        file_frame.pack(fill="x", pady=(6, 0))

        self._icon_button(file_frame, "대상 디렉터리 설정",    self.on_select_target_directory, "Secondary.TButton")
        self._icon_button(file_frame, "구조물 엑셀 파일 선택", self.on_select_excel,            "Secondary.TButton")
        self._icon_button(file_frame, "INFO 경로 선택",        self.on_select_infopath,         "Secondary.TButton")

        # ─ 고급 설정 ─
        tk.Frame(right, bg=COLORS["border"], height=1).pack(fill="x", pady=12)
        self._section_label(right, "🔧 고급 설정")

        adv_frame = tk.Frame(right, bg=COLORS["bg"])
        adv_frame.pack(fill="x", pady=(6, 0))

        self._icon_button(adv_frame, "선로 설정",   self.on_set_track,  "Secondary.TButton")
        self._icon_button(adv_frame, "오프셋 설정", self.on_set_offset, "Secondary.TButton")

        # ─ 실행 / 종료 ─
        tk.Frame(right, bg=COLORS["border"], height=1).pack(fill="x", pady=12)

        run_frame = tk.Frame(right, bg=COLORS["bg"])
        run_frame.pack(fill="x", pady=(0, 4))

        ttk.Button(
            run_frame,
            text="▶  작업 시작",
            style="Action.TButton",
            command=self.on_run,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            run_frame,
            text="종료",
            style="Danger.TButton",
            command=self.on_exit,
        ).pack(side="left")

    # ── 로그 영역 ─────────────────────────────────────────────────────────
    def _build_log(self):
        log_outer = tk.Frame(self.master, bg=COLORS["bg"])
        log_outer.pack(fill="both", expand=True, padx=20, pady=(12, 16))

        # 로그 헤더
        log_header = tk.Frame(log_outer, bg=COLORS["bg"])
        log_header.pack(fill="x", pady=(0, 6))

        tk.Label(
            log_header,
            text="CONSOLE OUTPUT",
            bg=COLORS["bg"],
            fg=COLORS["text_muted"],
            font=("Courier New", 9, "bold"),
        ).pack(side="left")

        # 로그 박스
        log_frame = tk.Frame(log_outer, bg=COLORS["log_bg"], bd=0,
                             highlightbackground=COLORS["border"],
                             highlightthickness=1)
        log_frame.pack(fill="both", expand=True)

        self.log_box = tk.Text(
            log_frame,
            bg=COLORS["log_bg"],
            fg=COLORS["log_text"],
            insertbackground=COLORS["log_text"],
            font=("Courier New", 10),
            bd=0,
            highlightthickness=0,
            relief="flat",
            padx=12,
            pady=10,
            wrap="word",
        )
        scroll = ttk.Scrollbar(log_frame, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=scroll.set)

        scroll.pack(side="right", fill="y")
        self.log_box.pack(fill="both", expand=True)

        self.write_log("▶ 프로그램이 시작되었습니다. 설정 후 [작업 시작]을 눌러주세요.")

    # ── 헬퍼: 섹션 레이블 ────────────────────────────────────────────────
    def _section_label(self, parent, text):
        tk.Label(
            parent,
            text=text,
            bg=COLORS["bg"],
            fg=COLORS["text_muted"],
            font=("Helvetica Neue", 9, "bold"),
        ).pack(anchor="w")

    # ── 헬퍼: 입력 행 (레이블 + 엔트리) ──────────────────────────────────
    def _field_row(self, parent, row, label_text, variable):
        tk.Label(
            parent,
            text=label_text,
            bg=COLORS["bg"],
            fg=COLORS["text_label"],
            font=("Helvetica Neue", 10),
            width=16,
            anchor="e",
        ).grid(row=row, column=0, sticky="e", padx=(0, 10), pady=4)

        entry = tk.Entry(
            parent,
            textvariable=variable,
            width=16,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            bd=0,
            font=("Courier New", 11),
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"],
            highlightthickness=1,
        )
        entry.grid(row=row, column=1, sticky="w", pady=4)

    # ── 헬퍼: 아이콘 버튼 ────────────────────────────────────────────────
    def _icon_button(self, parent, text, command, style):
        btn = ttk.Button(parent, text=text, style=style, command=command)
        btn.pack(fill="x", pady=3)

    # ── 로그 출력 ─────────────────────────────────────────────────────────
    def write_log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)

    # ── 이벤트 핸들러 ─────────────────────────────────────────────────────
    def on_select_excel(self):
        self.controller.set_structure_excelfile()

    def on_select_target_directory(self):
        self.controller.set_target_directory()

    def on_run(self):
        gui_state = {
            "start_station": self.start_station_var.get(),
            "end_station":   self.end_station_var.get(),
            "reverse_start": self.reverse_start_station_var.get(),
            "is_reverse":    self.is_reverse_var.get(),
            "isbrokenchain": self.is_brokenchain_var.get(),
            "brokenchain":   self.brokenchain_var.get(),
            "start_index":   self.start_index_var.get(),
        }
        self.controller.update_state(gui_state)
        self.controller.run()

    def on_exit(self):
        self.master.destroy()

    def on_set_offset(self):
        self.controller.set_offset()

    def on_set_track(self):
        self.controller.set_track()

    def on_select_infopath(self):
        self.controller.set_infopath()