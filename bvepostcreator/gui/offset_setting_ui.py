import tkinter as tk
from tkinter import ttk


class OFFSetSettingUI(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.result = None
        self.title("구조물별 오프셋 설정")
        self.geometry("300x200")

        #🔹 오프셋 입력
        offset_frame = ttk.LabelFrame(self, text="구조물별 offset 설정")
        offset_frame.pack(pady=10)

        ttk.Label(offset_frame, text="토공").grid(row=0, column=0, sticky="e", padx=5)
        self.e_xoffset_var = tk.DoubleVar(value=3.3)
        ttk.Entry(offset_frame, textvariable=self.e_xoffset_var, width=15).grid(row=0, column=1, padx=5)
        self.e_yoffset_var = tk.DoubleVar(value=0.0)
        ttk.Entry(offset_frame, textvariable=self.e_yoffset_var, width=15).grid(row=0, column=2, padx=5)

        ttk.Label(offset_frame, text="교량").grid(row=1, column=0, sticky="e", padx=5)
        self.b_xoffset_var = tk.DoubleVar(value=3)
        ttk.Entry(offset_frame, textvariable=self.b_xoffset_var, width=15).grid(row=1, column=1, padx=5)
        self.b_yoffset_var = tk.DoubleVar(value=0.0)
        ttk.Entry(offset_frame, textvariable=self.b_yoffset_var, width=15).grid(row=1, column=2, padx=5)

        ttk.Label(offset_frame, text="터널").grid(row=2, column=0, sticky="e", padx=5)
        self.t_xoffset_var = tk.DoubleVar(value=4.546)
        ttk.Entry(offset_frame, textvariable=self.t_xoffset_var, width=15).grid(row=2, column=1, padx=5)
        self.t_yoffset_var = tk.DoubleVar(value=0.0)
        ttk.Entry(offset_frame, textvariable=self.t_yoffset_var, width=15).grid(row=2, column=2, padx=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="확인", command=self.confirm).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="취소", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def confirm(self):
        # 오프셋 적용
        self.result = {
            '토공': (self.e_xoffset_var.get(), self.e_yoffset_var.get()),
            "교량": (self.b_xoffset_var.get(), self.b_yoffset_var.get()),
            "터널": (self.t_xoffset_var.get(), self.t_yoffset_var.get())
        }
        self.destroy()
