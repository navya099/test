import tkinter as tk
from tkinter import ttk

class PoleADDUI(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title("전주 추가")
        self.protocol("WM_DELETE_WINDOW", self.cancle)

        self.entry_post_number_var = tk.StringVar()
        self.entry_pos_var = tk.DoubleVar()
        self.entry_gauge_var = tk.DoubleVar()
        self.entry_section_var = tk.StringVar()
        self.entry_base_type_var = tk.StringVar()

        # 콤보박스 리스트
        section_list = ['일반개소', '에어조인트 시작점 (1호주)', '에어조인트 (2호주)', '에어조인트 중간주 (3호주)', '에어조인트 (4호주)', '에어조인트 끝점 (5호주)']
        base_type_list = ['I', 'O', 'F']

        # event가 None일 수 있으므로 초기화 시점에는 바인딩하지 않음
        tk.Label(self, text="전주번호").grid(row=0, column=0, padx=5, pady=5)
        self.entry_post_number = ttk.Entry(self, width=10, textvariable=self.entry_post_number_var)
        self.entry_post_number.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self, text="측점").grid(row=1, column=0, padx=5, pady=5)
        self.entry_pos = ttk.Entry(self, width=10, textvariable=self.entry_pos_var)
        self.entry_pos.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self, text="건식게이지").grid(row=2, column=0, padx=5, pady=5)
        self.entry_gauge = ttk.Entry(self, width=10, textvariable=self.entry_gauge_var)
        self.entry_gauge.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(self, text="구간").grid(row=4, column=0, padx=5, pady=5)
        self.entry_section = ttk.Combobox(self, width=10, textvariable=self.entry_section_var ,values=section_list)
        self.entry_section.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(self, text="기본 타입").grid(row=5, column=0, padx=5, pady=5)
        self.entry_base_type = ttk.Combobox(self, width=10, values=base_type_list, textvariable=self.entry_base_type_var)
        self.entry_base_type.grid(row=5, column=1, padx=5, pady=5)

        ttk.Button(self, text="확인", command=self.destroy).grid(row=6, column=0, padx=5, pady=5)
        ttk.Button(self, text="취소", command=self.cancle).grid(row=6, column=1, padx=5, pady=5)


    def cancle(self):
        self.destroy()

    def comfirm(self):
        return {
            "post_number": self.entry_post_number_var.get(),
            "pos": self.entry_pos_var.get(),
            "gauge": self.entry_gauge_var.get(),
            "section": None if self.entry_section_var.get()== '일반개소' else self.entry_section_var.get(),
            "base_type": self.entry_base_type_var.get()
        }