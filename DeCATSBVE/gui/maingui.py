import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import asksaveasfilename, askdirectory, askopenfilename

import pandas as pd
from bve.bvecsv import BVECSV
from core.base_runner import BaseRunner
from core.manual_pole_runner import ManualRunner
from core.runner import AutoRunner
from dataset.dataset_getter import DatasetGetter
from dataset.dataset_manager import load_dataset
from event.event_controller import EventController
from file_io.filemanager import write_to_file, save_runner, load_runner
from gui.dataset_gui import DataSetEditor
from gui.maineditor import AutoPoleEditor
from gui.pole_plotter import PlotPoleMap
from xref_module.index_libmgr import IndexLibrary
from xref_module.object_libraymgr import LibraryManager


class AutoPoleApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.tunnel_direction = {'main': None,'sub': None}
        self.db = None
        self.dataset = None
        self.idxlib = None
        self.title("AutoPOLE")
        self.events = EventController()
        self.objlib = LibraryManager()
        self.objlib.scan_library()


        # 로그 박스
        self.log_box = tk.Text(self, height=10, width=80)
        self.log_box.pack(side="bottom", fill="x")
        self.runner: BaseRunner | None = None

        # 입력 영역
        input_frame = tk.Frame(self)
        input_frame.pack(side="top", fill="x")
        tk.Label(input_frame, text="설계속도").pack(side="left")
        self.entry_speed_var = tk.IntVar(value=150)
        self.entry_speed = tk.Entry(input_frame, width=10, textvariable=self.entry_speed_var)
        self.entry_speed.pack(side="left")

        tk.Label(input_frame, text="시작측점").pack(side="left")
        self.entry_start_sta_var = tk.DoubleVar(value=0.0)
        self.entry_start_sta = tk.Entry(input_frame, width=10, textvariable=self.entry_start_sta_var)
        self.entry_start_sta.pack(side="left")

        tk.Label(input_frame, text="끝측점").pack(side="left")
        self.entry_end_sta_var = tk.DoubleVar(value=0.0)
        self.entry_end_sta = tk.Entry(input_frame, width=10, textvariable=self.entry_end_sta_var)
        self.entry_end_sta.pack(side="left")

        tk.Label(input_frame, text="파정").pack(side="left")
        self.entry_brokenchain_var = tk.DoubleVar(value=0.0)
        self.entry_brokenchain = tk.Entry(input_frame, width=10, textvariable=self.entry_brokenchain_var)
        self.entry_brokenchain.pack(side="left")

        self.is_custom_mode = tk.BooleanVar(value=False)
        tk.Checkbutton(input_frame, text="커스텀 모드", variable=self.is_custom_mode).pack(side="left")
        self.is_create_dxf = tk.BooleanVar(value=False)
        tk.Checkbutton(input_frame, text="도면 작성", variable=self.is_create_dxf).pack(side="left")

        self.gen_mode = tk.StringVar(value="auto")
        tk.Radiobutton(input_frame, text="자동 생성", variable=self.gen_mode, value="auto").pack(side="left")
        tk.Radiobutton(input_frame, text="수동 생성", variable=self.gen_mode, value="manual").pack(side="left")

        # 버튼 영역
        button_frame = tk.Frame(self)
        button_frame.pack(side="top", fill="x")
        tk.Button(button_frame, text="새로 만들기", command=self.run_and_open_editor).pack(side="left")
        tk.Button(button_frame, text="로그 클리어", command=self.clear_log).pack(side="left")
        tk.Button(button_frame, text="CSV저장", command=self.save).pack(side="left")
        tk.Button(button_frame, text="데이터저장", command=self.save_pickle).pack(side="left")
        tk.Button(button_frame, text="데이터로드", command=self.load_pickle).pack(side="left")
        tk.Button(button_frame, text="러너 갱신", command=self.update_runner_tracks).pack(side="left")
        tk.Button(button_frame, text="라이브러리 갱신", command=self.refresh_library).pack(side="left")
        tk.Button(button_frame, text="데이터셋 불러오기", command=self.load_dataset).pack(side="left")
        tk.Button(button_frame, text="데이터셋 편집", command=self.edit_dataset).pack(side="left")
        tk.Button(button_frame, text="종료", command=self.exit_app).pack(side="left")

        options_frame = tk.LabelFrame(self, text="트랙 옵션")
        options_frame.pack(side="top", fill="x", padx=5, pady=5)
        self.track_mode = tk.StringVar(value="single")
        tk.Radiobutton(options_frame, text="단일 트랙", variable=self.track_mode, value="single").pack(side="left")
        tk.Radiobutton(options_frame, text="이중 트랙", variable=self.track_mode, value="double").pack(side="left")

        # 트랙 옵션 전체 컨테이너
        tracks_frame = tk.Frame(self)
        tracks_frame.pack(side="top", fill="x", padx=5, pady=5)

        single_frame = tk.LabelFrame(tracks_frame, text="단일 트랙 방향")
        single_frame.pack(side="left", fill="x", padx=5, pady=5)

        self.single_direction = tk.StringVar(value="L")
        self.tunnel_direction['main'] = tk.StringVar(value="R")
        tk.Radiobutton(single_frame, text="본선 좌측", variable=self.single_direction, value="L").pack(anchor="w")
        tk.Radiobutton(single_frame, text="본선 우측", variable=self.single_direction, value="R").pack(anchor="w")

        tk.Radiobutton(single_frame, text="터널 좌측 전주 설치", variable=self.tunnel_direction['main'], value="L").pack(side="left")
        tk.Radiobutton(single_frame, text="터널 우측 전주 설치", variable=self.tunnel_direction['main'], value="R").pack(side="left")

        double_frame = tk.LabelFrame(tracks_frame, text="이중 트랙 방향")
        double_frame.pack(side="left", fill="x", padx=5, pady=5)

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
        if self.runner:
            self.runner.idxlib = self.idxlib

    def exit_app(self):
        self.quit()
        self.destroy()

    def clear_log(self):
        self.log_box.delete("1.0", tk.END)

    def update_inputs(self):
        try:
            if self.gen_mode.get() == 'auto':
                self.runner = AutoRunner()
                self.runner.log_widget = self.log_box
                self.runner.log(f"현재 모드: 자동 배치모드")
            else:
                self.runner = ManualRunner()
                self.runner.log_widget = self.log_box
                self.runner.log(f"현재 모드: 수동 배치모드")

            self.runner.designspeed = int(self.entry_speed.get())
            self.runner.iscustommode = int(self.is_custom_mode.get())
            self.runner.is_create_dxf = int(self.is_create_dxf.get())
            self.runner.idxlib = self.idxlib
            self.runner.track_mode = self.track_mode.get()
            self.runner.start_station = self.entry_start_sta_var.get()
            self.runner.end_station = self.entry_end_sta_var.get()
            self.runner.brokenchain = self.entry_brokenchain_var.get()

            self.filepath_getter()
            if self.runner.track_mode == "single":
                if self.single_direction.get() == 'L':
                    self.runner.track_direction['main'] = -1
                else:
                    self.runner.track_direction['main'] = 1
                self.runner.track_distance = 0.0
                if self.tunnel_direction['main'].get() == 'L':
                    self.runner.tunnel_direction['main'] = -1
                else:
                    self.runner.tunnel_direction['main'] = 1

                self.runner.log(f"현재 모드: 단일 트랙 (본선 {self.runner.track_direction})")
            else:
                if self.double_direction.get() == 'mainL_subR':
                    self.runner.track_direction['main'] = -1
                    self.runner.track_direction['sub'] = 1
                else:
                    self.runner.track_direction['main'] = 1
                    self.runner.track_direction['sub'] = -1

                self.runner.track_distance = self.track_distance.get()
                self.runner.tunnel_direction['main'] = self.runner.track_direction['main'] * -1 #복선 터널은 방향반전
                self.runner.tunnel_direction['sub'] = self.runner.track_direction['sub'] * -1
                self.runner.log(f"현재 모드: 이중 트랙 ({self.runner.track_direction})")

        except ValueError:
            self.runner.log("⚠️ 숫자를 입력하세요")

    def filepath_getter(self):
        folder = askdirectory(title='info 파일 경로 지정')
        coord_path = os.path.join(folder, 'bve_coordinates.txt')
        curve_path = os.path.join(folder, 'curve_info.txt')
        pitch_path = os.path.join(folder, 'pitch_info.txt')
        structue_path = askopenfilename(title='구조물 파일 열기',
                defaultextension=".xlsx",
                filetypes=[("XLSX files", "*.xlsx")],

        )
        if self.runner:
            self.runner.coord_file_path = coord_path
            self.runner.curve_file_path = curve_path
            self.runner.pitch_file_path = pitch_path
            self.runner.structure_file_path = structue_path

    def update_runner_tracks(self):
        """실행 중 runner의 트랙 관련 속성만 갱신"""
        if self.runner.track_mode == "single":
            if self.single_direction.get() == 'L':
                self.runner.track_direction['main'] = -1
            else:
                self.runner.track_direction['main'] = 1
            self.runner.track_distance = 0.0
            if self.tunnel_direction['main'].get() == 'L':
                self.runner.tunnel_direction['main'] = -1
            else:
                self.runner.tunnel_direction['main'] = 1

            self.runner.log(f"트랙 속성 갱신: 단일 트랙 (본선 {self.runner.track_direction})")
        else:
            if self.double_direction.get() == 'mainL_subR':
                self.runner.track_direction['main'] = -1
                self.runner.track_direction['sub'] = 1
            else:
                self.runner.track_direction['main'] = 1
                self.runner.track_direction['sub'] = -1

            self.runner.track_distance = self.track_distance.get()
            self.runner.tunnel_direction['main'] = self.runner.track_direction['main'] * -1
            self.runner.tunnel_direction['sub'] = self.runner.track_direction['sub'] * -1
            self.runner.log(f"트랙 속성 갱신: 이중 트랙 ({self.runner.track_direction})")

    def run_and_open_editor(self):
        # 입력값 반영 후 실행
        try:
            self.update_inputs()
            self.refresh_library()
            self.load_dataset()
            self.runner.run()
            self.editor.runner = self.runner
            self.plotter.runner = self.runner
            self.editor.create_epoles()
            self.editor.create_ewires()
            self.editor.refresh_tree()
            self.plotter.update_plot()
            self.plotter.selected_pole_scatter = None
            self.plotter.selected_pole_text = None
        except Exception as e:
            messagebox.showerror(f'에러', f'러너 실행중 오류가 발생했습니다. \n{e}')
            return

    def save(self):
        self.runner.polesaver_main = BVECSV(self.runner.poledata['main'], self.runner.wire_data['main'], track_index=0)
        t = self.runner.polesaver_main.create_pole_csv() #본선 저장
        t2 = self.runner.polesaver_main.create_wire_csv()
        if not self.runner.pole_path_main:
            # 기본 파일명 지정
            self.runner.pole_path_main= asksaveasfilename(
                title='본선 전주 데이터 저장',
                defaultextension=".txt",
                filetypes=[("TXT files", "*.txt")],
                initialfile="전주.txt"
            )
            self.runner.wire_path_main = asksaveasfilename(
                title='본선 전차선 데이터 저장',
                defaultextension=".txt",
                filetypes=[("TXT files", "*.txt")],
                initialfile="전차선.txt"
            )
        write_to_file(self.runner.pole_path_main, t)
        write_to_file(self.runner.wire_path_main, t2)
        if self.runner.track_mode == "double":
            self.runner.polesaver_sub = BVECSV(self.runner.poledata['sub'], self.runner.wire_data['sub'],
                                                track_index=1)
            s = self.runner.polesaver_sub.create_pole_csv()  # 본선 저장
            s2 = self.runner.polesaver_sub.create_wire_csv()
            if not self.runner.pole_path_sub:
                # 기본 파일명 지정
                self.runner.pole_path_sub = asksaveasfilename(
                    title='상선 전주 데이터 저장',
                    defaultextension=".txt",
                    filetypes=[("TXT files", "*.txt")],
                    initialfile="상선전주.txt"
                )
                self.runner.wire_path_sub = asksaveasfilename(
                    title='상선 전차선 데이터 저장',
                    defaultextension=".txt",
                    filetypes=[("TXT files", "*.txt")],
                    initialfile="상선전차선.txt"
                )

            write_to_file(self.runner.pole_path_sub, s)
            write_to_file(self.runner.wire_path_sub, s2)
        self.runner.log(f"저장 성공!")

    def save_pickle(self):
        save_runner(self.runner,'c:/temp/decatsbve.dat')
        messagebox.showinfo('정보','데이터 저장이 완료됐습니다.')

    def load_pickle(self):
        self.update_inputs()
        self.runner = load_runner('c:/temp/decatsbve.dat')
        self.runner.log_widget = self.log_box
        self.refresh_library()
        self.load_dataset()
        self.runner.polesaver_main = BVECSV(self.runner.poledata["main"], self.runner.wire_data["main"], 0)
        if self.runner.track_mode == "double":
            self.runner.polesaver_sub = BVECSV(self.runner.poledata["sub"], self.runner.wire_data["sub"], 1)
        #절대안정장치
        self.editor.runner = self.runner
        self.plotter.runner = self.runner

        self.editor.create_epoles()
        self.editor.create_ewires()
        self.editor.refresh_tree()
        self.plotter.update_plot()
        self.plotter.selected_pole_scatter = None
        self.plotter.selected_pole_text = None
        messagebox.showinfo('정보', '데이터 로드가 완료됐습니다.')

    def load_dataset(self):
        self.dataset = load_dataset(int(self.entry_speed.get()),int(self.is_custom_mode.get()))
        self.db = DatasetGetter(self.dataset)
        if self.runner:
            self.runner.dataprocessor = self.db
    def edit_dataset(self):
        de = DataSetEditor(self.dataset)