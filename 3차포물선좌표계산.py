import math
from modules.math_utils import degrees_to_dms, calculate_bearing, calculate_coordinates, calculate_distance
from modules.utils import format_distance
from matplotlib.widgets import Slider ,TextBox
import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, TextBox
import numpy as np
import math

class AlignmentCalculator:
    def __init__(self, BP, IP, EP, R, M, V, C, BP_STA):
        self.BP = BP
        self.IP = IP
        self.EP = EP
        self.R = R      # 원곡선 반경
        self.M = M      # 캔트배수
        self.V = V      # 설계속도
        self.C = C      # 캔트
        self.SP = []
        self.PC = []
        self.CP = []
        self.PS = []
        self.BP_STA = BP_STA

    def basic_cal(self):
        # 기본 완화곡선 계산
        self.X1 = self.M * self.C
        self.Y1 = self.X1 ** 2 / (6 * self.R)
        self.T = math.atan(self.X1 / (2 * self.R))
        self.T_dms = degrees_to_dms(math.degrees(self.T))

        # 방위각 계산
        self.q1 = calculate_bearing(*self.BP, *self.IP)
        self.q2 = calculate_bearing(*self.IP, *self.EP)
        self.q1_reverse = calculate_bearing(*self.IP, *self.BP)
        self.q2_reverse = calculate_bearing(*self.EP, *self.IP)

        #거리계산
        self.d1 = calculate_distance(self.BP, self.IP)
        self.d2 = math.sqrt((self.EP[0] - self.IP[0])**2 + (self.EP[1] - self.IP[1])**2)

        #교각
        self.ia = abs(self.q1 - self.q2)
        #원곡선교각
        self.ia2 = self.ia - 2 * self.T

        #방향
        self.direction = self.define_direction(self.q1, self.q2)

        # 파생 변수
        self.f = self.Y1 - (self.R * (1 - math.cos(self.T))) #이정량F
        self.k = self.f * math.tan(self.ia / 2) #수평좌표차K
        self.cl = self.R * (self.ia - 2 * self.T) #원곡선장
        self.L = self.X1 * (1 + 0.1 * (math.tan(self.T) ** 2)) #완화곡선장
        self.X2 = self.X1 - (self.R * math.sin(self.T))
        self.TL = self.R * math.tan(self.ia / 2) + self.X2 + self.k #접선장
        self.CL1 = self.cl + 2 * self.L #전체곡선장


    def calculate_sp(self):
        N = self.TL * math.cos(self.q1_reverse)
        E = self.TL * math.sin(self.q1_reverse)
        X = self.IP[0] + N
        Y = self.IP[1] + E
        self.SP = X, Y

    def calculate_ps(self):
        N = self.TL * math.cos(self.q2)
        E = self.TL * math.sin(self.q2)
        X = self.IP[0] + N
        Y = self.IP[1] + E
        self.PS = X, Y

    @staticmethod
    def define_direction(dir1, dir2):
        minus = math.sin(dir2 - dir1)
        return -1 if minus < 0 else 1

    def calculate_pc(self):

        s = math.sqrt(self.X1 ** 2 + self.Y1 ** 2)
        innerangle = math.atan(self.Y1 / self.X1)
        direction = self.define_direction(self.q1, self.q2)
        azimuth = self.q1 + innerangle * direction

        N = s * math.cos(azimuth)
        E = s * math.sin(azimuth)
        X = self.SP[0] + N
        Y = self.SP[1] + E
        self.PC =  X, Y

    def calculate_cp(self):

        s = math.sqrt(self.X1 ** 2 + self.Y1 ** 2)
        innerangle = math.atan(self.Y1 / self.X1)
        direction = self.define_direction(self.q1, self.q2)
        azimuth = self.q2_reverse - innerangle * direction

        N = s * math.cos(azimuth)
        E = s * math.sin(azimuth)
        X = self.PS[0] + N
        Y = self.PS[1] + E
        self.CP =  X, Y

    def calculate_target_coord(self, target_sta):
        if target_sta < self.SP_STA: #시작 직선
            section = 'start_line'
            return self.calculate_target_coord_by_line(target_sta, self.BP_STA, self.BP, self.q1)
        elif target_sta > self.PS_STA:
            section = 'end_line'
            return self.calculate_target_coord_by_line(target_sta, self.PS_STA, self.PS, self.q2)
        elif self.SP_STA <= target_sta <= self.PC_STA:
            section = 'start_spiral'
            #print('section : start_spiral')
            return self.calculate_target_coord_by_spiral(target_sta, self.SP_STA, self.SP, self.q1, flag=section)
        elif self.CP_STA <= target_sta <= self.PS_STA:
            section = 'end_spiral'
            #print(f'section : {section}')
            return self.calculate_target_coord_by_spiral(target_sta, self.PS_STA, self.PS, self.q2_reverse, flag=section)
        else:
            section = 'curve'
            #print('section : curve')
            return self.calculate_target_coord_by_simplecurve(target_sta)

    def calculate_target_coord_by_line(self, target_sta, start_sta, start_point, start_bearing):
        l = target_sta - start_sta
        result = calculate_coordinates(*start_point, start_bearing, l)
        return result

    def calculate_target_coord_by_spiral(self, target_sta, start_sta, start_point, start_bearing, flag=''):
        """
        스파이럴 구간 좌표 계산 (SP~PC 또는 CP~PS 모두 지원)
        Args:
            target_sta: 목표 측점
            start_sta: 구간 시작 측점 (SP 또는 CP)
            start_point: 구간 시작 좌표 (SP 또는 CP)
            start_bearing: 구간 시작 방위각 (q1 또는 q2)
            flag: 플래그
        """
        l = abs(target_sta - start_sta)  # 곡선거리
        x = l - (l ** 5) / (40 * self.R ** 2 * self.L ** 2)
        y = (x ** 3) / (6 * self.R * self.X1)

        s = math.sqrt(x ** 2 + y ** 2)
        q = math.atan(x ** 2 / (6 * self.R * self.X1))
        # 편기각 근사
        #print(f'편기각: {(math.degrees(q))}')
        t = (l **2) / (6 * self.R * self.L) *3 # 접선각
        #print(f'접선각: {math.degrees(t)}')
        if flag == 'start_spiral':
            q2 = start_bearing + q
        else:
            q2 = start_bearing - q
        #print(f'방위각: {degrees_to_dms(math.degrees(q2) - 90)}')
        N = s * math.cos(q2)
        E = s * math.sin(q2)

        X = start_point[0] + N
        Y = start_point[1] + E
        return X, Y

    def calculate_target_coord_by_simplecurve(self, target_sta):
        l = target_sta - self.PC_STA  # 곡선거리
        #직선거리
        s = 2 * self.R * math.sin(
            ((l / self.cl) * self.ia2 ) / 2
        )
        q = l / self.R  * (1 / 2)#편기각
        #print(f'편기각: {degrees_to_dms(math.degrees(q))}')
        t = self.q1 - self.T - (2 * q) #접선방위각
        #print(f'접선방위각: {degrees_to_dms(math.degrees(t) -90)}')
        if self.direction == -1:
            q2 = self.q1 - self.T - q #방위각
        else:
            q2 = self.q1 + self.T + q  # 방위각
        #print(f'방위각: {degrees_to_dms(math.degrees(q2) -90)}')

        N = s * math.cos(q2)
        E = s * math.sin(q2)
        X = self.PC[0] + N
        Y = self.PC[1] + E
        return X, Y

    def compute_all(self):
        #기본 제원 계산
        self.basic_cal()

        # SP, PS 좌표
        self.calculate_sp()
        self.calculate_ps()

        # PC, CP 좌표
        self.calculate_pc()
        self.calculate_cp()

        # 측점
        self.IP_STA = self.BP_STA + self.d1
        self.SP_STA = self.IP_STA - self.TL
        self.PC_STA = self.SP_STA + self.L
        self.CP_STA = self.PC_STA + self.cl
        self.PS_STA = self.CP_STA + self.L
        D = math.sqrt(
            (self.EP[0] - self.PS[0]) ** 2 + (self.EP[1] - self.PS[1]) ** 2
        )

        self.EP_STA = self.PS_STA + D


        return {
            'BP': self.BP,
            'SP': self.SP,
            'PS': self.PS,
            'PC': self.PC,
            'CP': self.CP,
            'EP': self.EP,
            'BP_STA': self.BP_STA,
            'SP_STA': self.SP_STA,
            'PC_STA': self.PC_STA,
            'CP_STA': self.CP_STA,
            'PS_STA': self.PS_STA,
            'EP_STA': self.EP_STA
        }

