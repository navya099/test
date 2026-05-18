import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from dem import DEMProcessor
from function import read_coordinates, parse_structure, convert_coordinates
from section import SectionProvider
from track import get_track_edges


class Run(tk.Tk):
    def __init__(self):
        super().__init__()
        self.provider = None
        self.title('DEM 횡단면도 실시간 뷰어 (3D Slice 기반)')
        self.geometry('1000x800')
        self.current_idx = -1
        self.read_coords = []
        self.provider = None
        self.track_width = 8.0
        self.slope_ratio = 1.5
        self.is_processing = False  # 스레드 중복 실행 방지 플래그
        # --- UI 구성 ---
        # 상단 제어바 (슬라이더 및 스테이션 정보)
        self.ctrl_frame = ttk.Frame(self)
        self.ctrl_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.station_label = ttk.Label(self.ctrl_frame, text="측점: 0 (No Data)")
        self.station_label.pack(side=tk.LEFT, padx=5)

        self.slider = ttk.Scale(self.ctrl_frame, from_=0, to=len(self.read_coords) - 1,
                                orient=tk.HORIZONTAL, command=self._on_slider_move)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # 수정 코드
        self.btn_run = ttk.Button(self.ctrl_frame, text='실행', command=self._start_process)
        self.btn_run.pack(side=tk.LEFT, padx=5)
        # 수정 코드
        ttk.Button(self.ctrl_frame, text='종료', command=self.destroy).pack(side=tk.LEFT, padx=5)
        # 수정 코드
        ttk.Button(self.ctrl_frame, text='옵션', command=self.show_option).pack(side=tk.LEFT, padx=5)

        # 상태 표시줄
        self.status_var = tk.StringVar(value="대기 중...")
        # 수정 후 (복사 가능한 Entry로 변경)
        self.status_bar = tk.Entry(self, textvariable=self.status_var,
                                   relief=tk.SUNKEN,
                                   state='readonly',  # 사용자가 직접 타이핑하는 것은 방지
                                   readonlybackground='#f0f0f0',  # 배경색을 라벨처럼 설정
                                   borderwidth=1)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 차트 영역
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

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
                if self.provider:
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

            # 2. 데이터 로드 및 파싱 검증
            self.read_coords = read_coordinates(read_file)
            if not self.read_coords:
                raise ValueError("좌표 파일이 비어있거나 형식이 잘못되었습니다.")

            self.structure_list = parse_structure(struct_file)

            # 3. 데이터 추출 (stations, xy_list)
            if len(self.read_coords[0]) == 4:
                self.xy_list = [[x, y] for sta, x, y, z in self.read_coords]
                self.xyz_list = [[x, y, z] for sta, x, y, z in self.read_coords]
                self.stations = [sta for sta, x, y, z in self.read_coords]
            elif len(self.read_coords[0]) == 3:
                self.xy_list = [[x, y] for x, y, z in self.read_coords]
                self.xyz_list = [[x, y, z] for x, y, z in self.read_coords]
                self.stations = [i * 25 for i, (x, y, z) in enumerate(self.read_coords)]
            else:
                raise ValueError("좌표 데이터의 컬럼 수가 맞지 않습니다. (Station, X, Y, Z 필요)")

            # 4. 좌표 변환 및 엔진 가동
            self.status_var.set('좌표변환 중...')
            converted_coord = convert_coordinates(self.xy_list, 5186, 4326)

            self.status_var.set('DEM 데이터 처리 중...')
            self.dem_processor = DEMProcessor(converted_coord)

            self.provider = SectionProvider(
                dem_processor=self.dem_processor,
                structure_list=self.structure_list,
                slope_ratio=self.slope_ratio,
                read_coords=self.read_coords,
                xylist = self.xy_list,
                track_width = self.track_width,
                xyzlist= self.xyz_list
            )

            # 5. UI 업데이트
            self.btn_run.config(state='disabled')
            self.slider.configure(from_=0, to=len(self.read_coords) - 1)
            self.slider.set(0)
            self._on_slider_move(0)

        except Exception as e:
            messagebox.showerror("실행 오류", f"프로세스 시작 중 오류가 발생했습니다:\n{str(e)}")
            self.status_var.set("준비 단계에서 오류 발생")
            self.btn_run.config(state='enabled')

    def _on_slider_move(self, val):
        """슬라이더 이동 시 메인 스레드에서 직접 호출"""
        if self.provider is None:
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
            data = self.provider.get_section(idx)

            # 3. 차트 그리기
            if data:
                self._draw_chart(data)
                self.status_var.set("연산 완료")
            else:
                self.status_var.set("데이터 없음")

        except Exception as e:
            error_msg = str(e)
            self._show_error(error_msg)
            messagebox.showerror("연산 오류", f"측점 {idx} 처리 중 오류:\n{error_msg}")
            self.btn_run.config(state='enabled')

    def _async_update(self, idx):
        """백그라운드 연산 및 GUI 업데이트 요청"""
        try:
            # SectionProvider에서 3D Micro-Mesh 기반 데이터 추출
            data = self.provider.get_section(idx)

            # GUI 업데이트는 메인 스레드에서 수행
            self.after(0, self._draw_chart, data)
        except Exception as e:
            import traceback
            err_details = traceback.format_exc()  # 상세 에러 내용 추출
            error_msg = str(e)
            # 람다 대신 직접 인자를 전달하는 메서드 호출
            self.after(0, self._show_error, err_details)

    def _show_error(self, message):
        self.status_var.set(f"Error: {message}")

    def _draw_chart(self, data):
        """전달받은 2D 데이터를 Matplotlib에 그리기"""
        self.ax.clear()

        # 지반선
        dist_g, elev_g = data['ground']
        self.ax.plot(dist_g, elev_g, color='green', label='Ground')

        # 사면
        dist_l, elev_l = data['slope_l']
        dist_r, elev_r = data['slope_r']
        self.ax.plot(dist_l, elev_l, color='purple', lw=2, label='Left Slope')
        self.ax.plot(dist_r, elev_r, color='red', lw=2, label='Right Slope')

        self.ax.legend()
        self.ax.set_title(f"Station: {data['station']}")
        self.canvas.draw()

        self.status_var.set("연산 완료")
        self.station_label.config(text=f"측점: {data['station']}")

    def _fetch_and_plot(self, idx):
        """SectionProvider를 통한 데이터 수집 및 그래프 갱신"""
        try:
            # 3D Micro-Mesh 생성 및 Slice 연산 (핵심 로직)
            data = self.provider.get_section(idx)

            # 메인 스레드에서 차트 업데이트 호출
            self.after(0, self._update_chart, data)
        except Exception as e:
            self.after(0, lambda: self.status_var.set(f"오류 발생: {str(e)}"))

    def _update_chart(self, data):
        """데이터를 바탕으로 실제 Matplotlib 그래프 갱신"""
        self.ax.clear()

        # 1. 지반선 (초록색)
        g_dist, g_elev = data['ground']
        self.ax.plot(g_dist, g_elev, color='green', label='Original Ground', lw=1.5)
        self.ax.fill_between(g_dist, g_elev, min(g_elev) - 5, color='green', alpha=0.1)

        # 2. 좌/우 사면 (보라색/빨간색 등)
        l_dist, l_elev = data['slope_l']
        r_dist, r_elev = data['slope_r']
        self.ax.plot(l_dist, l_elev, color='purple', lw=2, label='Left Slope')
        self.ax.plot(r_dist, r_elev, color='red', lw=2, label='Right Slope')

        self.ax.set_title(f"Cross Section at Station {data['station']}")
        self.ax.grid(True, alpha=0.3)
        self.ax.legend()
        self.ax.set_xlabel("Distance from Center (m)")
        self.ax.set_ylabel("Elevation (m)")

        self.canvas.draw()
        self.status_var.set("연산 완료")
        self.station_label.config(text=f"측점: {data['station']}")