from dataclasses import dataclass
import tkinter as tk

@dataclass
class BracketFittingViewModel:
    """UI전용 브래킷 금구류 뷰 모델"""
    name_var: tk.StringVar
    xoffset: tk.DoubleVar
    yoffset: tk.DoubleVar
    rotation: tk.DoubleVar