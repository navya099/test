from tkinter import ttk
import tkinter as tk
from gui.viewmodel.beam_vm import BeamVM

class BeamFrame(ttk.LabelFrame):
    def __init__(self, master, event=None):
        super().__init__(master, text="빔 정보")
        self.event = event
        self.current_section = None
        self.isloading = False
        if event:
            self.event.bind("section.selected", self._on_section_selected)
            self.event.bind("basic.changed", self._on_basic_changed)

    def _on_section_selected(self, section):
        self.current_section = section
        if self.current_section.beams_var:
            self.refresh_beams() #기존 객체 UI갱신
        else:
            self.rebuild_beams() #새 객세 생성

    def _on_basic_changed(self, *_):
        if getattr(self, "isloading", False):
            return  # 🔥 로딩 중이면 rebuild 금지

        self.grid()
        self.rebuild_beams()

    def rebuild_beams(self, *_):
        """
        - 구간이 처음 생성되었을 때만 호출해서 BeamVM들을 새로 만들어줍니다.
        - 데이터 모델 초기화 역할만 담당
        """
        # 기존 UI 제거
        for w in self.winfo_children():
            w.destroy()

        # ✅ beam_vars 초기화는 rebuild에서만
        self.current_section.beams_var.clear()

        # BeamVM 새로 생성
        for i in range(self.current_section.beam_count_var.get()):
            index = tk.IntVar(value=i + 1)
            beamtype_var = tk.StringVar(value="트러스빔")
            start_pole_var = tk.IntVar(value=1)
            end_pole_var = tk.IntVar(value=1)

            beam_vm = BeamVM(
                index=index,
                beamtype=beamtype_var,
                start_pole=start_pole_var,
                end_pole=end_pole_var
            )
            self.current_section.beams_var.append(beam_vm)

        # ✅ UI는 refresh에서 따로 그림
        self.refresh_beams()

    def refresh_beams(self):
        """
        - 이미 존재하는 BeamVM들을 그대로 사용해서 UI만 다시 그려줍니다
        - 상태 보존 + UI 갱신 역할을 담당
        """
        # 기존 UI 제거
        for w in self.winfo_children():
            w.destroy()

        headers = ["NO", "빔 타입", '시작 전주', '끝 전주']
        for col, text in enumerate(headers):
            ttk.Label(self, text=text, font=("맑은 고딕", 9, "bold")).grid(row=0, column=col, padx=5, pady=2)

        pole_labels = self._get_pole_labels()

        for i, beam_vm in enumerate(self.current_section.beams_var, start=1):
            row = i
            ttk.Label(self, text=str(i)).grid(row=row, column=0)

            ttk.Combobox(
                self,
                textvariable=beam_vm.beamtype,
                values=["강관빔", "트러스빔", "트러스라멘빔", "V트러스빔"],
                state="readonly",
                width=15
            ).grid(row=row, column=1)

            ttk.Combobox(
                self,
                textvariable=beam_vm.start_pole,
                values=list(range(1, len(pole_labels) + 1)),
                state="readonly",
                width=8
            ).grid(row=row, column=2)

            ttk.Combobox(
                self,
                textvariable=beam_vm.end_pole,
                values=list(range(1, len(pole_labels) + 1)),
                state="readonly",
                width=8
            ).grid(row=row, column=3)

    def _get_pole_labels(self):
        """
        Beam UI에서 사용할 전주 선택 목록
        """
        labels = []
        for i, pole_vm in enumerate(self.current_section.poles_var, start=1):
            labels.append(f"전주 {i}")
        return labels
