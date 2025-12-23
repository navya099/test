import tkinter as tk
from tkinter import ttk

from controller.event_controller import EventController
from controller.main_controller import MainProcess
from .basic_frame import BasicInfoFrame

from .bracket_frame import BracketFrame
from .structure_frame import StructureFrame

class PoleInstallGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("전주 설치 입력기")
        self.geometry("900x650")

        self.event = EventController()

        # ✅ 앱 전체 상태 (Single Source of Truth)
        self.station = tk.DoubleVar(value=87943.0)
        self.pole_number = tk.StringVar(value="47-27")
        self.railtype = tk.StringVar(value="준고속철도")
        self.left_x = tk.DoubleVar(value=-12.0)
        self.right_x = tk.DoubleVar(value=9.0)
        self.rail_count = tk.IntVar(value=2)

        #프레임 생성
        self.basic_frame = BasicInfoFrame(self, self.event)
        self.basic_frame.pack(fill="x", padx=10, pady=5)
        self.structure_frame = StructureFrame(self)
        self.structure_frame.pack(fill="x", padx=10, pady=5)
        self.bracket_frame = BracketFrame(self, self.event)
        self.bracket_frame.pack(fill="x", padx=10, pady=5)

        #버튼생성
        self._build_buttons()

    # =============================
    # 버튼
    # =============================
    def _build_buttons(self):
        frame = ttk.Frame(self)
        frame.pack(fill="x", pady=10)

        ttk.Button(frame, text="BVE 생성", command=self._generate).pack(side="right", padx=10)
        ttk.Button(frame, text="종료", command=self.destyoy).pack(side="right", padx=10)
        ttk.Button(frame, text="미리보기", command=self.plot_preview).pack(side="right", padx=10)

    def _generate(self):
        mp = MainProcess(self)
        mp.run()

    def destyoy(self):
        self.destroy()

    def plot_preview(self):
        raise NotImplementedError