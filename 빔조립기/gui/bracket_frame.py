import tkinter as tk
from tkinter import ttk
from adapter.tk_bracket_adapter import TKBracketAdapter
from alignment_geometry.alignment_interpolator import RailInterpolator
from alignment_geomtry import BVEAlignmentIntersapter
from gui.BracketConfigWindow import BracketConfigWindow
from model.tkraildata import TKRailData

class BracketFrame(ttk.LabelFrame):
    def __init__(self, master ,event, lib_manager):
        super().__init__(master, text="선로 정보")
        self.sub_line = None
        self.main_line = None
        self.master = master  # 명시적으로 잡아두는 게 좋음
        self.event = event
        self.current_section = None
        self.lib_manager = lib_manager
        if self.event:
            self.event.bind("section.selected", self._on_section_selected)
            self.event.bind("basic.changed", self._on_basic_changed)
            self.event.bind('station.loaded', self.on_station_loaded)

        self.build_bracket_frame()

    def _on_basic_changed(self, *_):
        if getattr(self, "isloading", False):
            return  # 🔥 로딩 중이면 rebuild 금지

        self.pack()
        self.rebuild_brackets()

    def _on_section_selected(self, section):
        self.current_section = section
        if section:
            if self.current_section.rails_var:
                self.refresh_brackets() #기존 객체 UI갱신
            else:
                self.rebuild_brackets() #새 객세 생성
        else:
            return

    def on_station_loaded(self, als):
        self.main_line = als[0]
        self.sub_line = als[1]

    def open_bracket_config(self, rail: TKRailData):
        BracketConfigWindow(self, rail, self.lib_manager)

    def build_bracket_frame(self):
        self.bracket_frame = ttk.LabelFrame(self, text="브래킷 설정 (선로별)")
        self.bracket_frame.pack(fill="both", expand=True, padx=10, pady=5)

    def rebuild_brackets(self, *_):
        if self.master.isloading:
            return

        for w in self.bracket_frame.winfo_children():
            w.destroy()

        self.current_section.rails_var.clear()
        sta_target = self.current_section.station_var.get()

        for alignment in self.sub_line:
            rail_name_var = tk.StringVar(value=alignment.name)
            rail_idx_var = tk.IntVar(value=alignment.index)

            rail_coordx_var = tk.DoubleVar(value=0.0)
            rail_coordy_var = tk.DoubleVar(value=0.0)
            rail_coordz_var = tk.DoubleVar(value=0.0)

            # ✅ 보간 클래스 호출
            result = RailInterpolator.get_point_at_station(sta_target, alignment.raildata)
            if result:
                x, y = result
                rail_coordx_var.set(x)
                rail_coordy_var.set(y)

            rail = TKRailData(
                index_var=rail_idx_var,
                name_var=rail_name_var,
                brackets=[],
                coordx=rail_coordx_var,
                coordy=rail_coordy_var,
                coordz=rail_coordz_var,
            )
            self.current_section.rails_var.append(rail)

        self.refresh_brackets()

    def refresh_brackets(self):
        """
        - 이미 존재하는 TKRailData들을 그대로 사용해서 UI만 다시 그려줍니다.
        - 상태 보존 + UI 갱신 역할을 담당
        """
        for w in self.bracket_frame.winfo_children():
            w.destroy()

        headers = ["NO", "선로명", "선로 인덱스", "선로 좌표 X", "선로 좌표 Y"]
        for col, text in enumerate(headers):
            ttk.Label(
                self.bracket_frame,
                text=text,
                font=("맑은 고딕", 9, "bold")
            ).grid(row=0, column=col, padx=5, pady=2, sticky="w")

        for i, rail in enumerate(self.current_section.rails_var, start=1):
            row = i
            ttk.Label(self.bracket_frame, text=f"선로 {i}").grid(row=row, column=0, padx=5, sticky="w")

            ttk.Entry(self.bracket_frame, textvariable=rail.name_var, width=6).grid(row=row, column=1)
            ttk.Entry(self.bracket_frame, textvariable=rail.index_var, width=6).grid(row=row, column=2)
            tk.Entry(self.bracket_frame, textvariable=rail.coordx, width=6).grid(row=row, column=3)
            tk.Entry(self.bracket_frame, textvariable=rail.coordy, width=6).grid(row=row, column=4)

            ttk.Button(
                self.bracket_frame,
                text="브래킷 설정",
                command=lambda r=rail: self.open_bracket_config(r)
            ).grid(row=row, column=5, padx=5)
        self.event.emit('rails.updated')