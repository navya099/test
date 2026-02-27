from tkinter import ttk
import tkinter as tk
from tkinter.filedialog import askopenfilename
from alignment_geometry.alignment_parser import AlignmentParser
from alignment_geomtry import BVEAlignmentIntersapter
from tkinter import messagebox

from controller.file_controler import FileController


class StationInfoFrame(ttk.LabelFrame):
    def __init__(self, master, event=None):
        super().__init__(master, text="정거장 정보")
        self.alignments = None
        self.event = event
        self.parser = AlignmentParser()
        self.filepath = ''
        default_station_name_var = tk.StringVar(value="OO정거장")
        ttk.Label(self, text="정거장명").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Entry(self, textvariable=default_station_name_var, width=15).grid(row=1, column=1, padx=5)
        ttk.Button(self, text="정거장파일 불러오기", command=self.load_info).grid(row=1, column=2, padx=5)
        self.al = None

    def load_info(self):
        self.open_file()

        try:
            if not self.filepath:
                messagebox.showwarning("경고", "먼저 파일을 선택하세요.")
                return
            # BVE Alignment 불러오기
            self.al = BVEAlignmentIntersapter.get_alignment()

            # 파일 컨트롤러로 라인 읽기
            fc = FileController(self.filepath)
            fc.load()

            alignments, forms, _, _, _ = self.parser.process_lines_to_alginment_data(fc.get_lines())
            self.alignments = alignments

            messagebox.showinfo("완료", f"정거장 데이터 {len(self.alignments)}개 불러옴")
            if self.event:
                self.event.emit('station.loaded', [self.al, self.alignments])
        except Exception as e:
            messagebox.showerror("에러", f"파일을 불러오는 중 오류 발생: {e}")

    def open_file(self):
        filename = askopenfilename(title="파일 열기")
        if filename:
            messagebox.showinfo("파일 선택", f"선택한 파일: {filename}")
            self.filepath = filename
