import tkinter as tk
from tkinter import ttk
import string
from gui.BracketConfigWindow import BracketConfigWindow
from library import LibraryManager
from model.tkraildata import TKRailData


class BracketFrame(ttk.LabelFrame):
    def __init__(self, master ,event):
        super().__init__(master, text="선로 정보")
        self.bracket_vars = None
        self.master = master  # 명시적으로 잡아두는 게 좋음
        self.event = event
        self.lib_manager = LibraryManager()
        self.lib_manager.scan_library()
        self.build_bracket_frame()

        self.event.bind("basic.changed", self._rebuild_brackets)

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
                coordz=tk.DoubleVar(value=0.0)
            )

            ttk.Button(
                self.bracket_frame,
                text="브래킷 설정",
                command=lambda r=rail: self.open_bracket_config(r)
            ).grid(row=row, column=5, padx=5)

            self.bracket_vars.append(rail)


