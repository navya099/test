import tkinter as tk

from kmpostcreator.controller.appcontroller import AppController
from kmpostcreator.gui.tk_dialogs import TkDialogService
from kmpostcreator.gui.widget import GUIWidget


class KmObjectApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KM Object 생성기")
        self.geometry("600x400")
        dialogs = TkDialogService(self)
        self.controller = AppController(dialogs)
        self.create_widgets()

    def create_widgets(self):
        GUIWidget(self, self.controller).create_widgets()

    def exit(self):
        self.destroy()
