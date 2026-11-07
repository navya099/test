"""좌측 컨트롤 / 우측 캔버스 / 이력 탭."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk,
)

from core.constants import (
    TunnelType, CornerStyle,
    HATCH_STYLE_SOLID, HATCH_STYLE_PATTERN, HATCH_STYLE_BOTH,
)
from ui.widgets import ParamRow


class ControlsPanel:
    """좌측 파라미터 편집 UI. app을 통해 콜백."""
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.rows: dict[str, ParamRow] = {}
        self.arch_rows: list[dict[str, ParamRow]] = []

        # ★ 스크롤 컨테이너 생성
        self._build_scroll_container()
        self._build()

    # ── 스크롤 컨테이너 ─────────────────────────────
    def _build_scroll_container(self):
        """
        parent 안에 Canvas + Scrollbar + 내부 Frame 구조 생성.
        self.scroll_frame 이 실제 컨트롤이 배치될 프레임.
        """
        outer = ttk.Frame(self.parent)
        outer.pack(fill="both", expand=True)
        outer.configure(width=300)  # 최소 폭 힌트

        # Canvas + Scrollbar
        canvas = tk.Canvas(outer, highlightthickness=0, bg="#f5f6f8")
        vbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vbar.set)

        vbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # 내부 프레임 (컨트롤이 여기에 배치됨)
        self.scroll_frame = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=self.scroll_frame,
                                             anchor="nw")

        # 내부 프레임 크기가 변하면 스크롤 영역 갱신
        def _on_frame_configure(_evt=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        # Canvas 폭에 맞춰 내부 프레임 폭 조정 (가로 스크롤 방지)
        def _on_canvas_configure(evt):
            canvas.itemconfigure(canvas_window, width=evt.width)

        self.scroll_frame.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        # 마우스 휠 바인딩 (Windows / macOS / Linux)
        def _on_mousewheel(evt):
            canvas.yview_scroll(int(-1 * (evt.delta / 120)), "units")

        def _on_mousewheel_linux(evt):
            if evt.num == 4:
                canvas.yview_scroll(-1, "units")
            elif evt.num == 5:
                canvas.yview_scroll(1, "units")

        # ★ 마우스가 캔버스 위에 있을 때만 스크롤
        def _bind_wheel(_evt):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel_linux)
            canvas.bind_all("<Button-5>", _on_mousewheel_linux)

        def _unbind_wheel(_evt):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)

        self._canvas = canvas
        self._vbar = vbar

    # ── 헤더 + 타입 라디오 ─────────────────────────
    def _build(self):
        parent = self.scroll_frame  # ★ 중요: scroll_frame 사용
        p = self.app.params

        #헤더
        header = ttk.Frame(parent)
        header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text="터널 단면 제원",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="슬라이더 또는 값을 직접 입력하세요.",
                  style="Info.TLabel").pack(anchor="w")

        #타입 라디오
        tf = ttk.Frame(parent)
        tf.pack(fill="x", pady=(0, 8))
        self.app.type_var = tk.StringVar(value=p.kind.value)
        for tt in TunnelType:
            ttk.Radiobutton(tf, text=tt.value, value=tt.value,
                            variable=self.app.type_var,
                            command=self.app.on_type_change
                            ).pack(side="left", padx=(0, 8))

        #그룹 3개
        self.shape_group = ttk.LabelFrame(parent, text="  단면 형상  ",
                                           padding=8)
        self.shape_group.pack(fill="x", pady=(0, 8))
        self.shape_group.columnconfigure(0, weight=1)

        # ★ 신규: 선로 그룹 (단면 형상 다음에)
        self.track_group = ttk.LabelFrame(parent, text="  선로 (트랙)  ",
                                          padding=8)
        self.track_group.pack(fill="x", pady=(0, 8))
        self.track_group.columnconfigure(0, weight=1)

        self.dim_group = ttk.LabelFrame(parent, text="  위치 · 치수  ",
                                         padding=8)
        self.dim_group.pack(fill="x", pady=(0, 8))
        self.dim_group.columnconfigure(0, weight=1)

        # ★ 안전박스 그룹
        self.safety_group = ttk.LabelFrame(parent, text="  안전박스  ",
                                            padding=8)
        self.safety_group.pack(fill="x", pady=(0, 8))
        self.safety_group.columnconfigure(0, weight=1)

        #스펙
        self.spec_label = ttk.Label(parent, text="",
                                     style="Spec.TLabel",
                                     anchor="w", justify="left")
        self.spec_label.pack(fill="x", pady=(0, 8))

        # 옵션
        opts = ttk.LabelFrame(parent, text="  옵션  ", padding=8)
        opts.pack(fill="x", pady=(0, 8))
        ttk.Checkbutton(opts, text="겹침 자동 방지 (슬라이더 조작 시)",
                        variable=self.app.auto_avoid_overlap
                        ).pack(anchor="w")
        hr = ttk.Frame(opts)
        hr.pack(fill="x", pady=(6, 0))
        ttk.Label(hr, text="DXF HATCH 스타일:",
                  style="Info.TLabel").pack(side="left", padx=(0, 8))
        for label, value in (("단색", HATCH_STYLE_SOLID),
                             ("ANSI31", HATCH_STYLE_PATTERN),
                             ("둘 다", HATCH_STYLE_BOTH)):
            ttk.Radiobutton(hr, text=label, value=value,
                            variable=self.app.hatch_style
                            ).pack(side="left", padx=(0, 6))

        self._build_action_buttons(parent)
        self.populate()

    # ── 액션 ───────────────────────────────────────
    def _build_action_buttons(self, parent):
        act = ttk.Frame(parent)
        act.pack(fill="x", pady=(0, 6))
        act.columnconfigure((0, 1), weight=1)

        self.app.btn_auto_fit = ttk.Button(
            act, text="⚡  FL 자동 맞춤  (Ctrl+F)",
            style="Accent.TButton", command=self.app.auto_fit_fl)
        self.app.btn_auto_fit.grid(row=0, column=0, columnspan=2,
                                    sticky="ew", pady=(0, 6))

        self.app.btn_align_fl = ttk.Button(
            act, text="🔗  아치 FL 통일  (Ctrl+Shift+F)",
            style="Link.TButton",
            command=self.app.align_multi_arch_fl_ui)
        self.app.btn_align_fl.grid(row=1, column=0, columnspan=2,
                                    sticky="ew", pady=(0, 6))
        self.app.btn_align_fl.grid_remove()

        ttk.Button(act, text="도면 저장  (Ctrl+S)",
                   command=self.app.save_dxf
                   ).grid(row=2, column=0, sticky="ew", padx=(0, 3))
        ttk.Button(act, text="DXF 열기  (Ctrl+O)",
                   command=self.app.open_dxf
                   ).grid(row=2, column=1, sticky="ew", padx=(3, 0))

        ttk.Button(act, text="스냅샷 저장  (Ctrl+Shift+S)",
                   command=self.app.take_snapshot
                   ).grid(row=3, column=0, columnspan=2, sticky="ew",
                          pady=(6, 0))
        ttk.Button(act, text="초기값 복원",
                   command=self.app.reset_params
                   ).grid(row=4, column=0, sticky="ew", padx=(0, 3),
                          pady=(6, 0))
        ttk.Button(act, text="종료", style="Danger.TButton",
                   command=self.app.close
                   ).grid(row=4, column=1, sticky="ew", padx=(3, 0),
                          pady=(6, 0))

    # ── 파라미터 재구성 ────────────────────────────
    def populate(self):
        for w in self.shape_group.winfo_children():
            w.destroy()
        for w in self.dim_group.winfo_children():
            w.destroy()
        for w in self.safety_group.winfo_children():
            w.destroy()
        for w in self.track_group.winfo_children():  # ★ 추가
            w.destroy()
        self.rows.clear()
        self.arch_rows.clear()
        self.track_rows = []  # ★ 추가

        kind = self.app.params.kind
        if kind == TunnelType.BOX:
            self._build_box_editor()
        elif kind in (TunnelType.NATM_2ARCH, TunnelType.NATM_3ARCH):
            self._build_multi_arch_editor()
        else:
            self._build_single_natm_editor()

        # ★ 안전박스는 모든 타입에 공통
        self._build_safety_editor()

        self._build_track_editor()  # ★ 추가

        # ★ populate 후 스크롤 영역 갱신
        self.scroll_frame.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _build_single_natm_editor(self):
        p = self.app.params
        shape = [
            ("R1",       "R1",       1.0, 20.0, 0.01, "m", 3),
            ("상단 각도", "top_angle", 0.0, 180.0, 0.5, "°", 1),
            ("R2",       "R2",       1.0, 20.0, 0.01, "m", 3),
            ("R2 각도",  "r2_angle",  0.0, 180.0, 0.5, "°", 1),
        ]
        dim = [
            ("선로 중심간격", "D",    0.0,  30.0, 0.01, "m", 2),
            ("R1 중심 Y",    "R1_Y", -10.0, 10.0, 0.01, "m", 3),
            ("목표 FL",      "FL",   -5.0,  5.0,  0.01, "m", 3),
        ]
        # ★ 신규: 라이닝(외곽선) 그룹
        lining_group = ttk.LabelFrame(self.shape_group, text="  라이닝(외곽선)  ", padding=6)
        lining_group.grid(row=len(shape), column=0, sticky="ew", pady=(6, 2))
        lining_group.columnconfigure(0, weight=1)

        # 체크박스 (표시 여부)
        def toggle_lining():
            self.app.params.show_lining = self.app.show_lining_var.get()
            self.app.update_plot()

        self.app.show_lining_var = tk.BooleanVar(value=p.show_lining)
        ttk.Checkbutton(lining_group, text="외곽선 표시", variable=self.app.show_lining_var,
                        command=toggle_lining).pack(anchor="w", pady=(0, 4))

        # 라이닝 두께 (ts) & 슬래브 두께 (ts_slab)
        specs_lining = [
            ("라이닝 두께 ts", "ts", 0.1, 2.0, 0.01, "m", 3),
            ("슬래브 두께 sb", "ts_slab", 0.1, 2.0, 0.01, "m", 3),
        ]
        for i, (label, attr, lo, hi, res, unit, dec) in enumerate(specs_lining):
            row = ParamRow(lining_group, label=label, attr=attr,
                           lo=lo, hi=hi, res=res, unit=unit, decimals=dec,
                           on_change=self.app.on_param_change,
                           initial=getattr(p, attr))
            row.frame.pack(fill="x", pady=2)
            self.rows[attr] = row

        for i, (label, attr, lo, hi, res, unit, dec) in enumerate(shape):
            row = ParamRow(self.shape_group, label=label, attr=attr,
                           lo=lo, hi=hi, res=res, unit=unit, decimals=dec,
                           on_change=self.app.on_param_change,
                           initial=getattr(p, attr))
            row.frame.grid(row=i, column=0, sticky="ew", pady=2)
            self.rows[attr] = row
        for i, (label, attr, lo, hi, res, unit, dec) in enumerate(dim):
            row = ParamRow(self.dim_group, label=label, attr=attr,
                           lo=lo, hi=hi, res=res, unit=unit, decimals=dec,
                           on_change=self.app.on_param_change,
                           initial=getattr(p, attr))
            row.frame.grid(row=i, column=0, sticky="ew", pady=2)
            self.rows[attr] = row

    def _build_box_editor(self):
        p = self.app.params
        base = [
            ("내공 폭 B",    "box_width",  2.0, 25.0, 0.01, "m", 2),
            ("내공 높이 H",  "box_height", 2.0, 20.0, 0.01, "m", 2),
            ("벽체 두께 tw", "box_wall_t", 0.1,  2.0, 0.01, "m", 3),
            ("슬래브 두께",  "box_slab_t", 0.1,  2.0, 0.01, "m", 3),
        ]
        dim = [
            ("선로 중심간격", "D",  0.0, 30.0, 0.01, "m", 2),
            ("바닥 FL",      "FL", -5.0, 10.0, 0.01, "m", 3),
        ]
        for i, (label, attr, lo, hi, res, unit, dec) in enumerate(base):
            row = ParamRow(self.shape_group, label=label, attr=attr,
                           lo=lo, hi=hi, res=res, unit=unit, decimals=dec,
                           on_change=self.app.on_param_change,
                           initial=getattr(p, attr))
            row.frame.grid(row=i, column=0, sticky="ew", pady=2)
            self.rows[attr] = row
        for i, (label, attr, lo, hi, res, unit, dec) in enumerate(dim):
            row = ParamRow(self.dim_group, label=label, attr=attr,
                           lo=lo, hi=hi, res=res, unit=unit, decimals=dec,
                           on_change=self.app.on_param_change,
                           initial=getattr(p, attr))
            row.frame.grid(row=i, column=0, sticky="ew", pady=2)
            self.rows[attr] = row

        # 모서리 스타일
        for tag, style_attr, r_attr, dx_attr, dy_attr, title in (
            ("top", "box_style_top", "box_fillet_top_r",
             "box_chamfer_top_dx", "box_chamfer_top_dy", "상단 모서리"),
            ("bot", "box_style_bot", "box_fillet_bot_r",
             "box_chamfer_bot_dx", "box_chamfer_bot_dy", "하단 모서리"),
        ):
            group = ttk.LabelFrame(self.shape_group, text=f"  {title}  ",
                                    padding=6)
            group.grid(row=len(base) + (0 if tag == "top" else 1),
                       column=0, sticky="ew", pady=(6, 2))
            group.columnconfigure(0, weight=1)

            style_var = tk.StringVar(value=getattr(p, style_attr).value)
            setattr(self.app, f"style_{tag}_var", style_var)
            row_frame = ttk.Frame(group, style="Card.TFrame")
            row_frame.grid(row=0, column=0, sticky="w", pady=(0, 4))
            for cs in CornerStyle:
                ttk.Radiobutton(row_frame, text=cs.value, value=cs.value,
                                variable=style_var,
                                command=self.app.on_box_style_change
                                ).pack(side="left", padx=(0, 8))

            r_row = ParamRow(group, label="필렛 R", attr=r_attr,
                             lo=0.0, hi=3.0, res=0.01, unit="m", decimals=3,
                             on_change=self.app.on_param_change,
                             initial=getattr(p, r_attr))
            r_row.frame.grid(row=1, column=0, sticky="ew")
            self.rows[r_attr] = r_row

            ch_row = ttk.Frame(group, style="Card.TFrame")
            ch_row.grid(row=2, column=0, sticky="ew")
            for label, attr in (("사선 dx", dx_attr), ("사선 dy", dy_attr)):
                row = ParamRow(ch_row, label=label, attr=attr,
                               lo=0.0, hi=3.0, res=0.01, unit="m",
                               decimals=3,
                               on_change=self.app.on_param_change,
                               initial=getattr(p, attr))
                row.frame.pack(fill="x", pady=1)
                self.rows[attr] = row

        # ★ 신규: 기둥 및 코핑부 그룹
        col_group = ttk.LabelFrame(self.shape_group, text="  중앙 기둥 / 코핑부  ", padding=6)
        col_group.grid(row=len(base) + 2, column=0, sticky="ew", pady=(6, 2))
        col_group.columnconfigure(0, weight=1)

        col_specs = [
            ("기둥 개수", "box_columns", 0, 5, 1, "개", 0),
            ("기둥 폭", "box_col_width", 0.1, 2.0, 0.01, "m", 3),
            ("코핑 폭", "box_coping_w", 0.0, 2.0, 0.01, "m", 3),
            ("코핑 높이", "box_coping_h", 0.1, 2.0, 0.01, "m", 3),
        ]
        for i, (label, attr, lo, hi, res, unit, dec) in enumerate(col_specs):
            row = ParamRow(col_group, label=label, attr=attr,
                           lo=lo, hi=hi, res=res, unit=unit, decimals=dec,
                           on_change=self.app.on_param_change,
                           initial=getattr(p, attr))
            row.frame.pack(fill="x", pady=2)
            self.rows[attr] = row

        # ★ 신규: 배수구(측구) 그룹
        drain_group = ttk.LabelFrame(self.shape_group, text="  배수구(측구)  ", padding=6)
        drain_group.grid(row=len(base) + 3, column=0, sticky="ew", pady=(6, 2))
        drain_group.columnconfigure(0, weight=1)

        drain_specs = [
            ("배수구 폭", "box_drain_w", 0.0, 1.5, 0.01, "m", 3),
            ("배수구 깊이", "box_drain_h", 0.0, 1.5, 0.01, "m", 3),
        ]
        for i, (label, attr, lo, hi, res, unit, dec) in enumerate(drain_specs):
            row = ParamRow(drain_group, label=label, attr=attr,
                           lo=lo, hi=hi, res=res, unit=unit, decimals=dec,
                           on_change=self.app.on_param_change,
                           initial=getattr(p, attr))
            row.frame.pack(fill="x", pady=2)
            self.rows[attr] = row


    def _build_multi_arch_editor(self):
        p = self.app.params
        nb = ttk.Notebook(self.shape_group)
        nb.pack(fill="both", expand=True)
        self.arch_notebook = nb

        labels = (["좌선", "우선"]
                  if p.kind == TunnelType.NATM_2ARCH
                  else ["중앙", "좌선", "우선"])
        specs = [
            ("R1",       "R1",       1.0, 25.0, 0.01, "m", 3),
            ("상단 각도", "top_angle", 0.0, 180.0, 0.5, "°", 1),
            ("R2",       "R2",       1.0, 25.0, 0.01, "m", 3),
            ("R2 각도",  "r2_angle",  0.0, 180.0, 0.5, "°", 1),
            ("R1 중심 Y", "R1_Y",    -5.0, 15.0, 0.01, "m", 3),
        ]
        for i, label in enumerate(labels):
            tab = ttk.Frame(nb)
            nb.add(tab, text=f"  {label}  ")
            rows_i: dict[str, ParamRow] = {}
            a = p.arches[i]
            for j, (lab, attr, lo, hi, res, unit, dec) in enumerate(specs):
                row = ParamRow(tab, label=lab, attr=f"arch{i}.{attr}",
                               lo=lo, hi=hi, res=res, unit=unit,
                               decimals=dec,
                               on_change=self.app.on_arch_param_change,
                               initial=getattr(a, attr))
                row.frame.grid(row=j, column=0, sticky="ew", pady=2)
                rows_i[attr] = row
            tab.columnconfigure(0, weight=1)
            self.arch_rows.append(rows_i)

        extra = ([("중벽 폭", "pillar_w", 0.3, 5.0, 0.01, "m", 2)]
                 if p.kind == TunnelType.NATM_2ARCH
                 else [("좌측 이격", "gap_L", 0.0, 5.0, 0.01, "m", 2),
                       ("우측 이격", "gap_R", 0.0, 5.0, 0.01, "m", 2)])
        for j, (lab, attr, lo, hi, res, unit, dec) in enumerate(extra):
            row = ParamRow(self.dim_group, label=lab, attr=attr,
                           lo=lo, hi=hi, res=res, unit=unit, decimals=dec,
                           on_change=self.app.on_param_change,
                           initial=getattr(p, attr))
            row.frame.grid(row=j, column=0, sticky="ew", pady=2)
            self.rows[attr] = row

    def _build_safety_editor(self):
        """★ 안전박스 파라미터 (좌/우/높이)."""
        p = self.app.params
        specs = [
            ("좌측 폭", "sideL",      0.1, 3.0, 0.01, "m", 2),
            ("우측 폭", "sideR",      0.1, 3.0, 0.01, "m", 2),
            ("안전 높이", "safeheight", 0.5, 5.0, 0.01, "m", 2),
        ]
        for i, (label, attr, lo, hi, res, unit, dec) in enumerate(specs):
            row = ParamRow(self.safety_group, label=label, attr=attr,
                           lo=lo, hi=hi, res=res, unit=unit, decimals=dec,
                           on_change=self.app.on_param_change,
                           initial=getattr(p, attr))
            row.frame.grid(row=i, column=0, sticky="ew", pady=2)
            self.rows[attr] = row

    def _build_track_editor(self):
        """★ 다중 트랙 편집: 라벨, X오프셋, 차량한계 표시/오프셋, 추가/삭제."""
        p = self.app.params
        tracks = p.get_tracks()

        # 상단 안내 + 버튼
        hint = ttk.Frame(self.track_group)
        hint.pack(fill="x", pady=(0, 6))
        ttk.Label(hint, text=f"선로 {len(tracks)}개",
                  style="Info.TLabel").pack(side="left")
        ttk.Button(hint, text="D 기반 2트랙",
                   command=self.app.reset_tracks_to_D
                   ).pack(side="right", padx=(4, 0))
        ttk.Button(hint, text="+ 추가",
                   command=self.app.add_track
                   ).pack(side="right", padx=(4, 0))

        # 각 트랙
        for i, t in enumerate(tracks):
            # ── 트랙 카드 ────────────────────────────
            card = ttk.LabelFrame(self.track_group,
                                  text=f"  트랙 {i + 1}  ", padding=6)
            card.pack(fill="x", pady=(4, 2))
            card.columnconfigure(1, weight=1)

            # 라벨 + 삭제
            top = ttk.Frame(card, style="Card.TFrame")
            top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
            top.columnconfigure(1, weight=1)

            label_var = tk.StringVar(value=t.label or f"T{i + 1}")
            ttk.Label(top, text="라벨", style="Card.TLabel").pack(side="left", padx=(0, 4))
            label_entry = ttk.Entry(top, textvariable=label_var, width=8)
            label_entry.pack(side="left", padx=(0, 8))
            label_entry.bind("<FocusOut>",
                             lambda e, idx=i, v=label_var: self.app.on_track_label_change(idx, v.get()))
            label_entry.bind("<Return>",
                             lambda e, idx=i, v=label_var: self.app.on_track_label_change(idx, v.get()))

            # 차량한계 표시 체크박스
            show_var = tk.BooleanVar(value=t.show_clearance)

            def _toggle(idx=i, var=show_var):
                self.app.on_track_clearance_toggle(idx, var.get())

            ttk.Checkbutton(top, text="차량한계 표시",
                            variable=show_var, command=_toggle
                            ).pack(side="left", padx=(0, 8))

            # 삭제 버튼
            del_btn = ttk.Button(top, text="✕", width=2,
                                 command=lambda idx=i: self.app.remove_track(idx))
            if len(tracks) <= 1:
                del_btn.state(["disabled"])
            del_btn.pack(side="right")

            # ── 파라미터 3개 ──────────────────────────
            param_specs = [
                ("X 오프셋", "offset_x", -30.0, 30.0, 0.01, "m", 3)
            ]
            for j, (lab, attr, lo, hi, res, unit, dec) in enumerate(param_specs):
                row = ParamRow(card, label=lab,
                               attr=f"track_{i}.{attr}",
                               lo=lo, hi=hi, res=res, unit=unit, decimals=dec,
                               on_change=self.app.on_track_param_change,
                               initial=getattr(t, attr))

                row.grid(row=j + 1, column=0, columnspan=2, sticky="ew", pady=1)
                self.track_rows.append({"row": row, "label_var": label_var})

        # 좌측 스크롤 갱신
        self.scroll_frame.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

class CanvasPanel:
    """우측 도면 + 이력 탭."""
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True)

        # 도면 탭
        tab_plot = ttk.Frame(nb)
        nb.add(tab_plot, text="  도면  ")
        self.fig, self.ax = plt.subplots(figsize=(7, 6), dpi=100)
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.grid(True, color="#e5e5e5", linewidth=0.6)
        self.canvas = FigureCanvasTkAgg(self.fig, master=tab_plot)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        tb = ttk.Frame(tab_plot)
        tb.pack(fill="x")
        self.toolbar = NavigationToolbar2Tk(self.canvas, tb,
                                              pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side="left")

        # 이력 탭
        tab_hist = ttk.Frame(nb)
        nb.add(tab_hist, text="  이력  ")
        self._build_history(tab_hist)

    def _build_history(self, parent):
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True, padx=4, pady=4)

        fit_tab = ttk.Frame(nb)
        nb.add(fit_tab, text="  FL 자동 맞춤  ")
        self._build_fit_history(fit_tab)

        snap_tab = ttk.Frame(nb)
        nb.add(snap_tab, text="  제원 스냅샷  ")
        self._build_snapshot(snap_tab)

    def _build_fit_history(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(fill="x", padx=8, pady=6)
        ttk.Button(bar, text="CSV 저장",
                   command=self.app.save_history_csv
                   ).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="초기화",
                   command=self.app.clear_history
                   ).pack(side="left", padx=(0, 6))
        ttk.Label(bar, text="더블클릭으로 파라미터 복원",
                  style="Info.TLabel").pack(side="left", padx=(12, 0))
        self.hist_count = ttk.Label(bar, text="0건")
        self.hist_count.pack(side="right")

        cols = ("timestamp", "target_FL", "achieved_FL", "R1_Y", "dR1_Y",
                "R1", "top_angle", "R2", "r2_angle", "D", "status")
        heads = {
            "timestamp": "시각", "target_FL": "목표 FL",
            "achieved_FL": "달성 FL", "R1_Y": "R1_Y", "dR1_Y": "ΔR1_Y",
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
        self.hist_tree.bind("<Double-1>", self.app.on_history_dblclick)
        sb = ttk.Scrollbar(frame, orient="vertical",
                            command=self.hist_tree.yview)
        self.hist_tree.configure(yscroll=sb.set)
        self.hist_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _build_snapshot(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(fill="x", padx=8, pady=6)
        ttk.Button(bar, text="현재 제원 저장", style="Accent.TButton",
                   command=self.app.take_snapshot
                   ).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="JSON 저장",
                   command=self.app.save_snapshots_json
                   ).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="JSON 불러오기",
                   command=self.app.load_snapshots_json
                   ).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="선택 삭제",
                   command=self.app.delete_snapshot
                   ).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="초기화",
                   command=self.app.clear_snapshots
                   ).pack(side="left", padx=(0, 6))
        self.snap_count = ttk.Label(bar, text="0건")
        self.snap_count.pack(side="right")

        ttk.Label(parent, text="더블클릭으로 해당 제원 복원",
                  style="Info.TLabel").pack(anchor="w", padx=12)

        cols = ("timestamp", "kind", "total_area", "note")
        heads = {
            "timestamp": "시각", "kind": "타입",
            "total_area": "총 내공면적(㎡)", "note": "메모",
        }
        widths = {"timestamp": 140, "kind": 130,
                  "total_area": 120, "note": 220}
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.snap_tree = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            self.snap_tree.heading(c, text=heads[c])
            self.snap_tree.column(c, width=widths.get(c, 100),
                                  anchor="center" if c != "note" else "w")
        self.snap_tree.bind("<Double-1>", self.app.on_snapshot_dblclick)
        sb = ttk.Scrollbar(frame, orient="vertical",
                            command=self.snap_tree.yview)
        self.snap_tree.configure(yscroll=sb.set)
        self.snap_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")