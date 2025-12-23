import tkinter as tk
from tkinter import ttk

from library import LibraryManager


class BracketFrame(ttk.LabelFrame):
    def __init__(self, master ,event):
        super().__init__(master, text="선로 정보")
        self.master = master  # 명시적으로 잡아두는 게 좋음
        self.event = event
        self.lib_manager = LibraryManager()
        self.lib_manager.scan_library()
        self.build_bracket_frame()

        self.event.bind("basic.changed", self._rebuild_brackets)

    def build_bracket_frame(self):
        self.bracket_frame = ttk.LabelFrame(self, text="브래킷 설정 (선로별)")
        self.bracket_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.bracket_vars = []
        self._rebuild_brackets()

    def _rebuild_brackets(self):
        for w in self.bracket_frame.winfo_children():
            w.destroy()

        self.bracket_vars.clear()

        # 🔹 라이브러리에서 브래킷 목록 가져오기
        group = self.lib_manager.define_group(self.master.railtype.get())
        brackets = self.lib_manager.list_files_in_category(
            category="브래킷",
            group=group
        )
        # =============================
        # 헤더
        # =============================
        headers = [
            "NO",
            "선로명",
            "선로 인덱스",
            "브래킷 종류",
            "X offset",
            "Y offset",
            'ROTATION'
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

            # 선로 표시
            ttk.Label(
                self.bracket_frame,
                text=f"선로 {i + 1}"
            ).grid(row=row, column=0, padx=5, sticky="w")

            # 선로이름
            rail_name_var = tk.StringVar(value='')
            ttk.Entry(
                self.bracket_frame,
                textvariable=rail_name_var,
                width=6
            ).grid(row=row, column=1, padx=5)

            # 선로 인덱스 (BVE용)
            rail_idx_var = tk.IntVar(value=0)
            ttk.Entry(
                self.bracket_frame,
                textvariable=rail_idx_var,
                width=6
            ).grid(row=row, column=2, padx=5)

            # 브래킷 콤보
            bracket_var = tk.StringVar()
            combo = ttk.Combobox(
                self.bracket_frame,
                textvariable=bracket_var,
                values=brackets,
                state="readonly",
                width=30
            )
            combo.grid(row=row, column=3, padx=5, sticky="w")

            if brackets:
                combo.current(0)

            # X offset
            x_var = tk.DoubleVar(value=0.0)
            ttk.Entry(
                self.bracket_frame,
                textvariable=x_var,
                width=8
            ).grid(row=row, column=4, padx=5)

            # Y offset
            y_var = tk.DoubleVar(value=0.0)
            ttk.Entry(
                self.bracket_frame,
                textvariable=y_var,
                width=8
            ).grid(row=row, column=5, padx=5)

            # ROT
            rotate_var = tk.DoubleVar(value=0.0)
            ttk.Entry(
                self.bracket_frame,
                textvariable=rotate_var,
                width=8
            ).grid(row=row, column=6, padx=5)

            self.bracket_vars.append(
                (rail_name_var, rail_idx_var, bracket_var, x_var, y_var, rotate_var)
            )