class AlignmentPlotter:
    def __init__(self, alignment_calc):
        """
        Args:
            alignment_calc: AlignmentCalculator 객체
        """
        self.calc = alignment_calc

    def sample_curve(self, SP_STA, PS_STA, num_points=100):
        """
        완화곡선 구간을 num_points로 샘플링하여 좌표 리스트 생성
        """
        sta_values = np.linspace(SP_STA, PS_STA, num_points)
        curve_coords = [self.calc.calculate_target_coord(sta) for sta in sta_values]
        return curve_coords

    def plot_curve_with_slider_and_textbox(self, results):
        """
        슬라이더와 TextBox를 이용해 target_sta를 실시간 변경하며 플롯 표시
        """
        # 직선 구간 시작점
        curve_coords = [results['BP']]

        # 곡선 구간 샘플링
        curve_coords += self.sample_curve(results['SP_STA'], results['PS_STA'], num_points=1000)

        # 직선 구간 끝점
        curve_coords.append(results['EP'])

        curve_x = [c[0] for c in curve_coords]
        curve_y = [c[1] for c in curve_coords]

        # 주요 점
        major_points = {
            'BP': results['BP'],
            'SP': results['SP'],
            'PC': results['PC'],
            'CP': results['CP'],
            'PS': results['PS'],
            'EP': results['EP'],
        }

        # 초기 target_sta (중앙값)
        init_sta = (results['BP_STA'] + results['EP_STA']) / 2
        target_coord = self.calc.calculate_target_coord(init_sta)

        # figure / axis
        fig, ax = plt.subplots(figsize=(10, 8))
        plt.subplots_adjust(bottom=0.35)  # TextBox 공간 확보

        # 곡선 그리기
        ax.plot(curve_x, curve_y, '-', color='blue', label='Curve Path')

        # 주요 점 표시
        for name, coord in major_points.items():
            ax.plot(coord[0], coord[1], 'o', markersize=8, color='green')
            ax.text(coord[0], coord[1], f'{name}', fontsize=10, ha='right', va='bottom', color='black')

        # target point
        target_point, = ax.plot(target_coord[0], target_coord[1], 'x', markersize=10, color='red', label='Target')

        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_title('Alignment Curve Visualization with Slider & TextBox')
        ax.axis('equal')
        ax.grid(True)
        ax.legend()

        # --------------------
        # Slider
        ax_slider = plt.axes([0.15, 0.2, 0.7, 0.03])
        sta_slider = Slider(
            ax=ax_slider,
            label='Target STA',
            valmin=results['BP_STA'],
            valmax=results['EP_STA'],
            valinit=init_sta,
            valstep=1.0,
        )

        # TextBox
        ax_text = plt.axes([0.15, 0.1, 0.2, 0.05])
        sta_textbox = TextBox(ax_text, 'Direct STA', initial=f'{init_sta:.2f}')

        # --------------------
        updating = False  # 전역/클로저 변수

        def update_target(new_sta):
            nonlocal updating
            if updating:
                return
            updating = True
            # 값 범위 제한
            new_sta = max(results['BP_STA'], min(results['EP_STA'], float(new_sta)))
            new_coord = self.calc.calculate_target_coord(new_sta)
            target_point.set_xdata([new_coord[0]])
            target_point.set_ydata([new_coord[1]])
            fig.canvas.draw_idle()
            print(f"Target STA: {new_sta:.2f}, Coord: ({new_coord[0]:.3f}, {new_coord[1]:.3f})")

            # 슬라이더와 TextBox 동기화
            sta_slider.set_val(new_sta)
            sta_textbox.set_val(f'{new_sta:.2f}')
            updating = False

        # Slider 이벤트
        def slider_update(val):
            update_target(val)

        sta_slider.on_changed(slider_update)

        # TextBox 이벤트
        def textbox_submit(text):
            update_target(text)

        sta_textbox.on_submit(textbox_submit)

        plt.show()


