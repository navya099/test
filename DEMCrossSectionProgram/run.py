import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from dem import DEMProcessor
from function import read_coordinates, parse_structure, convert_coordinates
from plot import PlotCrossSection
from processor import Processor
from section import SectionProvider
from visualize import SectionVisualizer

class Run(tk.Tk):
    def __init__(self):
        super().__init__()

        #내부 속성
        self.processor = None
        self.data = None
        self.title('DEM 횡단면도 실시간 뷰어 (3D Slice 기반)')
        self.geometry('1000x800')
        self.current_idx = -1
        self.track_width = 8.0
        self.slope_ratio = 1.5
        self.is_processing = False  # 스레드 중복 실행 방지 플래그

        # --- UI 구성 ---
        # 상단 제어바 (슬라이더 및 스테이션 정보)
        self.ctrl_frame = ttk.Frame(self)
        self.ctrl_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.station_label = ttk.Label(self.ctrl_frame, text="측점: 0 (No Data)")
        self.station_label.pack(side=tk.LEFT, padx=5)

        self.slider = ttk.Scale(self.ctrl_frame, from_=0, to=1,
                                orient=tk.HORIZONTAL, command=self._on_slider_move)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        #버튼
        self.btn_run = ttk.Button(self.ctrl_frame, text='실행', command=self._start_process)
        self.btn_run.pack(side=tk.LEFT, padx=5)
        ttk.Button(self.ctrl_frame, text='종료', command=self.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.ctrl_frame, text='옵션', command=self.show_option).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.ctrl_frame, text='3D보기', command=self.show_3dmesh).pack(side=tk.LEFT, padx=5)

        # 상태 표시줄
        self.status_var = tk.StringVar(value="대기 중...")
        # 수정 후 (복사 가능한 Entry로 변경)
        self.status_bar = tk.Entry(self, textvariable=self.status_var,
                                   relief=tk.SUNKEN,
                                   state='readonly',  # 사용자가 직접 타이핑하는 것은 방지
                                   readonlybackground='#f0f0f0',  # 배경색을 라벨처럼 설정
                                   borderwidth=1)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        #그래프 영역
        self.plotframe = ttk.Frame(self)
        self.plotframe.pack(side=tk.BOTTOM, fill=tk.X)
        self.plotter = PlotCrossSection(self)

    def show_option(self):
        """트랙 폭과 사면 기울기를 설정하는 팝업 창 생성"""
        # 팝업 창 설정
        option_win = tk.Toplevel(self)
        option_win.title("설정 옵션")
        option_win.geometry("300x200")
        option_win.grab_set()  # 설정 창이 닫히기 전까지 메인 창 조작 방지 (Modal)

        # 기본값 설정 (현재 클래스에 저장된 값 혹은 기본값)
        current_width = getattr(self, 'track_width', 8.0)
        current_ratio = getattr(self, 'slope_ratio', 1.5)

        # 입력 필드 레이아웃
        tk.Label(option_win, text="트랙 폭 (m):").pack(pady=(15, 0))
        ent_width = tk.Entry(option_win)
        ent_width.insert(0, str(current_width))
        ent_width.pack(pady=5)

        tk.Label(option_win, text="사면 기울기 (1:n):").pack(pady=(10, 0))
        ent_ratio = tk.Entry(option_win)
        ent_ratio.insert(0, str(current_ratio))
        ent_ratio.pack(pady=5)

        def save_and_close():
            try:
                # 입력값 검증 및 저장
                self.track_width = float(ent_width.get())
                self.slope_ratio = float(ent_ratio.get())
                self.status_var.set(f"옵션 변경 완료: 폭 {self.track_width}m, 기울기 1:{self.slope_ratio}")
                option_win.destroy()

                # 값이 바뀌었으므로 현재 화면 갱신 (이미 데이터가 로드된 경우)
                if self.processor:
                    self._on_slider_move(self.current_idx)

            except ValueError:

                messagebox.showerror("입력 오류", "숫자 형식을 입력해주세요.")

        # 저장 버튼
        tk.Button(option_win, text="적용", command=save_and_close).pack(pady=15)

    def _start_process(self):
        """데이터 로드 및 엔진 초기화 예외 처리 강화"""
        try:
            self.status_var.set('파일 선택 중...')

            # 1. 파일 선택 예외 처리
            read_file = filedialog.askopenfilename(title='좌표 파일 선택',
                                                   filetypes=[("CSV/TXT", "*.csv *.txt"), ("All Files", "*.*")])
            if not read_file: return

            struct_file = filedialog.askopenfilename(title='구조물 파일 선택',
                                                     filetypes=[("xlsx", "*.xlsx"), ("All Files", "*.*")])
            if not struct_file: return
            self.status_var.set('프로세스 준비 중...')
            self.processor = Processor()
            self.processor.run(read_file, struct_file, self.slope_ratio, self.track_width)

            # 5. UI 업데이트
            self.status_var.set('UI 업데이트 중...')
            self.btn_run.config(state='disabled')
            self.slider.configure(from_=0, to=len(self.processor.read_coords) - 1)
            self.slider.set(0)
            self._on_slider_move(0)

        except Exception as e:
            messagebox.showerror("실행 오류", f"프로세스 시작 중 오류가 발생했습니다:\n{str(e)}")
            self.status_var.set("준비 단계에서 오류 발생")
            self.btn_run.config(state='enabled')

    def _on_slider_move(self, val):
        """슬라이더 이동 시 메인 스레드에서 직접 호출"""
        if self.processor is None:
            return

        idx = int(float(val))
        if idx == self.current_idx:
            return

        self.current_idx = idx

        try:
            # 1. 상태 표시줄 업데이트 및 UI 강제 갱신
            self.status_var.set(f"측점 {idx} 연산 중... (Main Thread)")
            self.update_idletasks()  # "연산 중" 메시지가 화면에 즉시 보이게 함

            # 2. 직접 연산 수행 (스레드 없이 실행)
            self.data = self.processor.provider.get_section(idx)

            # 3. 차트 그리기
            if self.data:
                self._draw_chart(self.data)
                self.status_var.set("연산 완료")
            else:
                self.status_var.set("데이터 없음")
            self.btn_run.config(state='enabled')
        except Exception as e:
            error_msg = str(e)
            self._show_error(error_msg)
            messagebox.showerror("연산 오류", f"측점 {idx} 처리 중 오류:\n{error_msg}")
            self.btn_run.config(state='enabled')

    def _show_error(self, message):
        self.status_var.set(f"Error: {message}")

    def show_3dmesh(self):
        if self.data:
            self.status_var.set("3D 보기 실행")
            # 디버그로 pyvista 시각화
            # 시각화 클래스 구동
            visualizer = SectionVisualizer()
            visualizer.verify_section_3d(
                section_data=self.data,
                terrain_mesh=self.data['terrain_mesh'],
                slope_left_mesh=self.data['slope_left_mesh'],
                slope_right_mesh=self.data['slope_right_mesh']
            )
            self.status_var.set("3D 보기 종료")
        else:
            messagebox.showerror('에러', '정의된 횡단 데이터가 없습니다.')
            self.status_var.set("3D 보기 오류")
            return

    def _draw_chart(self, data):
        self.plotter.draw_chart(data)