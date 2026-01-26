from dataclasses import dataclass, field
import tkinter as tk
@dataclass
class TKRailData:
    index_var: tk.IntVar
    name_var: tk.StringVar
    brackets: list
    coordx: tk.DoubleVar
    coordy: tk.DoubleVar
    coordz: tk.DoubleVar

    @property
    def index(self):
        return self.index_var.get()

    @property
    def name(self):
        return self.name_var.get()

