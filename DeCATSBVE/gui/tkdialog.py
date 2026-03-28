import tkinter as tk
from tkinter import filedialog, ttk, messagebox ,simpledialog

from gui.dialogservice import DialogService


class TkDialogService(DialogService):
    def __init__(self, master):
        self.master = master

    def select_file(self, tilte, file_ext) -> str | None:
        return filedialog.askopenfilename(
            parent=self.master,
            defaultextension=file_ext,
            filetypes=[(f"{file_ext} files", f"*{file_ext}")],
            title=f"{file_ext} 파일 선택")

    def select_directory(self, title: str) -> str:
        return filedialog.askdirectory(
            parent=self.master,
            title=title,
        )

    def select_option_list(self, option_list):
        result = {"value": None}

        top = tk.Toplevel(self.master)

        def select(v):
            result["value"] = v
            top.destroy()

        for opt in option_list:
            ttk.Button(top, text=opt, command=lambda v=opt: select(v)).pack(pady=5)

        top.grab_set()
        top.wait_window()

        return result["value"]

    def open_offset_setting(self):
        dialog = OFFSetSettingUI(self.master)
        self.master.wait_window(dialog)  # 창 닫힐 때까지 대기
        return dialog.result

    def oepn_track_setting(self):
        dialog = TRACKSettingUI(self.master)
        self.master.wait_window(dialog)
        return dialog.result

