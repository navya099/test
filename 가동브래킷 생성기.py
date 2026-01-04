import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import math

# matplotlib 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


# ---------- 유틸 함수 ----------
def get_line_length(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def get_x_from_y(x1, y1, x2, y2, y_input):
    if x2 == x1:  # 수직선 예외 처리
        return x1
    m = (y2 - y1) / (x2 - x1)
    b = y1 - m * x1
    return (y_input - b) / m

def get_y_from_x(x1, y1, x2, y2, x_input):
    if x2 == x1:  # 수직선 예외 처리
        return None
    m = (y2 - y1) / (x2 - x1)
    b = y1 - m * x1
    return m * x_input + b

def draw_pipe(ax, x1, x2, y1, y2, color="green"):
    ax.plot([x1, x2], [y1, y2], color=color)

# ---------- 클래스 ----------
class MAST:
    def __init__(self, mast_type, width, height, x1, y1, x2, y2):
        self.mast_type = mast_type
        self.width = width
        self.height = height
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.artists = []

    def draw_centerline(self, ax):
        line, = ax.plot([self.x1, self.x2], [self.y1, self.y2], 'r--',
                        label=f"{self.mast_type} Centerline")
        self.artists.append(line)

    def draw_outline(self, ax):
        coords = [
            ([self.x1 - self.width/2, self.x2 - self.width/2], [self.y1, self.y2]),
            ([self.x1 + self.width/2, self.x2 + self.width/2], [self.y1, self.y2]),
            ([self.x1 - self.width/2, self.x1 + self.width/2], [self.y2, self.y2]),
            ([self.x1 - self.width/2, self.x1 + self.width/2], [self.y1, self.y1]),
        ]
        for x, y in coords:
            line, = ax.plot(x, y, 'skyblue')
            self.artists.append(line)

    def remove(self):
        for artist in self.artists:
            artist.remove()
        self.artists.clear()

# ---------- 메인 GUI ----------
class PipeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Slider Control")
        self.root.geometry("400x400")

        # Plot 창
        self.plot_root = tk.Toplevel(root)
        self.plot_root.title("Plot Window")
        self.plot_root.geometry("600x600")

        self.fig, self.ax = plt.subplots()
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(self.plot_root)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        NavigationToolbar2Tk(self.canvas, toolbar_frame)

        # 슬라이더 생성
        self.create_slider("메인파이프길이", 0.1, 5, 0.1, 1)
        self.create_slider("경사파이프y", 0, 10, 0.01, 3.576)
        self.create_slider("경사파이프x", 0, 10, 0.01, 0)
        self.create_slider("보조파이프길이", 0.1, 5, 0.1, 1.3)
        self.create_slider("건식게이지", 2.1, 5, 0.01, 2.1)

        #설계제원 입력창 생성
        self.create_text_input_form('전차선높이')
        self.create_text_input_form('가고')

        self.update_plot()

    def create_slider(self, label, from_, to, resolution, init):
        slider = tk.Scale(self.root, label=label, from_=from_, to=to,
                          resolution=resolution, orient="horizontal",
                          length=300, command=self.update_plot)
        slider.set(init)
        slider.pack(padx=10, pady=5)
        setattr(self, f"slider_{label}", slider)

    def create_text_input_form(self, title: str):
        # 라벨 추가
        label = tk.Label(self.root, text=title, font=("Malgun Gothic", 12))
        label.pack(padx=10, pady=5)

        # 입력창 변수
        text_var = tk.DoubleVar()

        # 입력창 생성
        entry = tk.Entry(self.root, textvariable=text_var, width=30)
        entry.pack(padx=10, pady=5)
        setattr(self, f"text_var{title}", text_var)

    def update_plot(self, val=None):
        self.ax.clear()
        self.ax.set_xlim(-5, 5)
        self.ax.set_ylim(0, 12)
        system_height = float(self.text_var가고.get())
        RL = (0,0)

        TW = (0, float(self.text_var전차선높이.get()))
        MW = (0,TW[1] +  system_height)
        MAIN_PIPE_L = float(self.slider_메인파이프길이.get())
        SLOPE_PIPE_Y1 = float(self.slider_경사파이프y.get())
        SLOPE_PIPE_X2 = float(self.slider_경사파이프x.get())
        SUB_PIPE_L = float(self.slider_보조파이프길이.get())
        G = float(self.slider_건식게이지.get())

        # 전주
        mast = MAST("강관주", 0.264, 9, RL[0] - G, RL[1], RL[0] - G, RL[1] + 9)
        mast.draw_centerline(self.ax)
        mast.draw_outline(self.ax)

        # 메인 파이프
        MAIN_PIPE_X1, MAIN_PIPE_Y1 = RL[0] - G, MW[1]
        MAIN_PIPE_X2, MAIN_PIPE_Y2 = MAIN_PIPE_X1 + MAIN_PIPE_L, MW[1]
        draw_pipe(self.ax, MAIN_PIPE_X1, MAIN_PIPE_X2, MAIN_PIPE_Y1, MAIN_PIPE_Y2)

        # 경사 파이프
        draw_pipe(self.ax, MAIN_PIPE_X1, SLOPE_PIPE_X2, SLOPE_PIPE_Y1, MAIN_PIPE_Y2)

        # 보조 파이프
        SUB_PIPE_X1 = get_x_from_y(MAIN_PIPE_X1, SLOPE_PIPE_Y1, SLOPE_PIPE_X2, MAIN_PIPE_Y2, TW[1])
        SUB_PIPE_Y1 = TW[1]
        SUB_PIPE_X2, SUB_PIPE_Y2 = SUB_PIPE_X1 + SUB_PIPE_L, SUB_PIPE_Y1
        draw_pipe(self.ax, SUB_PIPE_X1, SUB_PIPE_X2, SUB_PIPE_Y1, SUB_PIPE_Y2)

        # 포인트 표시
        for point, label, color in [(RL, "RL", "black"), (TW, "TW", "red"), (MW, "MW", "blue")]:
            self.ax.scatter(point[0], point[1], color=color)
            self.ax.text(point[0], point[1], label, fontsize=12, ha='left', color=color)

        self.fig.canvas.draw_idle()

# 실행
if __name__ == "__main__":
    root = tk.Tk()
    app = PipeApp(root)
    root.mainloop()