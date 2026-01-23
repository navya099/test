import tkinter as tk
from tkinter import ttk
import string
from gui.BracketConfigWindow import BracketConfigWindow
from library import LibraryManager
from model.raildata import RailData


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

    def open_bracket_config(self, rail: RailData):
        BracketConfigWindow(
            master=self,
            rail=rail,
            libmanager=self.lib_manager
        )

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

            rail = RailData(
                index_var=rail_idx_var,
                name_var=rail_name_var,
                brackets=[]
            )

            ttk.Button(
                self.bracket_frame,
                text="브래킷 설정",
                command=lambda r=rail: self.open_bracket_config(r)
            ).grid(row=row, column=4, padx=5)

            self.bracket_vars.append(rail)


