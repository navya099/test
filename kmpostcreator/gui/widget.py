import tkinter as tk
from tkinter import filedialog, ttk, messagebox, simpledialog

class GUIWidget:
    def __init__(self, master, controller):
        self.master = master
        self.controller = controller

    def create_widgets(self):
        # 🔹 입력 프레임 (grid)
        input_frame = ttk.Frame(self.master)
        input_frame.pack(pady=10)

        # 🔹 시작 측점 입력
        ttk.Label(input_frame, text="시작 측점").grid(row=0, column=0, sticky="e", padx=5)

        self.start_station_var = tk.DoubleVar(value=79500)
        ttk.Entry(
            input_frame,
            textvariable=self.start_station_var,
            width=15
        ).grid(row=0, column=1, padx=5)

        # 🔹 끝 측점 입력
        ttk.Label(input_frame, text="끝 측점").grid(row=0, column=2, sticky="e", padx=5)

        self.end_station_var = tk.DoubleVar(value=90158)
        ttk.Entry(
            input_frame,
            textvariable=self.end_station_var,
            width=15
        ).grid(row=0, column=3, padx=5)

        # 🔹역방향 측점 입력
        ttk.Label(input_frame, text="역방향 시작 측점").grid(row=0, column=4, sticky="e", padx=5)

        self.reverse_start_station_var = tk.DoubleVar(value=45683)
        ttk.Entry(
            input_frame,
            textvariable=self.reverse_start_station_var,
            width=15
        ).grid(row=0, column=5, padx=5)

        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(pady=10, anchor="center")

        self.is_reverse_var = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(btn_frame, text='역방향', variable=self.is_reverse_var)
        chk.state(['!alternate'])
        chk.pack(side=tk.LEFT, padx=10)

        ttk.Button(btn_frame, text="작업 디렉터리 설정", command=self.controller.dialogs.select_excel_file).pack(side=tk.LEFT, padx=10)

        ttk.Button(btn_frame, text="구조물 엑셀 파일 선택", command=self.controller.dialogs.select_excel_file).pack(side=tk.LEFT, padx=10)

        ttk.Button(btn_frame, text="작업 시작", command=self.on_run).pack(side=tk.LEFT, padx=10)

        ttk.Button(btn_frame, text="종료", command=self.master.exit).pack(side=tk.LEFT, padx=10)

        self.log_box = tk.Text(self.master, height=15, font=("Consolas", 10))
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.controller.set_logger(self.write_log)

    def write_log(self, msg):
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)

    def show_alignment_selector(self, on_select):
        top = tk.Toplevel(self.master)
        top.title("노선 구분 선택")

        ttk.Label(top, text="노선의 종류를 선택하세요").pack(pady=10)

        def select(value):
            on_select(value)
            top.destroy()

        for option in ["일반철도", "도시철도", "고속철도"]:
            ttk.Button(
                top,
                text=option,
                width=15,
                command=lambda v=option: select(v)
            ).pack(pady=5)

        top.grab_set()
        top.wait_window()

    def on_run(self):
        # 🔹 GUI → 상태 저장
        self.controller.state.start_station = self.start_station_var.get()
        self.controller.state.end_station = self.end_station_var.get()
        self.controller.state.reverse_start = self.reverse_start_station_var.get()
        self.controller.state.is_reverse = self.is_reverse_var.get()

        # 🔹 실행
        self.controller.run()
