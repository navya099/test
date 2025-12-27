import tkinter as tk
from doctest import master
from tkinter import ttk

from gui.BracketConfigWindow import BracketConfigWindow
from library import LibraryManager
from model.raildata import RailData


class BracketFrame(ttk.LabelFrame):
    def __init__(self, master ,event):
        super().__init__(master, text="선로 정보")
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
        for i in range(self.master.rail_count.get()):
            row = i + 1

            ttk.Label(
                self.bracket_frame,
                text=f"선로 {i + 1}"
            ).grid(row=row, column=0, padx=5, sticky="w")

            rail_name_var = tk.StringVar()
            ttk.Entry(
                self.bracket_frame,
                textvariable=rail_name_var,
                width=6
            ).grid(row=row, column=1)

            rail_idx_var = tk.IntVar(value=i)
            ttk.Entry(
                self.bracket_frame,
                textvariable=rail_idx_var,
                width=6
            ).grid(row=row, column=2)

            rail = RailData(index=rail_idx_var.get(), name=rail_name_var.get(), brackets=[])

            ttk.Button(
                self.bracket_frame,
                text="브래킷 설정",
                command=lambda r=rail: self.open_bracket_config(r)
            ).grid(row=row, column=4, padx=5)

            self.bracket_vars.append(rail)

