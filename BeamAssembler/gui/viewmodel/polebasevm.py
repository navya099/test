from dataclasses import dataclass
import tkinter as tk

from model.tkraildata import TKRailData


@dataclass
class PoleBaseVM:
    """TK UI용 전주기초 모델"""
    basename_var: tk.StringVar

