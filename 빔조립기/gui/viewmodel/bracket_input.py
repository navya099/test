from dataclasses import dataclass
import tkinter as tk

@dataclass
class BracketViewModel:
    """UI전용 브래킷 스테이트 보관"""
    rail_no: tk.IntVar
    bracket_type: tk.StringVar
    xoffset: tk.DoubleVar
    yoffset: tk.DoubleVar
    rotation: tk.DoubleVar
    rail_type: tk.StringVar
    fittings: list