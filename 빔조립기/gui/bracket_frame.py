import tkinter as tk
from tkinter import ttk
import string

from adapter.tk_bracket_adapter import TKBracketAdapter
from adapter.tk_raildata_adapter import TKRaildataAdapter
from gui.BracketConfigWindow import BracketConfigWindow
from library import LibraryManager
from model.tkraildata import TKRailData


class BracketFrame(ttk.LabelFrame):
    def __init__(self, master ,event, lib_manager):
        super().__init__(master, text="선로 정보")
        self.bracket_vars = None
        self.master = master  # 명시적으로 잡아두는 게 좋음
        self.event = event
        self.lib_manager = lib_manager
        self.build_bracket_frame()

        self.event.bind("basic.changed", self._rebuild_brackets)
        # 🔹 초기 rails 업데이트 이벤트
        self._on_rail_changed()

    def open_bracket_config(self, rail: TKRailData):
        def refresh_preview():
            self.master.plot_preview()  # ✅ 기존 PreviewViewer 갱신 함수 호출

        BracketConfigWindow(self, rail, self.lib_manager,
                            on_change=refresh_preview,
                            on_close=refresh_preview)

    def build_bracket_frame(self):
        self.bracket_frame = ttk.LabelFrame(self, text="브래킷 설정 (선로별)")
        self.bracket_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.bracket_vars = []
        self._rebuild_brackets()

    def _rebuild_brackets(self):
        if self.master.isloading:
            return
        for w in self.bracket_frame.winfo_children():
            w.destroy()

        self.bracket_vars.clear()
        # =============================
        # 헤더
        # =============================
        headers = [
            "NO",
            "선로명",
            "선로 인덱스",
            "선로 좌표 X",
            "선로 좌표 Y"
        ]

        for col, text in enumerate(headers):
            ttk.Label(
                self.bracket_frame,
                text=text,
                font=("맑은 고딕", 9, "bold")
            ).grid(row=0, column=col, padx=5, pady=2, sticky="w")

        # =============================
        # 행
        # =============================
        import string

        for i in range(self.master.rail_count.get()):
            row = i + 1

            ttk.Label(
                self.bracket_frame,
                text=f"선로 {i + 1}"
            ).grid(row=row, column=0, padx=5, sticky="w")

            # 기본 선로명 a, b, c ...
            default_name = string.ascii_lowercase[i % 26]

            rail_name_var = tk.StringVar(value=default_name)
            rail_idx_var = tk.IntVar(value=i)
            rail_coordx_var = tk.DoubleVar(value=0.0)
            rail_coordy_var = tk.DoubleVar(value=0.0)

            ttk.Entry(
                self.bracket_frame,
                textvariable=rail_name_var,
                width=6
            ).grid(row=row, column=1)

            ttk.Entry(
                self.bracket_frame,
                textvariable=rail_idx_var,
                width=6
            ).grid(row=row, column=2)

            tk.Entry(
                self.bracket_frame,
                textvariable=rail_coordx_var,
                width=6
            ).grid(row=row, column=3)

            tk.Entry(
                self.bracket_frame,
                textvariable=rail_coordy_var,
                width=6
            ).grid(row=row, column=4)

            rail = TKRailData(
                index_var=rail_idx_var,
                name_var=rail_name_var,
                brackets=[],
                coordx=rail_coordx_var,
                coordy=rail_coordy_var,
                coordz=tk.DoubleVar(value=0.0),
            )

            ttk.Button(
                self.bracket_frame,
                text="브래킷 설정",
                command=lambda r=rail: self.open_bracket_config(r)
            ).grid(row=row, column=5, padx=5)

            self.bracket_vars.append(rail)
            # 🔥 rail 목록 준비 완료 알림
            rail_name_var.trace_add("write", self._on_rail_changed)
            rail_idx_var.trace_add("write", self._on_rail_changed)
    def _on_rail_changed(self, *_):
        self.event.emit("rails.updated", self.bracket_vars)

    def rebuild_from_install(self, rails):
        """DTO 기준으로 UI를 강제로 맞추고 값 적용"""
        self.master.isloading = True

        # 1️⃣ 기존 UI 모두 제거
        for w in self.bracket_frame.winfo_children():
            w.destroy()
        self.bracket_vars.clear()

        # 2️⃣ DTO rail 개수만큼 UI 생성
        headers = ["NO", "선로명", "선로 인덱스", "선로 좌표 X", "선로 좌표 Y"]
        for col, text in enumerate(headers):
            ttk.Label(self.bracket_frame, text=text, font=("맑은 고딕", 9, "bold")).grid(row=0, column=col, padx=5, pady=2,
                                                                                     sticky="w")

        import string
        for i, rail_dict in enumerate(rails):
            row = i + 1

            ttk.Label(self.bracket_frame, text=f"선로 {i + 1}").grid(row=row, column=0, padx=5, sticky="w")

            # 기본 rail 이름
            rail_name_var = tk.StringVar(value=rail_dict["name"])
            rail_idx_var = tk.IntVar(value=rail_dict["index"])
            rail_coordx_var = tk.DoubleVar(value=rail_dict["coord"].x)
            rail_coordy_var = tk.DoubleVar(value=rail_dict["coord"].y)
            rail_coordz_var = tk.DoubleVar(value=rail_dict["coord"].z)

            ttk.Entry(self.bracket_frame, textvariable=rail_name_var, width=6).grid(row=row, column=1)
            ttk.Entry(self.bracket_frame, textvariable=rail_idx_var, width=6).grid(row=row, column=2)
            tk.Entry(self.bracket_frame, textvariable=rail_coordx_var, width=6).grid(row=row, column=3)
            tk.Entry(self.bracket_frame, textvariable=rail_coordy_var, width=6).grid(row=row, column=4)

            rail_ui = TKRailData(
                index_var=rail_idx_var,
                name_var=rail_name_var,
                brackets=[TKBracketAdapter.from_dict(br) for br in rail_dict.get("brackets", [])],
                coordx=rail_coordx_var,
                coordy=rail_coordy_var,
                coordz=rail_coordz_var,
            )

            ttk.Button(self.bracket_frame, text="브래킷 설정", command=lambda r=rail_ui: self.open_bracket_config(r)).grid(
                row=row, column=5, padx=5)

            self.bracket_vars.append(rail_ui)

            # rail 변경 이벤트
            rail_name_var.trace_add("write", self._on_rail_changed)
            rail_idx_var.trace_add("write", self._on_rail_changed)

        self.master.isloading = False

    def _apply_rail_values(self, rails):
        for rail_ui, rail_dict in zip(self.bracket_vars, rails):
            rail_ui.index_var.set(rail_dict["index"])
            rail_ui.name_var.set(rail_dict["name"])
            coord = rail_dict["coord"]
            rail_ui.coordx.set(coord.x)
            rail_ui.coordy.set(coord.y)
            rail_ui.coordz.set(coord.z)
            # 🔥 핵심
            brs = rail_dict["brackets"]#rail_dict["brackets"] == list[dict]
            for br in brs:
                rail_ui.brackets.append(TKBracketAdapter.from_dict(br))
