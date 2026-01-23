import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import scrolledtext

from controller.event_controller import EventController
from controller.main_controller import MainProcess
from preview.preview_sevice import PreviewService
from .basic_frame import BasicInfoFrame
from .bracket_frame import BracketFrame
from .preview import PreviewViewer
from .structure_frame import StructureFrame

class PoleInstallGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.bve_window = None
        self.title("전주 설치 입력기")
        self.geometry("900x650")

        self.event = EventController()

        # 상태 변수들
        self.station = tk.DoubleVar(value=87943.0)
        self.pole_number = tk.StringVar(value="47-27")
        self.railtype = tk.StringVar(value="준고속철도")
        self.left_x = tk.DoubleVar(value=-12.0)
        self.right_x = tk.DoubleVar(value=9.0)
        self.rail_count = tk.IntVar(value=2)

        # ✅ 미리보기 뷰어를 한 번만 생성
        self.viewer = PreviewViewer()
        self.viewer.set_projection('front')

        # 딜레이 타이머 ID 저장용
        self._preview_after_id = None

        # 변수 변경 시 자동 업데이트 (딜레이 방식)
        for var in [self.station, self.pole_number, self.railtype,
                    self.left_x, self.right_x, self.rail_count]:
            var.trace_add("write", self._schedule_preview)

        # 프레임 생성
        self.basic_frame = BasicInfoFrame(self, self.event)
        self.basic_frame.pack(fill="x", padx=10, pady=5)
        self.structure_frame = StructureFrame(self)
        self.structure_frame.pack(fill="x", padx=10, pady=5)
        self.bracket_frame = BracketFrame(self, self.event)
        self.bracket_frame.pack(fill="x", padx=10, pady=5)

        # 버튼 생성
        self._build_buttons()

    def plot_preview(self):
        mp = MainProcess(self)
        self.result = mp.run()

        # 기존 객체 초기화 후 다시 추가
        self.viewer.objects.clear()
        result = PreviewService.build_from_install(self.result.beam)
        for obj in result.objects:
            self.viewer.add_object(obj)

        if result.missing:
            messagebox.showwarning(
                '일부 파일 누락',
                '다음 파일을 찾을 수 없습니다:\n\n' + '\n'.join(result.missing)
            )

        self.viewer.draw()
        self.show_bvesyntac()
    # ✅ 딜레이 방식: 값 변경 시 바로 실행하지 않고 일정 시간 후 실행
    def _schedule_preview(self, *args):
        # 기존 예약된 실행이 있으면 취소
        if self._preview_after_id is not None:
            self.after_cancel(self._preview_after_id)

        # 300ms 후에 plot_preview 실행 예약
        self._preview_after_id = self.after(300, self.plot_preview)

    # =============================
    # 버튼
    # =============================
    def _build_buttons(self):
        frame = ttk.Frame(self)
        frame.pack(fill="x", pady=10)

        ttk.Button(frame, text="BVE 생성", command=self._generate).pack(side="right", padx=10)
        ttk.Button(frame, text="종료", command=self.destyoy).pack(side="right", padx=10)
        ttk.Button(frame, text="미리보기", command=self.plot_preview).pack(side="right", padx=10)

    def _generate(self):
        mp = MainProcess(self)
        self.result = mp.run()

    def destyoy(self):
        self.destroy()

    # ✅ 값 변경 시 자동 호출되는 함수
    def _update_preview(self, *args):
        self.plot_preview()

    def show_bvesyntac(self):
        if self.result:
            text = self.result.to_bve()

            # ✅ 처음 호출 시에만 새창 생성
            if self.bve_window is None or not self.bve_window.winfo_exists():
                self.bve_window = tk.Toplevel(self)
                self.bve_window.title("BVE 코드")
                self.bve_window.geometry("600x400")


                self.bve_text = scrolledtext.ScrolledText(self.bve_window, wrap="word")
                self.bve_text.pack(fill="both", expand=True)

                ttk.Button(self.bve_window, text="닫기", command=self.bve_window.destroy).pack(pady=5)

            # ✅ 기존 Text 내용 갱신
            self.bve_text.config(state="normal")
            self.bve_text.delete("1.0", "end")
            self.bve_text.insert("1.0", text)
            self.bve_text.config(state="disabled")

        else:
            messagebox.showwarning('에러', '아직 개체가 생성되지 않았습니다.')


