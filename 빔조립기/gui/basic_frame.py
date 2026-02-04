from tkinter import ttk
import tkinter as tk

class BasicInfoFrame(ttk.LabelFrame):
    def __init__(self, master , event):
        super().__init__(master, text="기본 정보")

        self.event = event
        self.station = master.station
        self.pole_number = master.pole_number
        self.rail_count = master.rail_count
        self.pole_count = master.pole_count
        self.beam_count = master.beam_count
        # 🔥 변경 감지
        self.rail_count.trace_add("write", self._on_changed)
        self.pole_count.trace_add("write", self._on_changed)
        self.beam_count.trace_add("write", self._on_changed)
        self.isbeaminstall = tk.BooleanVar(value=True)
        self._build()

    def _on_changed(self, *args):
        self.event.emit("basic.changed")

    def _build(self):
        fields = [
            ("측점", self.station),
            ("전주번호", self.pole_number),
            ("선로 수", self.rail_count),
            ("전주 갯수", self.pole_count),
            ("빔 갯수", self.beam_count),
        ]

        for i, (label, var) in enumerate(fields):
            ttk.Label(self, text=label).grid(row=i, column=0, sticky="w", padx=5)
            ttk.Entry(self, textvariable=var, width=15).grid(row=i, column=1, padx=5)

        # ✅ 빔 설치 여부
        ttk.Checkbutton(
            self,
            text="빔 설치",
            variable=self.isbeaminstall,
            command=self._on_changed
        ).grid(row=4, column=2, columnspan=2, sticky="w", padx=5)