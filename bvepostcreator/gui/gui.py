import tkinter as tk

from controller.appcontroller import AppController
from gui.tk_dialogs import TkDialogService
from gui.widget import GUIWidget


class BVEObjectApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BVE 선로제표 생성기")
        self.geometry("800x400")
        dialogs = TkDialogService(self)
        self.controller = AppController(dialogs)
        self.create_widgets()

    def create_widgets(self):
        GUIWidget(self, self.controller).create_widgets()

    def exit(self):
        self.destroy()
