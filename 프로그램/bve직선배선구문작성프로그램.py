from tkinter import ttk
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math
from AutoCAD.line import Line2d
from AutoCAD.point2d import Point2d
from tkinter import scrolledtext

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

class MainAPP(tk.Tk):
    def __init__(self):
        super().__init__()
        self.win = None
        self.title("BVE 간단 배선 작성 스크립트")
        self.geometry('500x500')
        self.start_var = tk.DoubleVar()
        self.end_var = tk.DoubleVar()
        self.start_x_var = tk.DoubleVar()
        self.end_x_var = tk.DoubleVar()
        self.railidx_var = tk.IntVar()

        tk.Label(self, text='시작 측점').pack()
        tk.Entry(self, textvariable=self.start_var).pack()
        tk.Label(self, text='끝 측점').pack()
        tk.Entry(self, textvariable=self.end_var).pack()
        tk.Label(self, text='시작 X').pack()
        tk.Entry(self, textvariable=self.start_x_var).pack()
        tk.Label(self, text='끝 X').pack()
        tk.Entry(self, textvariable=self.end_x_var).pack()
        tk.Label(self, text='레일인덱스').pack()
        tk.Entry(self, textvariable=self.railidx_var).pack()
        tk.Button(self, text="실행", command=self.run).pack(side='bottom', padx=10)
        tk.Button(self, text="종료", command=self.destroy).pack(side='bottom', padx=10)

        #self.init_plot()

    def init_plot(self):
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        toolbar_frame = tk.Frame(self)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        NavigationToolbar2Tk(self.canvas, toolbar_frame)

        self.ax.set_aspect('equal', adjustable='box')
        self.ax.grid(True)

    def run(self):
        # 1. 입력값 (x,y,z)
        start_station = self.start_var.get()
        end_station = self.end_var.get()
        start_x = self.start_x_var.get()
        end_x = self.end_x_var.get()
        railidx = self.railidx_var.get()

        start = Point2d(start_x, start_station)
        end = Point2d(end_x, end_station)
        line = Line2d(start, end)
        length = line.length
        block_size = 25
        block_count = int(length) // block_size
        angle = 90 - math.degrees(line.direction)
        # 3. 보간된 좌표 계산
        self.points = []
        for i in range(block_count + 1):
            station = start_station + i * 25
            p = Point2d(x=line.get_x_from_y(station), y=station)
            self.points.append(p)

        # 결과 문자열 생성
        result_text = ""
        for point in self.points:
            result_text += f"{point.y},.rail {railidx};{point.x};0;0;\n"

        # GUI 출력
        self.show_long_message(result_text)
        print(angle)
        #self.update_plot()

    def show_long_message(self, text):
        self.win = tk.Toplevel(self)
        self.win.title("BVE 코드")
        self.win.geometry("600x400")


        st = scrolledtext.ScrolledText(self.win, wrap="word")
        st.insert("1.0", text)
        st.config(state="disabled")
        st.pack(fill="both", expand=True)

        def copy_to_clipboard():
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()
            self.win.destroy()
        ttk.Button(self.win, text="복사하기", command=copy_to_clipboard).pack(side="left", padx=5, pady=5)
        ttk.Button(self.win, text="닫기", command=self.win.destroy).pack(side="right", padx=5, pady=5)

    def update_plot(self):
        self.ax.clear()
        # 5. 시각화
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        self.ax.plot(xs, ys, marker="o", linestyle="-", color="blue")
        self.canvas.draw()


if __name__ == '__main__':
    app = MainAPP()
    app.mainloop()