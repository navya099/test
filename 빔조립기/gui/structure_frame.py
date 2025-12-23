from tkinter import ttk
import tkinter as tk

class StructureFrame(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="구조물 정보")

        self.beam_type = tk.StringVar(value="트러스빔")
        self.pole_type = tk.StringVar(value="강관주")
        self.pole_width = tk.StringVar(value="P10")
        self.pole_height = tk.DoubleVar(value=9.0)
        self._build()

    def _build(self):
        ttk.Label(self, text="빔 타입").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            self, textvariable=self.beam_type,
            values=["강관빔", "트러스빔", "트러스라멘빔", 'V트러스빔'], width=15
        ).grid(row=0, column=1)

        ttk.Label(self, text="전주 타입").grid(row=1, column=0, sticky="w")
        ttk.Combobox(
            self, textvariable=self.pole_type,
            values=["강관주", "H형강주", "조립철주"], width=15
        ).grid(row=1, column=1)

        ttk.Label(self, text="전주 규격").grid(row=2, column=0, sticky="w")
        ttk.Combobox(
            self, textvariable=self.pole_width,
            values=["P10", "P12", "P14", 'P16', 'P18', 'P20'], width=15
        ).grid(row=2, column=1)

        ttk.Label(self, text="전주 높이").grid(row=3, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.pole_height).grid(row=3, column=1)