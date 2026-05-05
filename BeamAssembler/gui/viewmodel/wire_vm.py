from dataclasses import dataclass
import tkinter as tk

@dataclass
class WireVM:
    name_var: tk.StringVar
    start_x_var: tk.DoubleVar
    start_y_var: tk.DoubleVar
    start_z_var: tk.DoubleVar
    end_x_var: tk.DoubleVar
    end_y_var: tk.DoubleVar
    end_z_var: tk.DoubleVar

