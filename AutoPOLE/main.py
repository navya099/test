import random
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import math
import re
import numpy as np
from enum import Enum
from shapely.geometry import Point, LineString
import ezdxf  # Import ezdxf for saving to DXF
import json

'''
ver 2025.03.28
offset입력받기 및 구조물 입력받기
'''

#my 모듈
from jsonmodule import ConfigManager
from polemodule import PoleManager
from wiremodule import WireManager
from filemodule import FileManager
from dxfmodule import DxfManager

class AirJoint(Enum):
    START = "에어조인트 시작점 (1호주)"
    POINT_2 = "에어조인트 (2호주)"
    MIDDLE = "에어조인트 중간주 (3호주)"
    POINT_4 = "에어조인트 (4호주)"
    END = "에어조인트 끝점 (5호주)"

class ConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("설정 파일 로딩")
        self.root.geometry("500x400")
        
        # 파일 선택 버튼
        self.select_file_button = tk.Button(self.root, text="설정 파일 선택", command=self.load_config_file)
        self.select_file_button.pack(pady=20)
        
        # 파일 경로 표시
        self.file_label = tk.Label(self.root, text="선택된 파일: 없음")
        self.file_label.pack(pady=10)

        # 결과 출력 영역
        self.result_label = tk.Label(self.root, text="", fg="green")
        self.result_label.pack(pady=10)

        #실행 버튼
        self.exe_button = tk.Button(self.root, text="실행", command=mainprocesser)
        self.exe_button.pack(pady=20)
        
        # 종료 버튼
        self.quit_button = tk.Button(self.root, text="종료", command=self.root.quit)
        self.quit_button.pack(pady=20)

    def load_config_file(self):
        file_path = filedialog.askopenfilename(title="설정 파일 선택", filetypes=[("JSON Files", "*.json")])
        if file_path:
            self.file_label.config(text=f"선택된 파일: {file_path}")
            self.process_config(file_path)

    def process_config(self, file_path):
        config_manager = ConfigManager(file=file_path)
        if config_manager.config:
            validation_result = config_manager.validate_config()
            if validation_result is True:
                self.result_label.config(text="✅ 설정이 정상적으로 로드되었습니다.", fg="green")
            else:
                self.result_label.config(text=validation_result, fg="red")
        else:
            self.result_label.config(text="⚠️ 설정 파일을 불러올 수 없습니다.", fg="red")

class MainProcesser:
    def __init__(self): 
        self.polemanager = PoleManager()
        self.wiremanager = WireManager()
        self.filemanager = FileManager()
        self.dxfmanager = DxfManager()
        
def main():
    root = tk.Tk()
    app = ConfigApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
