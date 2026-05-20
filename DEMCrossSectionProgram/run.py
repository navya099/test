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
        self.track_type = '단선'
        self.track_distance = 4.3
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

        # 🚀 [신규 추가] 이전 측점 이동 버튼 (<)
        self.btn_prev = ttk.Button(self.ctrl_frame, text="<", width=3, command=lambda: self._move_step(-1))
        self.btn_prev.pack(side=tk.LEFT, padx=(5, 0))

        self.slider = ttk.Scale(self.ctrl_frame, from_=0, to=1, orient=tk.HORIZONTAL, command=self._on_slider_move)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # 🚀 [신규 추가] 다음 측점 이동 버튼 (>)
        self.btn_next = ttk.Button(self.ctrl_frame, text=">", width=3, command=lambda: self._move_step(1))
        self.btn_next.pack(side=tk.LEFT, padx=(0, 5))

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

        # 🚀 [보너스 편의기능] 키보드 좌우 방향키 핫키 바인딩 (프로그램 찍고 방향키 누르면 이동 가능)
        self.bind("<Left>", lambda event: self._move_step(-1))
        self.bind("<Right>", lambda event: self._move_step(1))

        # 창이 닫힐 때 백그라운드 스레드도 안전하게 죽도록 설정
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    # -------------------------------------------------------------
    # 🚀 [신규 제어 로직] 버튼 클릭 및 키보드 조작 시 1단계씩 이동하는 함수
    # -------------------------------------------------------------
    def _move_step(self, step):
        """현재 슬라이더 위치에서 수동으로 step 만큼 전후진 처리 (경계면 예외 포함)"""
        if self.processor is None:
            return

        total_count = len(self.processor.read_coords)
        current_val = int(self.slider.get())
        next_val = current_val + step

        # 0번 측점 미만이나 맨 마지막 측점 초과 시 가드 처리
        if 0 <= next_val < total_count:
            self.slider.set(next_val)  # Scale 값이 바뀌면서 _on_slider_move가 자동으로 호출됩니다.
    def show_option(self):
        """트랙 폭, 사면 기울기, 선로 종류(콤보박스) 및 중심간격을 설정하는 팝업 창"""
        option_win = tk.Toplevel(self)
        option_win.title("설정 옵션")
        option_win.geometry("320x350")  # 컴포넌트 추가에 따라 세로폭 살짝 확장
        option_win.resizable(False, False)
        option_win.grab_set()

        # 현재 클래스에 저장된 기존 설정값 로드
        current_width = getattr(self, 'track_width', 8.0)
        current_ratio = getattr(self, 'slope_ratio', 1.5)
        current_track_distance = getattr(self, 'track_distance', 4.3)
        current_track_type = getattr(self, 'track_type', '단선')

        # 1. 트랙 폭 입력창
        tk.Label(option_win, text="트랙 폭 (m):", font=("맑은 고딕", 9, "bold")).pack(pady=(15, 0))
        ent_width = ttk.Entry(option_win, width=20)
        ent_width.insert(0, str(current_width))
        ent_width.pack(pady=3)

        # 2. 사면 기울기 입력창
        tk.Label(option_win, text="사면 기울기 (1:n):", font=("맑은 고딕", 9, "bold")).pack(pady=(10, 0))
        ent_ratio = ttk.Entry(option_win, width=20)
        ent_ratio.insert(0, str(current_ratio))
        ent_ratio.pack(pady=3)

        # 3. 선로타입 콤보박스 선택창
        tk.Label(option_win, text="선로 타입 T:", font=("맑은 고딕", 9, "bold")).pack(pady=(10, 0))

        # ttk.Combobox 배치 (사용자가 임의 타이핑 못 하도록 state='readonly' 강제)
        combo_track_type = ttk.Combobox(option_win, values=['단선', '복선-하선', '복선-상선'], width=18, state='readonly')
        combo_track_type.set(current_track_type)
        combo_track_type.pack(pady=3)

        # 4. 선로중심간격 입력창
        tk.Label(option_win, text="선로중심간격 D (m):", font=("맑은 고딕", 9, "bold")).pack(pady=(10, 0))
        ent_track_distance = ttk.Entry(option_win, width=20)
        ent_track_distance.insert(0, str(current_track_distance))
        ent_track_distance.pack(pady=3)

        # 💡 [UI 인터랙션 가드] 단선일 때는 중심간격 입력창을 막고, 복선일 때만 풀어주는 함수
        def toggle_distance_entry(event=None):
            if combo_track_type.get() == "단선":
                ent_track_distance.config(state='disabled')
            else:
                ent_track_distance.config(state='normal')

        # 콤보박스 선택이 바뀔 때마다 위 토글 함수가 실행되도록 이벤트 바인딩
        combo_track_type.bind("<<ComboboxSelected>>", toggle_distance_entry)

        # 팝업창이 처음 켜질 때도 현재 상태에 맞춰 초기 상태 세팅 (단선이면 처음부터 disabled)
        toggle_distance_entry()

        # 5. 저장 및 캐시 갱신 로직
        def save_and_close():
            try:
                self.track_width = float(ent_width.get())
                self.slope_ratio = float(ent_ratio.get())
                self.track_type = combo_track_type.get()

                # 복선 계열일 때만 입력된 중심간격을 파싱, 단선이면 기존값 유지 혹은 0.0 처리
                if self.track_type != "단선":
                    self.track_distance = float(ent_track_distance.get())
                else:
                    self.track_distance = 0.0

                # 🚀 옵션이 바뀌면 데이터 왜곡을 막기 위해 기존 비동기 캐시 데이터를 싹 비움
                with self.cache_lock:
                    self.cache_data.clear()

                self.status_var.set(
                    f"옵션 변경 완료: 폭 {self.track_width}m, 기울기 1:{self.slope_ratio}, "
                    f"종류: {self.track_type}, 중심간격: {self.track_distance}m (캐시 재적재 가동)"
                )
                option_win.destroy()

                if self.processor:
                    # 현재 보고 있는 화면을 새 구배 정보로 강제 즉시 갱신 및 백그라운드 재가동
                    self._start_background_caching()
                    self.current_idx = -1
                    self._on_slider_move(self.slider.get())

            except ValueError:
                messagebox.showerror("입력 오류", "숫자 형식을 정확하게 입력해주세요.")

        # 적용 버튼 배치
        ttk.Button(option_win, text="적용", command=save_and_close).pack(pady=18)

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
            ui_input_data = {
                'read_file': read_file,
                'struct_file': struct_file,
                'track_width': self.track_width, #노반 폭
                'slope_ratio': self.slope_ratio, # 사면 기울기
                'track_distance': self.track_distance, #선로중심간격
                'track_type': self.track_type, #선로타입

            }
            self.processor = Processor(ui_input_data)
            self.processor.run()

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

    def export_to_bve(self):
        if self.processor is None:
            messagebox.showerror('에러', '로드된 데이터가 없습니다.')
            return

        total_stations = len(self.processor.read_coords)

        with self.cache_lock:
            cached_count = len(self.cache_data)

        # 1. 백그라운드가 다 돌았는지 여부 검사 및 유저 안내 인터페이스
        if cached_count < total_stations:
            confirm = messagebox.askyesno(
                "캐싱 미완료 안내",
                f"현재 전구간 중 {cached_count}/{total_stations}개 캐싱 완료 상태입니다.\n"
                f"지금 파일로 출력하면 미완료 구간은 실시간 연산하며 채워 넣으므로 다소 시간이 소요될 수 있습니다. 진행할까요?"
            )
            if not confirm: return

        self.status_var.set("BVE 저장 경로 확인중...")
        save_folder = filedialog.askdirectory(title='BVE 노선 스크립트 출력 폴더 선택')
        if not save_folder: return

        try:
            # 2. 락을 걸고 안전하게 현재까지 수집된 캐시 데이터의 스냅샷 복사
            with self.cache_lock:
                cache_snapshot = self.cache_data.copy()

            # 🚨 [치명적 버그 교정: 미완료 구간 실시간 강제 보충]
            # 스냅샷에 없는 인덱스가 있다면, 유저가 기다리는 동안 메인 스레드가 즉시 연산해서 스냅샷을 100% 꽉 채웁니다.
            if len(cache_snapshot) < total_stations:
                self.config(cursor="watch")  # 모래시계 커서 가동
                has_fast_mode = hasattr(self.processor.provider, 'get_section_fast')

                for i in range(total_stations):
                    if i not in cache_snapshot:
                        self.status_var.set(f"미완료 구간 실시간 연산 중... ({i}/{total_stations})")
                        self.update_idletasks()

                        # 고속 추출 모드가 있으면 활용, 없으면 일반 모드 백업
                        if has_fast_mode:
                            missing_data = self.processor.provider.get_section_fast(i)
                        else:
                            missing_data = self.processor.provider.get_section(i)

                        if missing_data:
                            missing_data['track_width'] = self.track_width
                            cache_snapshot[i] = missing_data

                            # 가로채서 연산한 귀한 결과물은 다음 슬라이더 조회를 위해 실제 전역 캐시에도 보충해 줍니다.
                            with self.cache_lock:
                                self.cache_data[i] = missing_data

            # 3. 고속 일괄 변환 처리기 작동 (이제 무조건 100% 꽉 찬 완벽한 데이터셋 보장)
            self.status_var.set("BVE 4종 스크립트 파일 덤프중...")
            self.update_idletasks()

            BVEExporter.export_all_sections(
                save_folder=save_folder,
                all_section_results=cache_snapshot,
                track_type=self.track_type,  # 예: "복선-하선"
                track_distance=self.track_distance,  # 예: 4.0
                track_width=self.track_width  # 예: 8.0
            )

            self.config(cursor="")  # 커서 원복
            messagebox.showinfo("성공", "사면좌, 사면우, height, ground 4종 파일이 일괄 생성되었습니다!")
            self.status_var.set("BVE 전구간 덤프 성공")

        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("오류", f"BVE 내보내기 중 장애 발생:\n{str(e)}")
            self.status_var.set("BVE 내보내기 오류")

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
            try:
                self.status_var.set("3D 시각화 구동 중... (메인 창 조작 제어)")

                # 1. 🚨 메인 윈도우의 마우스/키보드 이벤트를 잠시 비활성화 (포커스 가드)
                # 대안으로 grab_set을 쓸 수도 있으나, Toplevel이 아니므로 메인 창의 위젯 반응을 막음
                self.config(cursor="watch")

                # 기존 버튼들이 누락되지 않게 상단 제어바나 버튼을 잠시 disabled 시키는 것이 안전합니다.
                # 혹은 간단하게 윈도우 창 전체를 숨겼다가 다시 띄우는 편법도 실무에서 자주 쓰입니다.
                self.withdraw() # 창 숨기기 (선택 사항)

                visualizer = SectionVisualizer()

                # 2. PyVista 3D 창 구동 (유저가 이 창을 닫을 때까지 여기서 블로킹됨)
                visualizer.verify_section_3d(
                    self.data,
                    self.data['terrain_mesh'],
                    self.data['slope_left_mesh'],
                    self.data['slope_right_mesh']
                )

            except Exception as e:
                messagebox.showerror('3D 오류', f'시각화 중 오류가 발생했습니다:\n{str(e)}')
            finally:
                # 3. 🚨 PyVista 창이 닫히면 다시 메인 창을 정상 상태로 복구
                self.deiconify() # 창 다시 보이기 (위에서 숨겼을 경우)
                self.config(cursor="")
                self.status_var.set("3D 시각화 종료.")
                self.update()
        else:
            messagebox.showerror('에러', '데이터가 없습니다.')

    def _draw_chart(self, data):
        self.plotter.draw_chart(data)

    def _on_closing(self):
        """창이 닫힐 때 백그라운드 스레드를 안전하게 종료"""
        self.stop_caching = True
        self.destroy()