import tkinter as tk
from tkinter import filedialog, messagebox
from loggermodule import logger
from core import MainProcess


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("전주 처리 프로그램")
        self.geometry("500x200")
        self.wizard = None
        # "새 작업" 버튼
        self.new_task_button = tk.Button(self, text="새 작업", command=self.start_wizard)
        self.new_task_button.pack(pady=20)

        # "종료" 버튼
        self.exit_button = tk.Button(self, text="종료", command=self.close_application)
        self.exit_button.pack(pady=20)

        logger.info(f'MainWindow 초기화 완료')

    def start_wizard(self):
        """새 작업 마법사 창 시작"""
        self.wizard = TaskWizard(self)
        self.wizard.grab_set()  # 메인 창을 잠그고 마법사를 모달 창으로 설정

    def close_application(self):
        """프로그램 종료"""
        self.quit()


class TaskWizard(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("새 전주 생성 마법사")
        self.geometry("500x500")
        self.file_paths = [tk.StringVar() for _ in range(4)]
        self.step = 0
        self.mode = tk.StringVar()
        self.inputs = [tk.StringVar() for _ in range(4)]  # 4개의 입력에 대해 StringVar 초기화
        self.next_button = None  # Initialize next_button as None
        self.update_step()
        self.curve_info_path = None
        self.pitch_info_path = None
        self.coord_info_path = None
        self.structure_path = None

    def update_step(self):
        """현재 단계 UI 업데이트"""
        # 기존 위젯 제거
        for widget in self.winfo_children():
            widget.destroy()

        # 각 단계별 UI 구성
        if self.step == 0:
            self.select_file_paths()
            self.enable_next_button(True)

        elif self.step == 1:
            self.select_mode()
        elif self.step == 2:
            self.get_inputs()
            self.enable_next_button(True)  # 유효성 검사 후 '다음' 버튼 활성화
        elif self.step == 3:
            self.process_data()
        elif self.step == 4:
            tk.Label(self, text="마침", font=("Arial", 14)).pack(pady=10)
            tk.Label(self, text="모든 작업이 끝났습니다!", font=("Arial", 12)).pack(pady=10)

        # 버튼 프레임
        button_frame = tk.Frame(self)
        button_frame.pack(pady=20)

        if self.step > 0:
            tk.Button(button_frame, text="이전", command=self.prev_step).pack(side="left", padx=5)

        # '다음' 버튼 초기화
        if self.next_button:
            self.next_button.destroy()  # 이전에 있던 next_button을 제거합니다.

        if self.step < 4:
            self.next_button = tk.Button(button_frame, text="다음", command=self.next_step)
            self.next_button.pack(side="left", padx=5)
        else:
            tk.Button(button_frame, text="완료", command=self.finish_wizard).pack(side="left", padx=5)

        tk.Button(button_frame, text="취소", command=self.cancel).pack(side="right", padx=5)

    def enable_next_button(self, state):
        """'다음' 버튼 활성화/비활성화"""
        if self.next_button and self.next_button.winfo_exists():  # Ensure button exists
            self.next_button.config(state="normal" if state else "disabled")

    def next_step(self):
        """다음 단계로 이동"""
        if self.step == 2:
            if self.validate_inputs():  # 유효성 검사
                self.step += 1
                self.update_step()
            else:
                messagebox.showerror('에러', '입력값에 오류가 있습니다.')
        elif self.step == 4:
            self.finish_wizard()  # 마지막 단계에서는 마법사 완료 처리
            return
        elif self.step == 0:
            if all(path.get() for path in self.file_paths):
                self.step += 1
                self.update_step()
            else:
                logger.error('에러 : 파일이 선택되지 않았습니다.')
                messagebox.showerror('에러', '파일이 선택되지 않았습니다.')
                return
        elif self.step == 1:
            self.step += 1
            self.update_step()

        elif self.step == 3:
            self.step += 1
            self.update_step()

    def prev_step(self):
        """이전 단계로 이동"""
        if self.step > 0:
            self.step -= 1
            self.update_step()

    def cancel(self):
        """마법사 종료"""
        self.destroy()

    def select_file_paths(self):
        """Step 1: 파일 경로 선택"""
        tk.Label(self, text="단계1: 파일 선택", font=("Arial", 14)).pack(pady=10)

        file_tilte_list = [
            'curve_info.txt',
            'pitch_info.txt',
            'bve_coordinates.txt',
            'structure.xlsx'
        ]

        for i in range(len(file_tilte_list)):
            frame = tk.Frame(self)
            frame.pack(pady=5)

            tk.Label(frame, text=f"{file_tilte_list[i]}:").pack(side="left")
            entry = tk.Entry(frame, width=40, textvariable=self.file_paths[i])
            entry.pack(side="left", padx=5)
            button = tk.Button(frame, text="열기", command=lambda i=i: self.browse_file(i))
            button.pack(side="left")

        self.curve_info_path = self.file_paths[0]
        self.pitch_info_path = self.file_paths[1]
        self.coord_info_path = self.file_paths[2]
        self.structure_path = self.file_paths[3]

    def browse_file(self, i):
        """파일 선택 대화상자"""
        file_path = filedialog.askopenfilename()
        if file_path:
            logger.info(f"✅ 파일 선택됨: {file_path}")  # 디버깅용 출력
            self.file_paths[i].set(file_path)

    def select_mode(self):
        """Step 2: 모드 선택"""
        tk.Label(self, text="단계 2: 모드 선택", font=("Arial", 14)).pack(pady=10)

        for mode in ['기존 노선용', '새 노선용']:
            tk.Radiobutton(self, text=mode, variable=self.mode, value=mode).pack(pady=5)

    def get_inputs(self):
        """Step 3: 입력값 받기"""
        tk.Label(self, text="Step 3: Enter Details", font=("Arial", 14)).pack(pady=10)

        inputs_text_tilte = [
            '설계속도',
            '선로 갯수',
            '선로중심간격',
            '폴 방향',
        ]

        for i in range(len(inputs_text_tilte)):
            frame = tk.Frame(self)
            frame.pack(pady=5)

            tk.Label(frame, text=f"{inputs_text_tilte[i]}:").pack(side="left")
            entry = tk.Entry(frame, textvariable=self.inputs[i])  # textvariable로 inputs[i] 바인딩
            entry.pack(side="left", padx=5)

    def validate_inputs(self):
        """입력값 유효성 검사"""
        for i, input_var in enumerate(self.inputs):
            value = input_var.get().strip()  # 공백 제거

            # 각 입력값에 대해 타입 체크 및 유효성 검사
            if i == 0:  # '설계속도'
                if not value.isdigit():  # 숫자가 아닌 경우
                    messagebox.showerror("입력 오류", "설계속도는 숫자만 입력할 수 있습니다.")
                    return False  # 유효성 검사 실패
                if int(value) <= 0:  # 음수나 0은 불가능
                    messagebox.showerror("입력 오류", "설계속도는 0보다 큰 값이어야 합니다.")
                    return False  # 유효성 검사 실패

            elif i == 1:  # '선로 갯수'
                if not value.isdigit():
                    messagebox.showerror("입력 오류", "선로 갯수는 숫자만 입력할 수 있습니다.")
                    return False  # 유효성 검사 실패
                if int(value) < 1:  # 1 이상이어야 함
                    messagebox.showerror("입력 오류", "선로 갯수는 최소 1이어야 합니다.")
                    return False  # 유효성 검사 실패

            elif i == 2:  # '선로중심간격'
                try:
                    float_value = float(value)
                except ValueError:  # 숫자가 아닌 경우
                    messagebox.showerror("입력 오류", "선로중심간격은 숫자만 입력할 수 있습니다.")
                    return False  # 유효성 검사 실패
                if float_value <= 0:  # 0 이하일 수 없음
                    messagebox.showerror("입력 오류", "선로중심간격은 0보다 큰 값이어야 합니다.")
                    return False  # 유효성 검사 실패

            elif i == 3:  # '폴 방향'
                if value not in ['-1', '1']:  # 예시로, 방향을 특정 값으로 제한
                    messagebox.showerror("입력 오류", "폴 방향은 -1, 1 중 하나여야 합니다.")
                    return False  # 유효성 검사 실패

        return True  # 모든 검사 통과 시 True 반환

    def process_data(self):
        """Step 4: 데이터 처리"""
        tk.Label(self, text="Step 4: Processing Data", font=("Arial", 14)).pack(pady=10)

        results = self.process_files_and_inputs()
        tk.Label(self, text=f"Results: {results}", font=("Arial", 12)).pack(pady=20)

    def process_files_and_inputs(self):
        """파일과 입력값을 처리하는 함수"""

        # ✅ TaskWizard가 아닌, 필요한 데이터만 추출하여 MainProcess에 전달
        design_params = {
            "designspeed": int(self.inputs[0].get()),
            "linecount": int(self.inputs[1].get()),
            "lineoffset": float(self.inputs[2].get()),
            "poledirection": int(self.inputs[3].get()),
            "mode": 0 if self.mode.get() == '기존 노선용' else 1
        }

        file_paths = {
            "curve_path": self.file_paths[0].get(),
            "pitch_path": self.file_paths[1].get(),
            "coord_path": self.file_paths[2].get(),
            "structure_path": self.file_paths[3].get()
        }

        # ✅ GUI가 아닌 데이터만 MainProcess로 전달
        mainprocess = MainProcess(design_params, file_paths)
        mainprocess.run()

        return "Processing successful!"

    def finish_wizard(self):
        """마법사 완료 후 창 닫기"""
        self.destroy()
