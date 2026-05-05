import tkinter as tk
from tkinter import ttk, messagebox

from gui.viewmodel.wire_vm import WireVM


class WireFrame(ttk.LabelFrame):
    def __init__(self, master, event=None):
        super().__init__(master, text="전선 정보")
        self.button_frame = None
        self.current_section = None
        self.event = event
        if self.event:
            self.event.bind("section.selected", self._on_section_selected)
        self.build_ui()

    def build_ui(self):

        # 프레임 생성
        self.wire_frame = ttk.LabelFrame(self, text='전선별 설정')
        self.wire_frame.grid(row=0, column=0, columnspan=2, sticky="w")

        # 추가/삭제 버튼
        self.button_frame = ttk.Frame(self)
        self.button_frame.grid(row=1, column=0, sticky="w", pady=5)
        ttk.Button(self.button_frame, text="+", width=3, command=self.add_wire).grid(row=0, column=10, padx=2)
        ttk.Button(self.button_frame, text="-", width=3, command=self.remove_wire).grid(row=0, column=11, padx=2)

    def _on_section_selected(self, section):
        self.current_section = section
        if section:
            if self.current_section.wires_var:
                self.refresh_wires() #기존 객체 UI갱신
            else:
                self.rebuild_wires() #새 객세 생성
        else:
            return
    def rebuild_wires(self, *_):
        """
        - 구간이 처음 생성되었을 때만 호출해서 전선들을 새로 만들어줍니다.
        - 데이터 모델 초기화 역할만 담당합니다.
        """
        # 기존 UI 제거
        for w in self.wire_frame.winfo_children():
            w.destroy()

        # ✅ equips 초기화는 rebuild에서만
        if self.current_section.wires_var:
            self.current_section.wires_var.clear()
        else:
            self.current_section.wires_var = []
        # EquipVM 새로 생성
        for i in self.current_section.wires_var:
            wire_vm = WireVM(
                name_var=tk.StringVar(value="기본전선"),
                start_x_var=tk.DoubleVar(value=0.0),
                start_y_var=tk.DoubleVar(value=0.0),
                start_z_var=tk.DoubleVar(value=0.0),
                end_x_var=tk.DoubleVar(value=0.0),
                end_y_var=tk.DoubleVar(value=0.0),
                end_z_var=tk.DoubleVar(value=0.0),
            )
            self.current_section.wires_var.append(wire_vm)

        # ✅ UI는 refresh에서 따로 그림
        self.refresh_wires()

    def refresh_wires(self):
        """
        - 이미 존재하는 WireVM 그대로 사용해서 UI만 다시 그려줍니다.
        - 상태 보존 + UI 갱신 역할을 담당합니다.
        """
        # 기존 UI 제거
        for w in self.wire_frame.winfo_children():
            w.destroy()

        headers = ["전선명", "시작 X", "시작 Y", '시작 Z', '끝 X', "끝 Y", "끝 Z"]
        for col, text in enumerate(headers):
            ttk.Label(self.wire_frame, text=text, font=("맑은 고딕", 9, "bold")).grid(
                row=0, column=col, padx=5, pady=2
            )

        for i, wire in enumerate(self.current_section.wires_var, start=1):
            row = i
            #전선명 엔트리;
            ttk.Entry(self.wire_frame, textvariable=wire.name_var, width=6).grid(row=row, column=0)

            #시작 지오메트리 정보
            ttk.Entry(self.wire_frame, textvariable=wire.start_x_var, width=6).grid(row=row, column=1)
            ttk.Entry(self.wire_frame, textvariable=wire.start_y_var, width=6).grid(row=row, column=2)
            ttk.Entry(self.wire_frame, textvariable=wire.start_z_var, width=6).grid(row=row, column=3)

            # 끝 지오메트리 정보
            ttk.Entry(self.wire_frame, textvariable=wire.end_x_var, width=6).grid(row=row, column=4)
            ttk.Entry(self.wire_frame, textvariable=wire.end_y_var, width=6).grid(row=row, column=5)
            ttk.Entry(self.wire_frame, textvariable=wire.end_z_var, width=6).grid(row=row, column=6)

    def add_wire(self):
        # 새 장비 생성
        new_wire = WireVM(
            name_var=tk.StringVar(value="새 전선"),
            start_x_var=tk.DoubleVar(value=0.0),
            start_y_var=tk.DoubleVar(value=0.0),
            start_z_var=tk.DoubleVar(value=0.0),
            end_x_var=tk.DoubleVar(value=0.0),
            end_y_var=tk.DoubleVar(value=0.0),
            end_z_var=tk.DoubleVar(value=0.0),
        )
        if self.current_section.wires_var:
            self.current_section.wires_var.append(new_wire)
        else:
            self.current_section.wires_var =[]
            self.current_section.wires_var.append(new_wire)
        self.refresh_wires()
        self.event.emit("wires.updated")

    def remove_wire(self):
        if self.current_section.wires_var:
            self.current_section.wires_var.pop()  # 마지막 장비 제거
            self.refresh_wires()
            self.event.emit("wires.updated")