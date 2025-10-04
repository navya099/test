import os
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
from filemanager import FileManager
from library import LibraryManager


class PoleAssemblerApp:
    """
    메인 앱
    """
    def __init__(self, root):
        self.root = root
        self.root.title("전주 조립기")
        self.lib_manager = LibraryManager() #인스턴스 연결
        self.lib_manager.scan_library() #라이브러리 생성

        # 현재 선택 저장
        self.selection = {"pole": None, "bracket": None, "beam": None, "direction": None}

        #1. 선로 종류 선택
        ttk.Label(root, text="선로 종류 선택:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.railtype_var = tk.StringVar()
        self.railtype_combo = ttk.Combobox(
            root,
            textvariable=self.railtype_var,
            values=['도시철도', '일반철도', '고속철도', '준고속철도'],
            state="readonly"
        )
        self.railtype_combo.grid(row=0, column=1, padx=5, pady=5)
        self.railtype_combo.bind("<<ComboboxSelected>>", self.update_options)

        # 2. 위젯 생성
        # 전주 형식
        ttk.Label(root, text="전주 형식 선택:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.pole_var = tk.StringVar()
        self.pole_combo = ttk.Combobox(root, textvariable=self.pole_var, values= [], state="readonly")
        self.pole_combo.grid(row=1, column=1, padx=5, pady=5)

        # 브래킷
        ttk.Label(root, text="브래킷 종류:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.bracket_var = tk.StringVar()
        self.bracket_combo = ttk.Combobox(root, textvariable=self.bracket_var, state="disabled")
        self.bracket_combo.grid(row=2, column=1, padx=5, pady=5)

        #급전선
        ttk.Label(root, text="급전선 종류:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.feeder_var = tk.StringVar()
        self.feeder_combo = ttk.Combobox(root, textvariable=self.feeder_var, state="disabled")
        self.feeder_combo.grid(row=3, column=1, padx=5, pady=5)

        #보호선
        ttk.Label(root, text="보호선 지지물 종류:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.fpw_var = tk.StringVar()
        self.fpw_combo = ttk.Combobox(root, textvariable=self.fpw_var, state="disabled")
        self.fpw_combo.grid(row=4, column=1, padx=5, pady=5)

        #건식게이지
        ttk.Label(root, text="건식게이지:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.gauge_var = tk.DoubleVar()
        self.gauge_combo = ttk.Combobox(root, textvariable=self.gauge_var)
        self.gauge_combo.grid(row=5, column=1, padx=5, pady=5)

        # CSV 저장 버튼
        self.export_button = ttk.Button(root, text="CSV 내보내기", command=self.export_csv, state="disabled")
        self.export_button.grid(row=6, column=0, columnspan=2, pady=10)



    # 전주 선택 시 옵션 업데이트
    def update_options(self, event):
        """
        콤보상자 옵션 업데이트 메소드
        :param event:
        :return:
        """
        rail_type = self.railtype_var.get()
        group = self.lib_manager.define_group(rail_type)

        # 전주 목록 조회
        poles = self.lib_manager.list_files_in_category('기둥', group='base')

        self.pole_combo.config(values=poles)

        #브래킷 리스트 가져오기
        brackets = self.lib_manager.list_files_in_category(category='브래킷',group=group)
        self.bracket_combo.config(values=brackets, state="readonly")

        #급전선 세팅
        feeders = self.lib_manager.list_files_in_category(category='급전선설비',group='base')
        self.feeder_combo.config(values=feeders, state="readonly")

        #보호선 세팅
        fpws = self.lib_manager.list_files_in_category(category='금구류', group='base')
        self.fpw_combo.config(values=fpws, state="readonly")

        #저장버튼 활성화
        self.export_button.config(state="readonly")

    def export_csv(self):
        """조립된 전주를 CSV로 저장하고 텍스처 파일도 복사"""
        selections = {
            "기둥": self.pole_var.get(),
            "브래킷": self.bracket_var.get(),
            "급전선설비": self.feeder_var.get(),
            "금구류": self.fpw_var.get()
        }
        gauge = self.gauge_var.get()

        filemanager = FileManager(self.lib_manager)
        combine_lines, texturefiles = filemanager.combine_file(selections, gauge)

        # CSV 저장 위치
        export_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV 파일", "*.csv")],
            title="CSV 내보내기"
        )
        if not export_path:
            return

        # CSV 저장
        filemanager.save_csv(export_path, combine_lines)
        messagebox.showinfo('정보', f'CSV 저장 완료:\n{export_path}')

        # 텍스처 복사
        filemanager.copy_textures(texturefiles, os.path.dirname(export_path))
        messagebox.showinfo('정보', f'텍스처 파일 복사 완료:\n{os.path.dirname(export_path)}')



