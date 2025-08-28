import os
from tkinter import messagebox

from controller.controller_base import AppController


class EventHandler:
    def __init__(self, main_app, app_controller: AppController, file_controller, settings_controller):
        self.some_option_var = None
        self.main_app = main_app
        self.app_controller = app_controller
        self.file_controller = file_controller
        self.settings_controller = settings_controller

    def on_file_open(self):
        self.file_controller.open_file()
        filepath = self.file_controller.filepath
        if filepath:
            route = self.app_controller.load_route(filepath)  # ✅ 공식 인터페이스 호출
            if route:
                messagebox.showinfo("정보", f"루트파싱 성공")

    def on_file_save(self):
        filename = self.file_controller.save_file()
        if filename:
            messagebox.showinfo("파일 저장 기능", f"파일 저장 기능 {filename}")

    def on_open_settings(self):
        messagebox.showinfo("설정 기능", f"설정 저장 기능")