# -----------------------------
# GUI 통합
# -----------------------------
class AlignmentGUI:
    def __init__(self, master):
        self.master = master
        master.title("BVE Alignment Calculator")
        # 기본값 초기화 (프로그램 전체에서 유지)
        self.settings_values = {
            "BP X": 240574.609, "BP Y": 474571.811,
            "IP X": 241154.550, "IP Y": 474800.296,
            "EP X": 243732.851, "EP Y": 477831.087,
            "R": 2000, "M": 1300, "V": 150, "C": 0.133,
            "BP_STA": 45199.9998
        }
        # 설정 버튼
        tk.Button(master, text="Alignment 설정", command=self.open_settings_window, width=25, height=2).pack(pady=20)

    def open_settings_window(self):
        self.settings_win = tk.Toplevel(self.master)
        self.settings_win.title("Alignment Settings")

        labels = list(self.settings_values.keys())
        self.entries = []

        for i, label in enumerate(labels):
            tk.Label(self.settings_win, text=label).grid(row=i, column=0, padx=5, pady=3, sticky="e")
            entry = tk.Entry(self.settings_win)
            entry.grid(row=i, column=1, padx=5, pady=3)
            entry.insert(0, str(self.settings_values[label]))  # 마지막 값 사용
            self.entries.append(entry)

        tk.Button(self.settings_win, text="설정 적용", command=self.apply_settings).grid(row=len(labels), column=0, columnspan=2, pady=10)

    def apply_settings(self):
        try:
            # Entry 값 읽어서 settings_values 업데이트
            labels = list(self.settings_values.keys())
            for label, entry in zip(labels, self.entries):
                self.settings_values[label] = float(entry.get())

            # AlignmentCalculator 생성
            BP = (self.settings_values["BP X"], self.settings_values["BP Y"])
            IP = (self.settings_values["IP X"], self.settings_values["IP Y"])
            EP = (self.settings_values["EP X"], self.settings_values["EP Y"])
            R_val = self.settings_values["R"]
            M_val = self.settings_values["M"]
            V_val = self.settings_values["V"]
            C_val = self.settings_values["C"]
            BP_STA_val = self.settings_values["BP_STA"]

            self.calc = AlignmentCalculator(BP, IP, EP, R_val, M_val, V_val, C_val, BP_STA_val)
            self.results = self.calc.compute_all()
            if self.calc.PC_STA < self.calc.SP_STA:
                messagebox.showerror('에러','유효하지 않은 완화곡선입니다., 제원을 변경하세요')
                return

            # SP, PC, CP, PS 출력
            print('-----완화곡선제원출력-----')
            print(f'방위각1 : {degrees_to_dms((math.degrees(self.calc.q1) -90))}')
            print(f'방위각2 : {degrees_to_dms((math.degrees(self.calc.q2) -90))}')
            print(f'교각 IA : {degrees_to_dms((math.degrees(self.calc.ia)))}')
            print(f"곡선방향 : {'LEFT CURVE' if self.calc.direction == 1 else 'RIGHT CURVE'}")
            print(f'완화곡선 길이 L : {self.calc.L}')
            print(f'접선장 TL : {self.calc.TL}')
            print(f'곡선장 CL : {self.calc.CL1}')
            print("SP좌표:", self.results['SP'])
            print("PC좌표:", self.results['PC'])
            print("CP좌표:", self.results['CP'])
            print("PS좌표:", self.results['PS'])
            print(f"SP측점:, {format_distance(self.results['SP_STA'], 2)}")
            print(f"PC측점:, {format_distance(self.results['PC_STA'], 2)}")
            print(f"CP측점:, {format_distance(self.results['CP_STA'], 2)}")
            print(f"PS측점:, {format_distance(self.results['PS_STA'], 2)}")
            print(f"EP측점:, {format_distance(self.results['EP_STA'], 2)}")
            print()

            # Plotter 호출
            self.plot = AlignmentPlotter(self.calc)
            self.plot.plot_curve_with_slider_and_textbox(self.results)

            self.settings_win.destroy()

        except ValueError as ve:
            messagebox.showerror("Error", f"숫자를 입력하세요.\n{ve}")
        except Exception as e:
            messagebox.showerror("Error", f"잘못된 입력입니다.\n{e}")


# -----------------------------
# 실행
# -----------------------------
root = tk.Tk()
app = AlignmentGUI(root)
root.mainloop()