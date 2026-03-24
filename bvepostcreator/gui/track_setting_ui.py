import tkinter as tk
from tkinter import ttk


class TRACKSettingUI(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.result = None
        self.title("선로 설정")
        self.geometry("300x300")

        options_frame = tk.LabelFrame(self, text="트랙 옵션")
        options_frame.pack(side="top", fill="x", padx=5, pady=5)
        self.track_mode = tk.StringVar(value="single")
        tk.Radiobutton(options_frame, text="단일 트랙", variable=self.track_mode, value="single").pack(side="left")
        tk.Radiobutton(options_frame, text="이중 트랙", variable=self.track_mode, value="double").pack(side="left")

        # 트랙 옵션 전체 컨테이너
        tracks_frame = tk.LabelFrame(self, text="트랙 방향")
        tracks_frame.pack(side="top", fill="x", padx=5, pady=5)

        single_frame = tk.LabelFrame(tracks_frame, text="단일 트랙 방향")
        single_frame.pack(side="left", fill="x", padx=5, pady=5)

        self.single_direction = tk.StringVar(value="L")
        tk.Radiobutton(single_frame, text="좌측", variable=self.single_direction, value="L").pack(anchor="w")
        tk.Radiobutton(single_frame, text="우측", variable=self.single_direction, value="R").pack(anchor="w")

        double_frame = tk.LabelFrame(tracks_frame, text="이중 트랙 방향")
        double_frame.pack(side="left", fill="x", padx=5, pady=5)

        self.double_direction = tk.StringVar(value="mainL_subR")
        tk.Radiobutton(double_frame, text="본선 L / 상선 R", variable=self.double_direction, value="mainL_subR").pack(
            anchor="w")
        tk.Radiobutton(double_frame, text="본선 R / 상선 L", variable=self.double_direction, value="mainR_subL").pack(
            anchor="w")

        # 선로 인덱스 전체 컨테이너
        trackidx_frame = tk.LabelFrame(self, text="선로인덱스")
        trackidx_frame.pack(side="top", fill="x", padx=5, pady=5)


        ttk.Label(trackidx_frame, text="본선:").grid(row=0, column=0, sticky="e", padx=5)
        self.main_track_idx = tk.IntVar(value=0)
        ttk.Entry(trackidx_frame, textvariable=self.main_track_idx, width=5).grid(row=0, column=1, padx=5)
        self.sub_track_idx = tk.IntVar(value=1)
        ttk.Label(trackidx_frame, text="상선:").grid(row=0, column=2, sticky="e", padx=5)
        ttk.Entry(trackidx_frame, textvariable=self.sub_track_idx, width=5).grid(row=0, column=3, padx=5)

        self.track_distance = tk.DoubleVar(value=4.3)
        tk.Label(trackidx_frame, text="선로중심간격:").grid(row=1, column=0, sticky="e", padx=5)
        tk.Entry(trackidx_frame, width=10, textvariable=self.track_distance).grid(row=1, column=1, padx=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="확인", command=self.confirm).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="취소", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def confirm(self):
        track_index: dict[str, int | None] = {'main': None, 'sub': None}
        track_direction: dict[str, int | None] = {'main': None, 'sub': None}

        if self.track_mode.get() == "single":
            track_direction['main'] = -1 if self.single_direction.get() == 'L' else 1
            track_index['main'] = self.main_track_idx.get()
        else:
            track_index['main'] = self.main_track_idx.get()
            track_index['sub'] = self.sub_track_idx.get()

            if self.double_direction.get() == 'mainL_subR':
                track_direction['main'] = -1
                track_direction['sub'] = 1
            else:
                track_direction['main'] = 1
                track_direction['sub'] = -1

        self.result = {
            "mode": self.track_mode.get(),
            "direction": track_direction,
            "distance": self.track_distance.get(),
            "index": track_index
        }
        self.destroy()