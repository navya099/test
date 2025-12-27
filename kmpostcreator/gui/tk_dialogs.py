import tkinter as tk
from tkinter import filedialog, ttk, messagebox ,simpledialog
from controller.dialogs import DialogService


class TkDialogService(DialogService):
    def __init__(self, master):
        self.master = master

    def select_excel_file(self):
        return filedialog.askopenfilename(
            parent=self.master,
            title="구조물 엑셀 파일 선택",
            filetypes=[("Excel files", "*.xls *.xlsx")]
        )

    def select_directory(self):
        return filedialog.askdirectory(
            parent=self.master,
            title="대상 디렉터리 선택"
        )

    def select_alignment(self):
        result = {"value": None}

        top = tk.Toplevel(self.master)
        top.title("노선 구분 선택")

        def select(v):
            result["value"] = v
            top.destroy()

        for opt in ["일반철도", "도시철도", "고속철도"]:
            ttk.Button(top, text=opt, command=lambda v=opt: select(v)).pack(pady=5)

        top.grab_set()
        top.wait_window()

        return result["value"]

    def ask_brokenchain(self) -> tuple[bool, float | None]:
        exists = messagebox.askyesno("파정 확인", "노선에 거리파정이 존재하나요?")
        if not exists:
            return False, 0

        while True:
            value = simpledialog.askstring(
                "파정 입력",
                "거리파정 값을 입력하세요 (예: 12.34):"
            )
            if value is None:
                return False, 0

            try:
                return True, float(value)
            except ValueError:
                messagebox.showerror("입력 오류", "숫자(float) 형식으로 입력하세요.")

    def ask_offset(self):
        while True:
            value = simpledialog.askstring(
                "오프셋 입력",
                "오프셋 값을 입력하세요 (예: 12.34):"
            )
            if value is None:
                return None
            try:
                return float(value)
            except ValueError:
                messagebox.showerror("입력 오류", "숫자(float) 형식으로 입력하세요.")