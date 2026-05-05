import os
from tkinter import ttk
import tkinter as tk
from tkinter.filedialog import askopenfilename

from alignment_geometry.alignment_calculator import AlignmentCalculator
from alignment_geometry.alignment_parser import AlignmentParser
from alignment_geometry.alignment_loader import BVEAlignmentIntersapter
from tkinter import messagebox

from controller.file_controler import FileController


class IndexInfoFrame(ttk.LabelFrame):
    def __init__(self, master, event=None):
        super().__init__(master, text="커스텀 인덱스 정보")
        self.event = event
        self.default_beam_idx_var = tk.IntVar(value=1500)
        self.default_pole_idx_var = tk.IntVar(value=1500)
        ttk.Label(self, text="커스텀 빔 시작 인덱스").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Entry(self, textvariable=self.default_beam_idx_var, width=15).grid(row=1, column=1, padx=5)
        ttk.Label(self, text="커스텀 전주 시작 인덱스").grid(row=1, column=2, sticky="w", padx=5)
        ttk.Entry(self, textvariable=self.default_pole_idx_var, width=15).grid(row=1, column=3, padx=5)