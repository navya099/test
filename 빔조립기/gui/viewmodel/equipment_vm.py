from dataclasses import dataclass
from tkinter import ttk
import tkinter as tk

@dataclass
class EquipmentVM:
    name_var: tk.StringVar
    x_var: tk.DoubleVar
    y_var: tk.DoubleVar
    rotation_var: tk.DoubleVar
    base_rail_index_var: tk.IntVar