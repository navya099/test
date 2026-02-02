from tkinter import ttk
import tkinter as tk

class BasicInfoFrame(ttk.LabelFrame):
    def __init__(self, master , event):
        super().__init__(master, text="기본 정보")

        self.event = event
        self.station = master.station
        self.pole_number = master.pole_number
        self.railtype = master.railtype
        self.left_x = master.left_x
        self.right_x = master.right_x
        self.rail_count = master.rail_count

        # 🔥 변경 감지
        self.railtype.trace_add("write", self._on_changed)
        self.rail_count.trace_add("write", self._on_changed)


        self._build()

    def _on_changed(self, *args):
        self.event.emit("basic.changed")

    def _build(self):
        fields = [
            ("측점", self.station),
            ("전주번호", self.pole_number),
            ("좌측 건식게이지", self.left_x),
            ("우측 건식게이지", self.right_x),
            ("선로 수", self.rail_count),
        ]

        for i, (label, var) in enumerate(fields):
            ttk.Label(self, text=label).grid(row=i, column=0, sticky="w", padx=5)
            ttk.Entry(self, textvariable=var, width=15).grid(row=i, column=1, padx=5)
