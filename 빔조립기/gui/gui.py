import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import scrolledtext
from tkinter.filedialog import askopenfilename, asksaveasfile, asksaveasfilename
from tkinter import filedialog
from adapter.tkinstalladpater import TkInstallAdapter
from bve.bve_structure_list import BVEStrurctureList
import os
from bve.bveserializer import BVETextBuilder
from controller.event_controller import EventController
from controller.file_controler import FileController
from controller.library_controller import IndexLibrary
from controller.main_controller import MainProcess
from library import LibraryManager
from preview.preview_sevice import PreviewService
from .basic_frame import BasicInfoFrame
from .bracket_frame import BracketFrame
from .equipment_window import EquipMentWindow
from .preview import PreviewViewer
from .section_frame import SectionFrame
from .stationinfoframe import StationInfoFrame
from .structure_frame import StructureFrame
import pickle

from .wire_frame import WireFrame

SHEET_ID = "1z0aUcuZCxOQp2St3icbQMbOkrSPfJK_8iZ2JKFDbW8c"
SHEET_NAME = "freeobj"  # ← 원하는 시트 이름
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

class PoleInstallGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.filepath = None
        self._cached_df = None
        self.al = None
        self.selected_dto = None
        self.bve_window = None
        self.title("정거장구간 전차선로 설계 프로그램")
        self.geometry("900x900")
        self.isloading = False
        self.installadaptor = TkInstallAdapter()
        if self._cached_df is None:
            import pandas as pd
            self._cached_df = pd.read_csv(URL)
        df = self._cached_df
        self.idxlib = IndexLibrary(df)
        self.mp = MainProcess(self.idxlib)
        self.event = EventController()
        self.lib_manager = LibraryManager()
        self.lib_manager.scan_library()

        # ✅ 미리보기 뷰어를 한 번만 생성
        self.viewer = PreviewViewer()
        self.viewer.set_projection('front')

        # 딜레이 타이머 ID 저장용
        self._preview_after_id = None

        # 메인 컨테이너 (스크롤 가능)
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 프레임 생성
        self.station_info_frame = StationInfoFrame(scrollable_frame, self.event)
        self.station_info_frame.pack(fill="x", padx=10, pady=5)
        self.section_frame = SectionFrame(scrollable_frame, self.event)
        self.section_frame.pack(fill="x", padx=10, pady=5)
        self.basic_frame = BasicInfoFrame(scrollable_frame, self.event)
        self.basic_frame.pack(fill="x", padx=10, pady=5)
        self.structure_frame = StructureFrame(scrollable_frame, self.event)
        self.structure_frame.pack(fill="x", padx=10, pady=5)
        self.eq_frame = EquipMentWindow(scrollable_frame, self.event, self.lib_manager)
        self.eq_frame.pack(fill="x", padx=10, pady=5)
        self.bracket_frame = BracketFrame(scrollable_frame, self.event, self.lib_manager)
        self.bracket_frame.pack(fill="x", padx=10, pady=5)
        self.wire_frame = WireFrame(scrollable_frame, self.event)
        self.wire_frame.pack(fill="x", padx=10, pady=5)
        
        # 버튼 생성
        self._build_buttons()


    def plot_preview(self):
        self._generate()
        self.viewer.objects.clear()

        self.get_selected_dto()

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
        frame.pack(fill="x", side="bottom", pady=10)

        ttk.Button(frame, text="종료", command=self.destyoy).pack(side="right", padx=10)
        ttk.Button(frame, text="미리보기", command=self.plot_preview).pack(side="right", padx=10)
        ttk.Button(frame, text="로드", command=self.load).pack(side="right", padx=10)
        ttk.Button(frame, text="저장", command=self.save).pack(side="right", padx=10)
        ttk.Button(frame, text="도면저장", command=self.save_dxf).pack(side="right", padx=10)
        ttk.Button(frame, text="bve구문저장", command=self.save_allbve).pack(side="right", padx=10)

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

        path = asksaveasfilename(title='전주 데이터 저장',
                defaultextension=".pkl",
                filetypes=[("PKL files", "*.pkl")]
            )  # pickle 파일
        if path:
            with open(path, "wb") as f:
                pickle.dump(installs, f)

            messagebox.showinfo('데이터 저장', '저장이 완료됐습니다.')
        else:
            print('올바른 pkl파일을 지정해주세요')
            return
    def load(self):
        self.isloading = True
        path = askopenfilename(title='전주 데이터 열기',
                defaultextension=".pkl",
                filetypes=[("PKL files", "*.pkl")]
            )  # pickle 파일
        if path:
            try:
                with open(path, "rb") as f:
                    self.result = pickle.load(f)
                    self.section_frame.sections = self.installadaptor.apply(self, self.result)
                    self.section_frame.refresh_sections()
                self.isloading = False
                messagebox.showinfo('데이터 로드', '로드가 완료됐습니다.')
            except Exception as e:
                messagebox.showerror('에러', f'로드에 실패했습니다. {e}')
        else:
            print('올바른 pkl파일을 지정해주세요')
            return

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

            if self.get_selected_dto():

                # ✅ 2D: 단일 선택된 구간만 저장
                result2d = PreviewService.build_from_install(self.selected_dto)
                for obj in result2d.objects:
                    self.viewer.add_object(obj)

                filename2d = f'c:/temp/{self.selected_dto.pole_number}.dxf'
                dxfmgr.export_dxf(self.viewer.objects, filename2d, option='2d')

            # ✅ 3D: 모든 구간을 합쳐서 하나의 파일로 저장
            all_objects = []
            wires= []
            for dto in self.result:  # self.result = 전체 DTO 리스트
                result3d = PreviewService.build_from_install(dto)
                all_objects.extend(result3d.objects)
                wires.append(dto.wires)
            filename3d = 'c:/temp/all_sections_3d.dxf'
            dxfmgr.export_dxf(all_objects, filename3d, option='3d', wires=wires)
            #전선 도면작성

            messagebox.showinfo('완료', '도면 저장이 완료됐습니다.')

        except Exception as e:
            messagebox.showerror('에러', f'도면 저장중 에러가 발생했습니다.\n{e}')

    def get_selected_dto(self):
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

    def save_allbve(self):
        if not self.filepath:
            folder_path = filedialog.askdirectory(
                title="폴더 선택",
                initialdir="C:/",  # 기본 시작 경로 (옵션)
                mustexist=True  # 존재하는 폴더만 선택 가능
            )

            if folder_path:
                print("선택된 폴더:", folder_path)
                # 여기서 folder_path를 활용하면 됩니다
            else:
                print("선택된 폴더가 없습니다.:")
                return

            self.filepath = os.path.join(folder_path, "전주.txt")
            self.path2 = os.path.join(folder_path, "커스텀.txt")
        all_text = ''
        self._generate()
        for dto in self.result:
            all_text += BVETextBuilder.to_text(dto)
            all_text += '\n'  # DTO 간 구분을 위해 빈 줄 추가

        fc = FileController(self.filepath)
        fc.save(all_text)


        lines = BVEStrurctureList.to_text()

        fc.set_path(self.path2)
        fc.save(lines)