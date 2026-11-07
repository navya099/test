"""ParamRow (슬라이더 + 엔트리)."""
import tkinter as tk
from tkinter import ttk


class ParamRow:
    def __init__(self, parent, *, label, attr, lo, hi, res, unit,
                 decimals, on_change, initial):
        self.attr = attr
        self.on_change = on_change
        self.res = res
        self.decimals = decimals
        self.lo = lo
        self.hi = hi
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text=label, style="Card.TLabel",
                  width=13).grid(row=0, column=0, sticky="w", padx=(6, 8))
        self.var = tk.DoubleVar(value=initial)
        self.scale = ttk.Scale(frame, from_=lo, to=hi, orient="horizontal",
                               variable=self.var, command=self._on_scale)
        self.scale.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self.entry_var = tk.StringVar(value=f"{initial:.{decimals}f}")
        entry = ttk.Entry(frame, textvariable=self.entry_var,
                          width=9, justify="right")
        entry.grid(row=0, column=2, sticky="e")
        entry.bind("<Return>", self._on_entry)
        entry.bind("<FocusOut>", self._on_entry)
        ttk.Label(frame, text=unit, style="Unit.TLabel",
                  width=3).grid(row=0, column=3, sticky="w", padx=(4, 6))
        self.frame = frame

    def _on_scale(self, _val):
        v = round(self.var.get() / self.res) * self.res
        self.entry_var.set(f"{v:.{self.decimals}f}")
        self.on_change(self.attr, v)

    def _on_entry(self, _evt=None):
        try:
            v = float(self.entry_var.get())
        except ValueError:
            self.entry_var.set(f"{self.var.get():.{self.decimals}f}")
            return
        v = max(self.lo, min(self.hi, v))
        self.var.set(v)
        self.entry_var.set(f"{v:.{self.decimals}f}")
        self.on_change(self.attr, v)

    def set_value(self, v: float):
        self.var.set(v)
        self.entry_var.set(f"{v:.{self.decimals}f}")

    # ui/widgets.py의 ParamRow 클래스에 추가
    def grid(self, **kwargs):
        return self.frame.grid(**kwargs)

    def pack(self, **kwargs):
        return self.frame.pack(**kwargs)

    def place(self, **kwargs):
        return self.frame.place(**kwargs)