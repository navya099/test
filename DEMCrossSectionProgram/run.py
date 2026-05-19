import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import threading
import time
import os

from bveexporter import BVEExporter
from dxfexporter import DXFExporter
from processor import Processor
from plot import PlotCrossSection
from visualize import SectionVisualizer


class Run(tk.Tk):
    def __init__(self):
        super().__init__()

        # 내부 속성
        self.processor = None
        self.data = None
        self.title('DEM 횡단면도 실시간 뷰어 (Hybrid Async Cache)')
        self.geometry('1000x800')
        self.current_idx = -1
        self.track_width = 8.0
        self.slope_ratio = 1.5

        # 🚀 [하이브리드 캐시 핵심 속성]
        self.cache_data = {}  # 연산 완료된 단면 데이터를 인덱스별로 저장 {idx: data_dict}
        self.cache_lock = threading.Lock()  # 멀티스레드 환경에서 캐시 딕셔너리 보호용 락
        self.caching_thread = None  # 백그라운드 스레드 객체
        self.stop_caching = False  # 스레드 강제 종료 플래그 (새 파일 로드 시 기존 스레드 정지)

        # --- UI 구성 ---
        self.ctrl_frame = ttk.Frame(self)
        self.ctrl_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.station_label = ttk.Label(self.ctrl_frame, text="측점: 0 (No Data)")
        self.station_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(self.ctrl_frame, text=" |  이동:").pack(side=tk.LEFT, padx=(5, 2))
        self.ent_search = ttk.Entry(self.ctrl_frame, width=8)
        self.ent_search.pack(side=tk.LEFT, padx=2)
        self.ent_search.bind("<Return>", lambda event: self._jump_to_station())

        btn_jump = ttk.Button(self.ctrl_frame, text="이동", width=5, command=self._jump_to_station)
        btn_jump.pack(side=tk.LEFT, padx=(2, 10))

        self.slider = ttk.Scale(self.ctrl_frame, from_=0, to=1, orient=tk.HORIZONTAL, command=self._on_slider_move)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        self.btn_run = ttk.Button(self.ctrl_frame, text='실행', command=self._start_process)
        self.btn_run.pack(side=tk.LEFT, padx=5)
        ttk.Button(self.ctrl_frame, text='종료', command=self.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.ctrl_frame, text='옵션', command=self.show_option).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.ctrl_frame, text='3D보기', command=self.show_3dmesh).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.ctrl_frame, text='bve저장', command=self.export_to_bve).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.ctrl_frame, text='도면저장', command=self.export_to_dxf).pack(side=tk.LEFT, padx=5)

        # 상태 표시줄
        self.status_var = tk.StringVar(value="대기 중...")
        self.status_bar = tk.Entry(self, textvariable=self.status_var, relief=tk.SUNKEN, state='readonly',
                                   readonlybackground='#f0f0f0', borderwidth=1)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 그래프 영역
        self.plotframe = ttk.Frame(self)
        self.plotframe.pack(side=tk.BOTTOM, fill=tk.X)
        self.plotter = PlotCrossSection(self)

        # 창이 닫힐 때 백그라운드 스레드도 안전하게 죽도록 설정
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def show_option(self):
        option_win = tk.Toplevel(self)
        option_win.title("설정 옵션")
        option_win.geometry("300x200")
        option_win.grab_set()

        current_width = getattr(self, 'track_width', 8.0)
        current_ratio = getattr(self, 'slope_ratio', 1.5)

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
                self.track_width = float(ent_width.get())
                self.slope_ratio = float(ent_ratio.get())

                # 🚀 옵션이 바뀌면 기존 캐시 데이터를 전부 비우고 새로 비동기 러닝을 돌아야 함
                with self.cache_lock:
                    self.cache_data.clear()

                self.status_var.set(f"옵션 변경: 폭 {self.track_width}m, 기울기 1:{self.slope_ratio} (캐시 재적재)")
                option_win.destroy()

                if self.processor:
                    # 현재 화면 강제 갱신 및 백그라운드 재가동
                    self._start_background_caching()
                    self.current_idx = -1
                    self._on_slider_move(self.slider.get())

            except ValueError:
                messagebox.showerror("입력 오류", "숫자 형식을 입력해주세요.")

        tk.Button(option_win, text="적용", command=save_and_close).pack(pady=15)

    def _start_process(self):
        """데이터 로드 및 무조건 즉시 실행"""
        try:
            # 혹시 기존에 돌고 있던 캐싱 스레드가 있다면 먼저 안전하게 종료 유도
            if self.caching_thread and self.caching_thread.is_alive():
                self.stop_caching = True
                self.caching_thread.join(timeout=1.0)

            self.status_var.set('파일 선택 중...')
            read_file = filedialog.askopenfilename(title='좌표 파일 선택',
                                                   filetypes=[("CSV/TXT", "*.csv *.txt"), ("All Files", "*.*")])
            if not read_file: return

            struct_file = filedialog.askopenfilename(title='구조물 파일 선택',
                                                     filetypes=[("xlsx", "*.xlsx"), ("All Files", "*.*")])
            if not struct_file: return

            self.status_var.set('엔진 초기화 중...')
            self.update_idletasks()

            self.processor = Processor()
            self.processor.run(read_file, struct_file, self.slope_ratio, self.track_width)

            # 캐시 공간 초기화 및 제어 플래그 리셋
            self.cache_data.clear()
            self.stop_caching = False

            # UI 설정 변경
            self.btn_run.config(state='disabled')
            total_count = len(self.processor.read_coords)
            self.slider.configure(from_=0, to=total_count - 1)
            self.slider.set(0)

            # 🚀 핵심: 0번 단면만 메인 스레드에서 즉시 연산해 화면에 보여주고, 나머지는 백그라운드로 넘김
            self._on_slider_move(0)

            # 백그라운드 캐싱 워커 스레드 기동
            self._start_background_caching()

        except Exception as e:
            messagebox.showerror("실행 오류", f"프로세스 시작 중 오류가 발생했습니다:\n{str(e)}")
            self.status_var.set("오류 발생")
            self.btn_run.config(state='enabled')

    # -------------------------------------------------------------
    # 🚀 [비동기 캐싱 코어] 백그라운드 스레드 생성 및 로직
    # -------------------------------------------------------------
    def _start_background_caching(self):
        """백그라운드 스레드를 생성하여 전구간을 백그라운드에서 캐싱"""
        self.stop_caching = False
        self.caching_thread = threading.Thread(target=self._background_caching_worker, daemon=True)
        self.caching_thread.start()

    def _background_caching_worker(self):
        """순수 데이터 연산 루프를 돌며 딕셔너리에 결과 캐시 상주"""
        if not self.processor: return

        total_stations = len(self.processor.read_coords)
        has_fast_mode = hasattr(self.processor.provider, 'get_section_fast')

        for i in range(total_stations):
            if self.stop_caching:
                break  # 사용자가 파일 새로 부르거나 창 닫으면 루프 탈출

            # 이미 캐싱되어 있거나 메인 스레드가 먼저 연산한 구역은 생략
            with self.cache_lock:
                if i in self.cache_data:
                    continue

            # 무거운 UI 연산 없이 순수 데이터 엔진만 고속 런타임
            if has_fast_mode:
                section_data = self.processor.provider.get_section_fast(i)
            else:
                section_data = self.processor.provider.get_section(i)

            if section_data:
                section_data['track_width'] = self.track_width
                # 락을 걸고 안전하게 데이터 적재
                with self.cache_lock:
                    self.cache_data[i] = section_data

            # 100개 측점마다 메인 윈도우 하단 바에 진척도 가볍게 보고 (UI Thread 안 뻗게 주기 조절)
            if i % 100 == 0 or i == total_stations - 1:
                progress_pct = (len(self.cache_data) / total_stations) * 100
                self.status_var.set(f"연산 완료 및 전구간 백그라운드 캐싱 중... ({progress_pct:.1f}%)")

    def _on_slider_move(self, val):
        """슬라이더 이동 시 캐시 확인 후 0초 만에 렌더링, 없으면 즉시 실시간 연산 구동"""
        if self.processor is None: return

        idx = int(float(val))
        if idx == self.current_idx: return
        self.current_idx = idx

        # 1. 🚀 [캐시 히트 체크] 이미 백그라운드가 계산해 둔 메모리가 있는지 확인
        with self.cache_lock:
            cached_res = self.cache_data.get(idx)

        if cached_res:
            # 캐시에 이미 데이터가 존재하므로 즉시 드로잉 (0.001초 렉 제로 효과)
            self.data = cached_res
            self._draw_chart(self.data)
            self.station_label.config(text=f"측점: {self.data['station']} (캐시 로드)")
        else:
            # 백그라운드가 아직 도달하지 못한 측점인 경우, 메인 스레드가 즉시 실시간 연산 가로채기
            self.station_label.config(text=f"측점 계산 중...")
            self.update_idletasks()

            self.data = self.processor.provider.get_section(idx)
            if self.data:
                self.data['track_width'] = self.track_width
                # 가로채서 계산한 결과도 다음을 위해 캐시에 저장해 둠
                with self.cache_lock:
                    self.cache_data[idx] = self.data
                self._draw_chart(self.data)
                self.station_label.config(text=f"측점: {self.data['station']} (실시간 연산)")

        self.btn_run.config(state='enabled')

    # -------------------------------------------------------------
    # ⚡ [초고속 해방] 수집 완료된 데이터를 단 1초 만에 텍스트 파일로 일괄 출력
    # -------------------------------------------------------------
    def export_to_bve(self):
        if self.processor is None:
            messagebox.showerror('에러', '로드된 데이터가 없습니다.')
            return

        total_stations = len(self.processor.read_coords)

        with self.cache_lock:
            cached_count = len(self.cache_data)

        # 백그라운드가 다 돌았는지 여부 검사 및 유저 안내 인터페이스
        if cached_count < total_stations:
            confirm = messagebox.askyesno(
                "캐싱 미완료 안내",
                f"현재 전구간 중 {cached_count}/{total_stations}개 캐싱 완료 상태입니다.\n"
                f"지금 파일로 출력하면 미완료 구간은 실시간 연산하며 채워 넣으므로 다소 시간이 소요될 수 있습니다. 진행할까요?"
            )
            if not confirm: return

        save_folder = filedialog.askdirectory(title='사면 구문 BVE 저장 경로 선택')
        if not save_folder: return

        section_data =  None
        try:
            BVEExporter.initialize_files(save_folder)

            left_lines = []
            right_lines = []

            self.status_var.set("메모리 캐시 덤프 중...")
            self.config(cursor="watch")
            self.update_idletasks()

            for i in range(total_stations):
                with self.cache_lock:
                    section_data = self.cache_data.get(i)

                # 아직 캐싱 안 된 부위는 루프 내에서 가볍게 처리
                if not section_data:
                    section_data = self.processor.provider.get_section(i)
                    if section_data:
                        section_data['track_width'] = self.track_width
                        with self.cache_lock:
                            self.cache_data[i] = section_data

                if section_data:
                    track_width = self.track_width
                    left_distance = -(track_width / 2.0 + section_data['left_dist'])
                    right_distance = (track_width / 2.0 + section_data['right_dist'])

                    fh_z = section_data['center'][2]
                    left_level = section_data['slope_l'][1] - fh_z
                    right_level = section_data['slope_r'][1] - fh_z
                    station = section_data['station']

                    left_lines.append(f"{station},.rail 200;{left_distance:.3f};{left_level:.3f};86;\n")
                    right_lines.append(f"{station},.rail 201;{right_distance:.3f};{right_level:.3f};87;\n")

            # 대량 버퍼 디스크 파일 쓰기 (1초 마법 구간)
            with open(os.path.join(save_folder, '사면좌.txt'), 'w', encoding='utf-8') as f:
                f.writelines(left_lines)
            with open(os.path.join(save_folder, '사면우.txt'), 'w', encoding='utf-8') as f:
                f.writelines(right_lines)

            self.config(cursor="")
            self.status_var.set("BVE 내보내기 1초 컷 성공!")
            messagebox.showinfo("성공", f"전구간({total_stations}개) 사면 구문이 메모리 덤프 방식으로 초고속 저장되었습니다.")

        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("오류", str(e))

    def export_to_dxf(self):
        if not self.data:
            messagebox.showerror('에러', '저장할 횡단 데이터가 없습니다.')
            return
        try:
            default_name = f"Section_{int(self.data['station'])}.dxf"
            save_file = filedialog.asksaveasfilename(title='DXF 도면 저장', initialfile=default_name,
                                                     filetypes=[("AutoCAD DXF", "*.dxf")])
            if not save_file: return

            self.data['track_width'] = self.track_width
            DXFExporter.export_section(save_file, self.data)
            self.status_var.set(f"DXF 도면 내보내기 성공: {default_name}")
            messagebox.showinfo("성공", f"횡단면 도면이 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("dxf 저장 오류", str(e))

    def _jump_to_station(self):
        if self.processor is None: return
        search_val = self.ent_search.get().strip()
        if not search_val: return
        try:
            stations_arr = np.array(self.processor.stations, dtype=float)
            input_station = float(search_val)
            target_idx = int(np.argmin(np.abs(stations_arr - input_station)))

            if 0 <= target_idx < len(self.processor.read_coords):
                self.slider.set(target_idx)
            else:
                messagebox.showerror("범위 초과", f"존재하지 않는 측점입니다.")
        except Exception as e:
            messagebox.showerror("검색 오류", str(e))

    def show_3dmesh(self):
        if self.data:
            visualizer = SectionVisualizer()
            visualizer.verify_section_3d(self.data, self.data['terrain_mesh'], self.data['slope_left_mesh'],
                                         self.data['slope_right_mesh'])
        else:
            messagebox.showerror('에러', '데이터가 없습니다.')

    def _draw_chart(self, data):
        self.plotter.draw_chart(data)

    def _on_closing(self):
        """창이 닫힐 때 백그라운드 스레드를 안전하게 종료"""
        self.stop_caching = True
        self.destroy()