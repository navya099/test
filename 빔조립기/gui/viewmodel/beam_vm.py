from dataclasses import dataclass
import tkinter as tk

@dataclass
class BeamVM:
    beamtype: tk.StringVar
    start_pole: tk.IntVar
    end_pole: tk.IntVar
