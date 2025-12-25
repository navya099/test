import tkinter as tk
from tkinter import filedialog, ttk

from kmpostcreator.controller.dialogs import DialogService


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
