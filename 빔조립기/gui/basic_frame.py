from tkinter import ttk
import tkinter as tk

class BasicInfoFrame(ttk.LabelFrame):
    def __init__(self, master, event=None):
        super().__init__(master, text="기본 정보")
        self.current_section = None
        self.event = event

        # 이벤트 바인딩
        if self.event:
            self.event.bind("section.added", self.on_section_added)
            self.event.bind("section.selected", self.on_section_selected)



        self._build()
        self.rail_entry.bind("<KeyRelease>", self._on_changed)
        self.pole_count_entry.bind("<KeyRelease>", self._on_changed)
        self.beam_count_entry.bind("<KeyRelease>", self._on_changed)

    def on_section_added(self, tkinstall):
        self.current_section = tkinstall

    def on_section_selected(self, selected_section):
        self.current_section = selected_section

        # Entry의 textvariable을 구간 객체의 변수로 직접 연결
        self.station_entry.config(textvariable=self.current_section.station_var)
        self.pole_entry.config(textvariable=self.current_section.pole_number_var)
        self.rail_entry.config(textvariable=self.current_section.rail_count_var)
        self.pole_count_entry.config(textvariable=self.current_section.pole_count_var)
        self.beam_count_entry.config(textvariable=self.current_section.beam_count_var)
        # ✅ 체크박스 연결
        self.beam_check.config(variable=self.current_section.isbeaminstall_var)

    def _on_changed(self, *args):
        if self.event and self.current_section:
            self.event.emit("basic.changed", self.current_section)

    def _build(self):
        # 기본값용 tk.Variable 생성 (section이 없을 때 대비)
        default_station = tk.DoubleVar(value=45876)
        default_pole_number = tk.StringVar(value="43-11")
        default_rail_count = tk.IntVar(value=2)
        default_pole_count = tk.IntVar(value=2)
        default_beam_count = tk.IntVar(value=1)
        default_isbeaminstall = tk.BooleanVar(value=True)

        # 라벨 + Entry 위젯 생성
        ttk.Label(self, text="측점").grid(row=0, column=0, sticky="w", padx=5)
        self.station_entry = ttk.Entry(self, textvariable=default_station, width=15)
        self.station_entry.grid(row=0, column=1, padx=5)

        ttk.Label(self, text="전주번호").grid(row=1, column=0, sticky="w", padx=5)
        self.pole_entry = ttk.Entry(self, textvariable=default_pole_number, width=15)
        self.pole_entry.grid(row=1, column=1, padx=5)

        ttk.Label(self, text="선로 수").grid(row=2, column=0, sticky="w", padx=5)
        self.rail_entry = ttk.Entry(self, textvariable=default_rail_count, width=15)
        self.rail_entry.grid(row=2, column=1, padx=5)

        ttk.Label(self, text="전주 갯수").grid(row=3, column=0, sticky="w", padx=5)
        self.pole_count_entry = ttk.Entry(self, textvariable=default_pole_count, width=15)
        self.pole_count_entry.grid(row=3, column=1, padx=5)

        ttk.Label(self, text="빔 갯수").grid(row=4, column=0, sticky="w", padx=5)
        self.beam_count_entry = ttk.Entry(self, textvariable=default_beam_count, width=15)
        self.beam_count_entry.grid(row=4, column=1, padx=5)

        # 빔 설치 여부 체크박스
        self.beam_check = ttk.Checkbutton(
            self,
            text="빔 설치",
            variable=default_isbeaminstall,
            command=self._on_changed)

        self.beam_check.grid(row=4, column=2, columnspan=2, sticky="w", padx=5)