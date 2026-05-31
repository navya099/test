import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
from scipy.interpolate import interp1d
import numpy as np
import tkinter as tk
from tkinter import filedialog, Scale, Button, Checkbutton, IntVar
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
# 전역 변수들
drawing = False
modifying = False
adding_vertex = False
file_points = []
user_points = []
selected_point = None
first_point_drawn = False  # 첫 번째 점을 그렸는지 여부 추적
selected_line = None  # 선택된 선을 저장할 전역 변수

def update_graph(value):
    target_x = scale.get()  # 슬라이더의 현재 값 가져오기

    # 해당 x 좌표에 대한 보간된 y 좌표 찾기
    target_y = f(target_x)

    # 그래프 업데이트
    ax.clear()
    ax.plot(file_x, file_y, label='File Polyline')
    if user_points:
        user_line = LineString(user_points)
        ux, uy = user_line.xy
        ax.plot(ux, uy, label='User Polyline')
    ax.scatter(target_x, target_y, color='red', label='Target Point')
    ax.legend()
    canvas.draw()
    print(f'Y={target_y:.2f}')

def on_click(event):
    global drawing, modifying, user_points, selected_point, first_point_drawn, adding_vertex

    if drawing:
        if not first_point_drawn:  # 첫 번째 점을 아직 그리지 않은 경우
            user_points.append((event.xdata, event.ydata))
            first_point_drawn = True
        else:
            user_points.append((event.xdata, event.ydata))
            redraw()
        print_user_points_and_slopes()
    elif modifying:
        if adding_vertex:
            nearest_segment = find_nearest_segment(event.xdata, event.ydata)
            if nearest_segment is not None:
                user_points.insert(nearest_segment + 1, (event.xdata, event.ydata))
                redraw()
                print_user_points_and_slopes()
        else:
            selected_point = find_nearest_point(event.xdata, event.ydata)

def draw_mode():
    global drawing, modifying, first_point_drawn
    drawing = True
    modifying = False
    first_point_drawn = False  # draw 모드 진입 시 첫 번째 점 재설정
    
def on_motion(event):
    global user_points, selected_point

    if modifying and selected_point is not None:
        user_points[selected_point] = (event.xdata, event.ydata)
        redraw()

def on_release(event):
    global selected_point
    selected_point = None
    print_user_points_and_slopes()

def find_nearest_point(x, y):
    distances = [(i, np.hypot(px - x, py - y)) for i, (px, py) in enumerate(user_points)]
    nearest_point = min(distances, key=lambda t: t[1])
    if nearest_point[1] < 0.1:  # 가까운 점 기준
        return nearest_point[0]
    return None

def find_nearest_segment(x, y):
    min_dist = float('inf')
    nearest_segment = None
    for i in range(len(user_points) - 1):
        line = LineString([user_points[i], user_points[i + 1]])
        dist = line.distance(Point(x, y))
        if dist < min_dist:
            min_dist = dist
            nearest_segment = i
    return nearest_segment

def redraw():
    ax.clear()
    ax.plot(file_x, file_y, label='File Polyline')
    if user_points:
        if len(user_points) > 1:  # 두 개 이상의 점이 있는 경우에만 LineString 생성
            user_line = LineString(user_points)
            ux, uy = user_line.xy
            ax.plot(ux, uy, 'o-', picker=5,label='User Polyline')
        else:  # 첫 번째 점만 있는 경우, 해당 점만 표시
            ax.scatter(user_points[0][0], user_points[0][1], color='blue', label='User Point')
    canvas.draw()

def modify_mode():
    global drawing, modifying, user_points, draggable_line

    drawing = False
    modifying = True

    # 기존의 그래프에 DraggableLine 추가
    draggable_line = DraggableLine(ax.lines[1])  # user polyline line을 수정 가능하도록 설정

