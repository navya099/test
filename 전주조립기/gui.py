import os
import shutil
from tkinter import ttk, messagebox, filedialog
import tkinter as tk

from library import LibraryManager


class PoleAssemblerApp:
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
        self.pole_combo.bind("<<ComboboxSelected>>", self.update_options)

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

        # CSV 저장 버튼
        self.export_button = ttk.Button(root, text="CSV 내보내기", command=self.export_csv, state="disabled")
        self.export_button.grid(row=5, column=0, columnspan=2, pady=10)

    # 전주 선택 시 옵션 업데이트
    def update_options(self, event):
        rail_type = self.railtype_var.get()

        # rail_type -> LibraryManager 그룹 매핑
        if rail_type == '고속철도':
            group = 'highspeedrail'
        elif rail_type == '일반철도':
            group = 'normalspeedrail'
        elif rail_type == '준고속철도':
            group = 'subhighspeedrail'
        else:  # 도시철도
            group = 'base'

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
        combine_lines, texturefiles = self.combine_file()

        # CSV 저장
        export_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV 파일", "*.csv")],
            title="CSV 내보내기"
        )
        if not export_path:
            return

        with open(export_path, 'w', encoding='utf-8') as f:
            for line in combine_lines:
                f.write(line)

        messagebox.showinfo('정보', f'CSV 저장 완료:\n{export_path}')

        # 텍스처 복사
        self.copy_textures(texturefiles, os.path.dirname(export_path))
        messagebox.showinfo('정보', f'텍스처 파일 복사 완료:\n{os.path.dirname(export_path)}')

    def copy_textures(self, texturefiles: list[str], dest_dir: str):
        """텍스처 파일을 지정 폴더로 복사"""
        os.makedirs(dest_dir, exist_ok=True)
        for src in texturefiles:
            if os.path.exists(src):
                shutil.copy(src, dest_dir)

    def combine_file(self):
        combine_lines = []
        texturefiles = []
        selections = {
            "기둥": self.pole_var.get(),
            "브래킷": self.bracket_var.get(),
            "급전선설비": self.feeder_var.get(),
            "금구류": self.fpw_var.get()
        }

        for category, filename in selections.items():
            if not filename:
                continue

            # 브래킷만 그룹별 탐색, 나머지는 공통(base)
            if category == "브래킷":
                group = "고속철도" if filename in self.lib_manager.highspeedrail.get(category, []) else \
                    "일반철도" if filename in self.lib_manager.normalspeedrail.get(category, []) else \
                        "cako250"  # 필요시 준고속도 포함
            else:
                group = "공통"

            # 실제 파일 경로 생성
            file_path = os.path.join(self.lib_manager.base_dir, group, category, filename)

            # 주석 추가
            combine_lines.append(f',;{file_path}\n')

            # 파일 내용 읽어서 추가
            lines = self.readfile(file_path)
            combine_lines.extend(lines)

            # 텍스처 검사
            for line in lines:
                texturename = self.search_texture_name(line)
                if texturename and texturename in self.lib_manager.textures:
                    texturefiles.append(self.lib_manager.textures[texturename])

        return combine_lines, texturefiles

    def readfile(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return lines

    def search_texture_name(self, line: str) -> str:
        """LoadTexture 구문에서 텍스처 이름 추출"""
        line = line.strip()
        if line.startswith('LoadTexture'):
            parts = line.split(',')
            if len(parts) > 1:
                return parts[1].strip()
        return ''


