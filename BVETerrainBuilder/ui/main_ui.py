import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import logging


class MainGUI:
    def __init__(self, process_callback):
        self.process_callback = process_callback
        self.root = tk.Tk()
        self.root.title("Railway Terrain Builder v1.0")
        self.root.geometry("600x500")

        self.paths = {
            "coord": tk.StringVar(),
            "struct": tk.StringVar(),
            "rail": tk.StringVar()
        }
        self._setup_ui()

    def _setup_ui(self):
        # ── 파일 선택 영역 ──
        frame = ttk.LabelFrame(self.root, text="파일 경로 설정", padding=10)
        frame.pack(fill="x", padx=10, pady=5)

        for i, (key, label) in enumerate([("coord", "좌표 파일"), ("struct", "구조물 파일"), ("rail", "선로 정보")]):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w")
            ttk.Entry(frame, textvariable=self.paths[key]).grid(row=i, column=1, sticky="ew", padx=5)
            ttk.Button(frame, text="찾기", command=lambda k=key: self._browse(k)).grid(row=i, column=2)

        frame.columnconfigure(1, weight=1)

        # ── 옵션 영역 ──
        opt_frame = ttk.LabelFrame(self.root, text="실행 옵션", padding=10)
        opt_frame.pack(fill="x", padx=10, pady=5)

        self.seg_input = tk.StringVar(value="16")  # 기본값
        ttk.Label(opt_frame, text="세그먼트 번호 (쉼표 구분):").pack(side="left")
        ttk.Entry(opt_frame, textvariable=self.seg_input, width=15).pack(side="left", padx=5)

        self.is_visible = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="시각화(PyVista) 표시", variable=self.is_visible).pack(side="left", padx=10)

        # ── 로그 창 ──
        self.log_text = tk.Text(self.root, height=10, state="disabled", background="#f0f0f0")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)

        # ── 실행 버튼 ──
        self.btn_run = ttk.Button(self.root, text="엔진 가동 (Run Process)", command=self._start_thread)
        self.btn_run.pack(pady=10)

    def _browse(self, key):
        path = filedialog.askopenfilename()
        if path: self.paths[key].set(path)

    def _start_thread(self):
        # GUI가 얼지 않도록 별도 쓰레드에서 실행
        thread = threading.Thread(target=self._execute_process, daemon=True)
        thread.start()
        self.btn_run.config(state="disabled")

    def _execute_process(self):
        try:
            # 입력값 정리
            segs = [int(s.strip()) for s in self.seg_input.get().split(",") if s.strip()]
            self.process_callback(
                self.paths["coord"].get(),
                self.paths["struct"].get(),
                self.paths["rail"].get(),
                segs,
                self.is_visible.get()
            )
            messagebox.showinfo("완료", "모든 작업이 성공적으로 끝났습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"작업 중 에러 발생: {e}")
        finally:
            self.btn_run.config(state="normal")

    def run(self):
        self.root.mainloop()