class DraggableLine:
    def __init__(self, line):
        self.line = line
        self.xs = line.get_xdata()
        self.ys = line.get_ydata()
        self.press = None
        self.background = None

        self.connect()

    def connect(self):
        self.cidpress = self.line.figure.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidrelease = self.line.figure.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self.line.figure.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)

    def on_press(self, event):
        if event.inaxes != self.line.axes: return
        contains, _ = self.line.contains(event)
        if not contains: return

        self.press = (self.xs, self.ys), event.xdata, event.ydata
        self.background = self.line.figure.canvas.copy_from_bbox(self.line.axes.bbox)
        self.ind = np.argmin(np.sqrt((self.xs - event.xdata)**2 + (self.ys - event.ydata)**2))
        self.offset_x = self.xs[self.ind] - event.xdata
        self.offset_y = self.ys[self.ind] - event.ydata

    def on_motion(self, event):
        if self.press is None: return
        if event.inaxes != self.line.axes: return

        (xs, ys), xpress, ypress = self.press

        self.xs[self.ind] = event.xdata + self.offset_x
        self.ys[self.ind] = event.ydata + self.offset_y

        self.line.set_data(self.xs, self.ys)

        self.line.figure.canvas.restore_region(self.background)
        self.line.axes.draw_artist(self.line)
        self.line.figure.canvas.blit(self.line.axes.bbox)
        
        # 중간 기울기 업데이트
        self.update_slope()

    def on_release(self, event):
        self.press = None
        self.line.figure.canvas.draw()
        print_user_points_and_slopes()

    def disconnect(self):
        if self.line is not None:
            self.line.figure.canvas.mpl_disconnect(self.cidpress)
            self.line.figure.canvas.mpl_disconnect(self.cidrelease)
            self.line.figure.canvas.mpl_disconnect(self.cidmotion)
            self.line = None  # self.line을 None으로 설정하여 on_release 메서드에서 에러 방지

    def update_slope(self):
        # 각 세그먼트의 중간 기울기를 계산하고 텍스트로 표시
        ax = self.line.axes
        for i, text in enumerate(ax.texts):
            text.remove()  # 기존 텍스트 제거
        for i in range(len(self.xs) - 1):
            x1, y1 = self.xs[i], self.ys[i]
            x2, y2 = self.xs[i + 1], self.ys[i + 1]
            slope = (y2 - y1) / (x2 - x1)
            midpoint_x = (x1 + x2) / 2
            midpoint_y = (y1 + y2) / 2
            ax.text(midpoint_x, midpoint_y, f"Slope: {slope*1000:.2f} %", fontsize=8, ha='center', va='center')
            print(f"Segment {i}-{i+1} Slope: {slope*1000:.2f} %")
            print(f"Segment {i} station =  {x1:.2f}, fl = {y1:.2f}")
        # 마지막 세그먼트 처리
        x1, y1 = self.xs[-2], self.ys[-2]
        x2, y2 = self.xs[-1], self.ys[-1]
        print(f"Segment {len(self.xs)-1} station = {x2:.2f}, fl = {y2:.2f}")

        # txt 파일로 저장
        txt = ""  # 파일에 쓸 문자열 초기화
        for i in range(len(self.xs)):
            txt += f"{self.xs[i]:.2f},.pitch "
            if i < len(self.xs) - 1:
                slope = (self.ys[i + 1] - self.ys[i]) / (self.xs[i + 1] - self.xs[i])
                txt += f"{slope*1000:.2f};\n"
        with open(save_path, "w",encoding='utf-8') as f:
            f.write(txt)


def erase_mode():
    global user_points, draggable_line

    user_points = []
    redraw()

    # DraggableLine 제거
    draggable_line.disconnect()

def add_vertex_mode():
    global adding_vertex
    adding_vertex = not adding_vertex  # 체크박스 토글

def print_user_points_and_slopes():
    pass
    '''
    if user_points:
        print("User Polyline Points and Slopes:")
        for i in range(len(user_points)):
            print(f"Point {i}: x={user_points[i][0]:.2f}, y={user_points[i][1]:.2f}")
            if i < len(user_points) - 1:
                x1, y1 = user_points[i]
                x2, y2 = user_points[i + 1]
                slope = (y2 - y1) / (x2 - x1)
                print(f"Segment {i}-{i+1} Slope: {slope:.2f}")
    else:
        print("No user points to display.")
    '''
# tkinter 애플리케이션 생성
root = tk.Tk()

# 파일 선택 대화창 열기
file_path = filedialog.askopenfilename(title="파일 선택", filetypes=[("텍스트 파일", "*.txt")])

if file_path:

    # 선택한 파일의 경로에서 디렉토리 부분과 파일 이름 부분을 분리합니다.
    directory, filename = os.path.split(file_path)
    
    # 새 파일의 저장 경로를 선택한 파일의 디렉토리와 동일하도록 설정합니다.
    save_path = os.path.join(directory, "bveprofile.txt")
    
    try:
        # 선택한 파일 열기 및 데이터 읽기
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # 첫 줄이 헤더인지 확인
        first_line = lines[0].strip().split()
        try:
            # 헤더가 아닌 경우(숫자인 경우), 첫 줄도 포함하여 처리
            x, y = map(float, first_line)
            file_points.append((x, y))
            start_index = 1
        except ValueError:
            # 헤더인 경우, 첫 줄 건너뛰기
            start_index = 1

        # 나머지 줄 처리
        for line in lines[start_index:]:
            x, y = map(float, line.strip().split(','))
            file_points.append((x, y))

        # LineString 생성
        file_line = LineString(file_points)

        # x와 y 좌표 추출
        file_x, file_y = file_line.xy

        # 보간 함수 생성
        f = interp1d(file_x, file_y, kind='linear')

        # 슬라이더 생성
        scale = Scale(root, from_=min(file_x), to=max(file_x), orient='horizontal', resolution=0.01, command=update_graph)
        scale.pack()

        # 그래프 생성
        fig, ax = plt.subplots()
        ax.plot(file_x, file_y, label='File Polyline')
        ax.set_aspect('auto')
        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.get_tk_widget().pack()
        canvas.draw()

        # 버튼 추가
        draw_button = Button(root, text="Draw", command=draw_mode)
        draw_button.pack(side=tk.LEFT)

        modify_button = Button(root, text="Modify", command=modify_mode)
        modify_button.pack(side=tk.LEFT)

        erase_button = Button(root, text="Erase", command=erase_mode)
        erase_button.pack(side=tk.LEFT)

        # 체크박스 추가
        add_vertex_var = IntVar()
        add_vertex_checkbox = Checkbutton(root, text="Add Vertex", variable=add_vertex_var, command=add_vertex_mode)
        add_vertex_checkbox.pack(side=tk.LEFT)

        # 마우스 이벤트 연결
        canvas.mpl_connect("button_press_event", on_click)
        canvas.mpl_connect("motion_notify_event", on_motion)
        canvas.mpl_connect("button_release_event", on_release)

        # tkinter 애플리케이션 실행
        root.mainloop()

    except FileNotFoundError:
        print("파일을 찾을 수 없습니다.")
    except Exception as e:
        print("파일을 읽는 중 오류가 발생했습니다:", e)
else:
    print("파일 선택이 취소되었습니다.")
