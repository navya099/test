from dataclasses import dataclass, field
import tkinter as tk
@dataclass
class RailData:
    index_var: tk.IntVar
    name_var: tk.StringVar
    brackets: list

    @property
    def index(self):
        return self.index_var.get()

    @property
    def name(self):
        return self.name_var.get()

