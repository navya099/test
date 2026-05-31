import math
import tkinter as tk
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from math_utils import calculate_distance, calculate_bearing, calculate_destination_coordinates
from tkinter import ttk, messagebox

class TangentSolver:
    def __init__(self, A, C, R):
        """
        A: 외부 점 (tuple, ex: (x, y))
        C: 원 중심 (tuple, ex: (x, y))
        R: 반지름 (float)
        """
        self.A = A
        self.C = C
        self.R = R

    def tangent_points(self):
        """외부 점 A에서 원에 접하는 두 접점 좌표를 반환"""
        xa, ya = self.A
        xc, yc = self.C
        x, y = sp.symbols('x y', real=True)

        eq1 = (x - xc)**2 + (y - yc)**2 - self.R**2
        eq2 = (x - xc)*(xa - x) + (y - yc)*(ya - y)

        sol = sp.solve([eq1, eq2], (x, y))
        return [(float(px), float(py)) for px, py in sol]

    def top_point(self, points):
        """y 좌표가 큰 접점을 반환 (위쪽 점)"""
        return max(points, key=lambda p: p[1])

    def visualize(self, points, top_point=None):
        """원, 점 A, 중심 C, 접점, 접선 시각화"""
        fig, ax = plt.subplots(figsize=(6,6))
        ax.set_aspect('equal')
        ax.grid(True)

        # 원
        circle = plt.Circle(self.C, self.R, fill=False, color='black', linestyle='--')
        ax.add_artist(circle)

        # 점 A, C
        ax.scatter(*self.A, color='blue')
        ax.text(self.A[0]+0.05, self.A[1], 'A', color='blue')

        ax.scatter(*self.C, color='red')
        ax.text(self.C[0]+0.05, self.C[1], 'C', color='red')

        # 접점 및 접선
        for i, P in enumerate(points):
            ax.scatter(*P, color='green')
            ax.text(P[0]+0.05, P[1], f'T{i+1}', color='green')
            ax.plot([self.A[0], P[0]], [self.A[1], P[1]], color='orange', label=f'Tangent {i+1}' if i==0 else None)

        if top_point:
            ax.plot([self.A[0], top_point[0]], [self.A[1], top_point[1]], 'r--', label='Top tangent')

        ax.legend()
        ax.set_title("Circle with tangent lines from A")
        plt.tight_layout()
        plt.show()


class TKINTER(tk.Tk):
    def __init__(self):
        super().__init__()
        self.result_length = tk.DoubleVar()
        self.result_angle = tk.DoubleVar()
        self.title("경사 주 파이프 계산기")

        # 입력 필드
        labels = [
            "#1 전주면에서 궤도중심까지의 거리 (-는 좌측):",
            "#2 전차선 높이:",
            "#3 가고:",
            "#4 조가선 현수클램프 치수:",
            "#5 조가선 파이프측 지지클램프 치수:",
            "#6 전차선 높이와 가동브래켓 중심점 높이 m:",
            "#7 전주면에서 파이프 시작점 수평거리 x:",
            "#8 편위:"
        ]
        defaults = [-2.947, 5.08, 1.4, 0.07, 0.11, 0.11, 0.275, -0.2]  # 원하는 기본값 리스트

        # Entry들을 인스턴스 속성으로 저장
        self.entries = {}
        for i, text in enumerate(labels):
            ttk.Label(self, text=text).grid(row=i, column=0, sticky="w")
            e = ttk.Entry(self)
            e.grid(row=i, column=1)
            e.insert(0, str(defaults[i]))  # 기본값 삽입
            self.entries[f"entry_{i+1}"] = e

        ttk.Button(self, text="계산하기", command=self.run_solver).grid(row=8, column=0, columnspan=2, pady=10)
        self.render = Render(self)

    def run_solver(self):
        try:
            # Entry 값 읽기
            dist = float(self.entries["entry_1"].get())
            height = float(self.entries["entry_2"].get())
            sysheight = float(self.entries["entry_3"].get())
            fitingh1 = float(self.entries["entry_4"].get())
            fitingh2 = float(self.entries["entry_5"].get())
            m = float(self.entries["entry_6"].get())
            fitingh3 = float(self.entries["entry_7"].get())
            stagger = float(self.entries["entry_8"].get())

            # 계산
            A = (dist + fitingh3, height + m)
            C = (stagger, height + sysheight + fitingh1)
            R = fitingh2

            solver = TangentSolver(A, C, R)
            points = solver.tangent_points()
            top_point = solver.top_point(points)

            angle = calculate_bearing(A, top_point)
            length = calculate_distance(A, top_point) + 0.15

            # 결과 표시
            self.result_angle.set(math.degrees(angle))
            self.result_length.set(length)


            self.data = [A, C, R, top_point, self.result_angle.get(), self.result_length.get(), self.entries]
            #messagebox.showinfo('계산 결과', f'경사 주 파이프 각도:{self.result_angle.get()}\n경사 주 파이프 길이:{self.result_length.get()}')

            self.render.plot_graph(self.data)

        except Exception as e:
            messagebox.showerror("Error", str(e))

class Render:
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        if not self.window:
            self._create_window()

    def _create_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("그래프 보기")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def plot_graph(self, data: list):
        if self.window is None or not self.window.winfo_exists():
            self._create_window()

        A, C, R, top_point, theta, length, entries = data

        self.ax.cla()
        self.ax.set_aspect('equal')
        self.ax.grid(True)

        # 원
        circle = plt.Circle(C, R, fill=False, color='black', linestyle='--')
        #ax.add_artist(circle)

        # 점 A, C
        self.ax.scatter(*A, color='blue')
        self.ax.text(A[0] + 0.05, A[1], 'A', color='blue')

        self.ax.scatter(*C, color='red')
        self.ax.text(C[0] + 0.05, C[1], 'C', color='red')

        # 접점
        self.ax.scatter(*top_point, color='green')
        self.ax.text(top_point[0] + 0.05, top_point[1], 'Top', color='green')

        dist = float(entries["entry_1"].get())
        height = float(entries["entry_2"].get())
        sysheight = float(entries["entry_3"].get())
        fitingh1 = float(entries["entry_4"].get())
        fitingh2 = float(entries["entry_5"].get())
        m = float(entries["entry_6"].get())
        fitingh3 = float(entries["entry_7"].get())
        stagger = float(entries["entry_8"].get())

        # A → top_point 직선
        B = calculate_destination_coordinates(A,bearing=math.radians(theta),distance=length)

        MW = calculate_destination_coordinates(C,bearing=-math.pi / 2,distance=fitingh1)#조가선
        self.ax.text(MW[0], MW[1], 'MW',color='blue')
        self.ax.scatter(MW[0], MW[1], color='green')

        CW = stagger, height
        self.ax.scatter(CW[0],CW[1], color='green')
        self.ax.text(CW[0], CW[1], 'CW', color='blue')

        self.ax.plot([A[0], B[0]], [A[1], B[1]], color='orange', label='Tangent')
        self.ax.plot([top_point[0], C[0]], [top_point[1], C[1]])
        self.ax.plot([C[0], MW[0]], [C[1], MW[1]])
        self.ax.legend()
        self.ax.set_title(f"θ={theta:.2f}°, Length={length:.3f}")
        self.canvas.draw()



if __name__ == '__main__':
    main = TKINTER()
    main.mainloop()
