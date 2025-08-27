import tkinter as tk
from BVEAlignmentViewer.controller.controller import FileController, EditController, SettingsController, HelpController, \
    AppController
from BVEAlignmentViewer.event.event import EventHandler
from BVEAlignmentViewer.gui.menu import MenuGUI
from BVEAlignmentViewer.plot.plot import PlotFrame

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OPENBVE 선형뷰어")
        self.geometry("650x450")

        # 컨트롤러 생성

        self.file_ctrl = FileController()
        self.edit_ctrl = EditController()
        self.settings_ctrl = SettingsController()
        self.help_ctrl = HelpController()
        self.appcontroller = AppController(self, self.file_ctrl)

        # 이벤트 핸들러 생성

        self.event_handler = EventHandler(self, self.appcontroller, self.file_ctrl, self.settings_ctrl)

        # 메뉴 GUI 생성 시 이벤트 핸들러 메서드를 넘김

        MenuGUI(self, self.event_handler, self.edit_ctrl, self.settings_ctrl, self.help_ctrl)

        # 메인 프레임
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        #PLOT 프레임

        self.plot_frame = PlotFrame(main_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)