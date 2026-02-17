import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from bve.bvecsv import BVECSV
from core.runner import AutoPole
from event.event_controller import EventController
from file_io.filemanager import write_to_file, load_poles, save_poles, save_runner, load_runner
from gui.maineditor import AutoPoleEditor
from gui.pole_plotter import PlotPoleMap
from xref_module.index_libmgr import IndexLibrary
from xref_module.object_libraymgr import LibraryManager


class AutoPoleApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.idxlib = None
        self.title("AutoPOLE")
        self.events = EventController()
        self.objlib = LibraryManager()
        self.objlib.scan_library()
        # 로그 박스
        self.log_box = tk.Text(self, height=10, width=80)
        self.log_box.pack(side="bottom", fill="x")
        self.runner = AutoPole(self.log_box)
        # 라이브러리 갱신
        self.refresh_library()
        # 입력 영역
        input_frame = tk.Frame(self)
        input_frame.pack(side="top", fill="x")
        tk.Label(input_frame, text="설계속도").pack(side="left")
        self.entry_speed_var = tk.IntVar(value=150)
        self.entry_speed = tk.Entry(input_frame, width=10, textvariable=self.entry_speed_var)
        self.entry_speed.pack(side="left")

        self.is_custom_mode = tk.BooleanVar(value=False)
        tk.Checkbutton(input_frame, text="커스텀 모드", variable=self.is_custom_mode).pack(side="left")
        self.is_create_dxf = tk.BooleanVar(value=False)
        tk.Checkbutton(input_frame, text="도면 작성", variable=self.is_create_dxf).pack(side="left")



        # 버튼 영역
        button_frame = tk.Frame(self)
        button_frame.pack(side="top", fill="x")
        tk.Button(button_frame, text="새로 만들기", command=self.run_and_open_editor).pack(side="left")
        tk.Button(button_frame, text="로그 클리어", command=self.clear_log).pack(side="left")
        tk.Button(button_frame, text="CSV저장", command=self.save).pack(side="left")
        tk.Button(button_frame, text="데이터저장", command=self.save_pickle).pack(side="left")
        tk.Button(button_frame, text="데이터로드", command=self.load_pickle).pack(side="left")
        tk.Button(button_frame, text="라이브러리 갱신", command=self.refresh_library).pack(side="left")
        tk.Button(button_frame, text="종료", command=self.exit_app).pack(side="left")

        options_frame = tk.LabelFrame(self, text="트랙 옵션")
        options_frame.pack(side="top", fill="x", padx=5, pady=5)
        self.track_mode = tk.StringVar(value="single")
        tk.Radiobutton(options_frame, text="단일 트랙", variable=self.track_mode, value="single").pack(side="left")
        tk.Radiobutton(options_frame, text="이중 트랙", variable=self.track_mode, value="double").pack(side="left")

        single_frame = tk.LabelFrame(self, text="단일 트랙 방향")
        single_frame.pack(side="top", fill="x", padx=5, pady=5)

        self.single_direction = tk.StringVar(value="L")
        tk.Radiobutton(single_frame, text="본선 좌측", variable=self.single_direction, value="L").pack(anchor="w")
        tk.Radiobutton(single_frame, text="본선 우측", variable=self.single_direction, value="R").pack(anchor="w")

        double_frame = tk.LabelFrame(self, text="이중 트랙 방향")
        double_frame.pack(side="top", fill="x", padx=5, pady=5)

        self.double_direction = tk.StringVar(value="mainL_subR")
        tk.Radiobutton(double_frame, text="본선 L / 상선 R", variable=self.double_direction, value="mainL_subR").pack(
            anchor="w")
        tk.Radiobutton(double_frame, text="본선 R / 상선 L", variable=self.double_direction, value="mainR_subL").pack(
            anchor="w")
        #트랙 간격(계산용)
        self.track_distance = tk.DoubleVar(value=4.3)
        tk.Label(double_frame, text="선로중심간격").pack(side="left")
        tk.Entry(double_frame, width=10, textvariable=self.track_distance).pack(anchor="w")

        # 메인 영역 (좌우 분할)
        main_frame = tk.PanedWindow(self, orient="horizontal")
        main_frame.pack(fill="both", expand=True)

        # 좌측: Editor
        editor_frame = tk.Frame(main_frame)
        self.editor = AutoPoleEditor(self.runner, self.objlib,self.events, master=editor_frame)
        self.editor.pack(fill="both", expand=True)   # 추가

        main_frame.add(editor_frame)

        # 우측: Plotter
        plotter_frame = tk.Frame(main_frame)
        self.plotter = PlotPoleMap(self.runner, self.events, master=plotter_frame)
        self.plotter.pack(fill="both", expand=True)  # 추가

        main_frame.add(plotter_frame)

    def refresh_library(self):
        SHEET_ID = "1z0aUcuZCxOQp2St3icbQMbOkrSPfJK_8iZ2JKFDbW8c"
        SHEET_NAME = "freeobj"  # ← 원하는 시트 이름
        URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

        self.idxlib = IndexLibrary(pd.read_csv(URL))
        self.runner.idxlib = self.idxlib

    def exit_app(self):
        self.quit()
        self.destroy()

    def clear_log(self):
        self.log_box.delete("1.0", tk.END)

    def update_inputs(self):
        try:
            self.runner.designspeed = int(self.entry_speed.get())
            self.runner.iscustommode = int(self.is_custom_mode.get())
            self.runner.is_create_dxf = int(self.is_create_dxf.get())
            self.runner.idxlib = self.idxlib
            self.runner.track_mode = self.track_mode.get()

            if self.runner.track_mode == "single":
                self.runner.track_direction = self.single_direction.get()
                self.runner.log(f"현재 모드: 단일 트랙 (본선 {self.runner.track_direction})")
            else:
                self.runner.track_direction = self.double_direction.get()
                self.runner.track_distance = self.track_distance.get()
                self.runner.log(f"현재 모드: 이중 트랙 ({self.runner.track_direction})")
        except ValueError:
            self.runner.log("⚠️ 숫자를 입력하세요")

    def run_and_open_editor(self):
        # 입력값 반영 후 실행
        self.update_inputs()
        self.runner.run()
        self.editor.create_epoles()
        self.editor.create_ewires()
        self.editor.refresh_tree()
        self.plotter.update_plot()


    def save(self):
        t = self.runner.polesaver_main.create_pole_csv() #본선 저장
        t2 = self.runner.polesaver_main.create_wire_csv()
        write_to_file(self.runner.pole_path_main, t)
        write_to_file(self.runner.wire_path_main, t2)
        if self.runner.track_mode == "double":
            s = self.runner.polesaver_sub.create_pole_csv()  # 본선 저장
            s2 = self.runner.polesaver_sub.create_wire_csv()
            write_to_file(self.runner.pole_path_sub, s)
            write_to_file(self.runner.wire_path_sub, s2)
        self.runner.log(f"저장 성공!")

    def save_pickle(self):
        save_runner(self.runner,'c:/temp/decatsbve.dat')
        messagebox.showinfo('정보','데이터 저장이 완료됐습니다.')

    def load_pickle(self):
        load_runner(self.runner, 'c:/temp/decatsbve.dat')
        self.runner.polesaver_main = BVECSV(self.runner.poledata["main"], self.runner.wire_data["main"], 0)
        if self.runner.track_mode == "double":
            self.runner.polesaver_sub = BVECSV(self.runner.poledata["sub"], self.runner.wire_data["sub"], 1)
        self.editor.create_epoles()
        self.editor.create_ewires()
        self.editor.refresh_tree()
        self.plotter.update_plot()
        messagebox.showinfo('정보', '데이터 로드가 완료됐습니다.')