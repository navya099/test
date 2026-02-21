import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import scrolledtext
from adapter.tkinstalladpater import TkInstallAdapter
from bve.bveserializer import BVETextBuilder
from controller.event_controller import EventController
from controller.main_controller import MainProcess
from library import LibraryManager
from preview.preview_sevice import PreviewService
from serializer.poleinstallserializer import PoleInstallSerializer
from .basic_frame import BasicInfoFrame
from .bracket_frame import BracketFrame
from .equipment_window import EquipMentWindow
from .preview import PreviewViewer
from .section_frame import SectionFrame
from .structure_frame import StructureFrame
import pickle
class PoleInstallGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.selected_dto = None
        self.bve_window = None
        self.title("전주 설치 입력기")
        self.geometry("900x1200")
        self.isloading = False
        self.installadaptor = TkInstallAdapter()
        self.mp = MainProcess()
        self.event = EventController()
        self.lib_manager = LibraryManager()
        self.lib_manager.scan_library()

        # ✅ 미리보기 뷰어를 한 번만 생성
        self.viewer = PreviewViewer()
        self.viewer.set_projection('front')

        # 딜레이 타이머 ID 저장용
        self._preview_after_id = None

        # 프레임 생성
        self.section_frame = SectionFrame(self, self.event)
        self.section_frame.pack(fill="x", padx=10, pady=5)
        self.basic_frame = BasicInfoFrame(self, self.event)
        self.basic_frame.pack(fill="x", padx=10, pady=5)
        self.structure_frame = StructureFrame(self, self.event)
        self.structure_frame.pack(fill="x", padx=10, pady=5)
        self.eq_frame = EquipMentWindow(self, self.event, self.lib_manager)
        self.eq_frame.pack(fill="x", padx=10, pady=5)
        self.bracket_frame = BracketFrame(self, self.event, self.lib_manager)
        self.bracket_frame.pack(fill="x", padx=10, pady=5)

        # 버튼 생성
        self._build_buttons()

    def plot_preview(self):
        self._generate()
        self.viewer.objects.clear()

        selected_items = self.section_frame.section_list.selection()
        if not selected_items:
            messagebox.showinfo("알림", "구간을 먼저 선택하세요.")
            return

        iid = selected_items[0]

        # ✅ DTO 리스트에서 iid로 매칭
        self.selected_dto = next((dto for dto in self.result if dto.iid == iid), None)
        if not self.selected_dto:
            messagebox.showwarning("오류", "선택된 구간에 해당하는 DTO가 없습니다.")
            return

        result = PreviewService.build_from_install(self.selected_dto)
        for obj in result.objects:
            self.viewer.add_object(obj)

        if result.missing:
            messagebox.showwarning(
                '일부 파일 누락',
                '다음 파일을 찾을 수 없습니다:\n\n' + '\n'.join(result.missing)
            )

        self.viewer.draw()
        self.show_bvesyntac()

    # =============================
    # 버튼
    # =============================
    def _build_buttons(self):
        frame = ttk.Frame(self)
        frame.pack(fill="x", pady=10)

        ttk.Button(frame, text="종료", command=self.destyoy).pack(side="right", padx=10)
        ttk.Button(frame, text="미리보기", command=self.plot_preview).pack(side="right", padx=10)
        ttk.Button(frame, text="로드", command=self.load).pack(side="right", padx=10)
        ttk.Button(frame, text="저장", command=self.save).pack(side="right", padx=10)
        ttk.Button(frame, text="도면저장", command=self.save_dxf).pack(side="right", padx=10)

    def _generate(self):
        self.result = self.installadaptor.collect(self.section_frame.sections)
        self.mp.run(self.result)

    def destyoy(self):
        self.destroy()

    # ✅ 값 변경 시 자동 호출되는 함수
    def _update_preview(self, *args):
        self.plot_preview()

    def show_bvesyntac(self):
        if self.selected_dto:
            text = BVETextBuilder.to_text(self.selected_dto)

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



    def save(self):
        # VM → DTO 변환
        installs = self.installadaptor.collect(self.section_frame.sections)

        path = r'c:/temp/saved_beam_assembler_data.pkl'  # pickle 파일
        with open(path, "wb") as f:
            pickle.dump(installs, f)

        messagebox.showinfo('데이터 저장', '저장이 완료됐습니다.')

    def load(self):
        self.isloading = True
        path = r'c:/temp/saved_beam_assembler_data.pkl'
        try:
            with open(path, "rb") as f:
                self.result = pickle.load(f)
                self.section_frame.sections = self.installadaptor.apply(self, self.result)
                self.section_frame.refresh_sections()
            self.isloading = False
            messagebox.showinfo('데이터 로드', '로드가 완료됐습니다.')
        except Exception as e:
            messagebox.showerror('에러', f'로드에 실패했습니다. {e}')

    def show_errors(self, title, messages):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("600x400")
        win.grab_set()

        text = tk.Text(win, wrap="word", state="normal")
        text.pack(fill="both", expand=True)

        for msg in messages:
            text.insert("end", "• " + msg + "\n")

        text.config(state="disabled")

        ttk.Button(win, text="확인", command=win.destroy).pack(pady=5)

    def show_warnings(self, warnings):
        msg = "\n".join(f"• {w}" for w in warnings)
        return messagebox.askyesno(
            "경고",
            f"다음 경고가 있습니다:\n\n{msg}\n\n계속 로드하시겠습니까?"
        )

    def save_dxf(self):
        try:
            self._generate()
            self.viewer.objects.clear()

            from controller.dxf_controller import DXFController
            dxfmgr = DXFController()

            # ✅ 2D: 단일 선택된 구간만 저장
            result2d = PreviewService.build_from_install(self.selected_dto)
            for obj in result2d.objects:
                self.viewer.add_object(obj)

            filename2d = f'c:/temp/{self.selected_dto.pole_number}.dxf'
            dxfmgr.export_dxf(self.viewer.objects, filename2d, option='2d')

            # ✅ 3D: 모든 구간을 합쳐서 하나의 파일로 저장
            all_objects = []
            for dto in self.result:  # self.result = 전체 DTO 리스트
                result3d = PreviewService.build_from_install(dto)
                all_objects.extend(result3d.objects)

            filename3d = 'c:/temp/all_sections_3d.dxf'
            dxfmgr.export_dxf(all_objects, filename3d, option='3d')

            messagebox.showinfo('완료', '도면 저장이 완료됐습니다.')

        except Exception as e:
            messagebox.showerror('에러', f'도면 저장중 에러가 발생했습니다.\n{e}')