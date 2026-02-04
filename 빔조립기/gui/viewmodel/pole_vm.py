from dataclasses import dataclass
import tkinter as tk

from model.tkraildata import TKRailData


@dataclass
class PoleVM:
    """TK UI용 전주 모델"""
    index: tk.IntVar
    poletype: tk.StringVar
    polespec: tk.StringVar
    pole_length: tk.DoubleVar
    base_rail_index: tk.IntVar
    base_rail_uid: tk.StringVar
    gauge: tk.DoubleVar
