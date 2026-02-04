from dataclasses import dataclass, field
import tkinter as tk
import uuid

@dataclass
class TKRailData:

    index_var: tk.IntVar
    name_var: tk.StringVar
    brackets: list
    coordx: tk.DoubleVar
    coordy: tk.DoubleVar
    coordz: tk.DoubleVar
    uid= uuid.uuid4().hex  # 절대 안 바뀜
    @property
    def index(self):
        return self.index_var.get()

    @property
    def name(self):
        return self.name_var.get()

