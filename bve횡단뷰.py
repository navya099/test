import math
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
from tkinter import Tk, Label, Button, StringVar, Entry, OptionMenu, filedialog
import csv
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk  # 추가
import tkinter as tk

# matplotlib 설정: 한글 폰트 및 마이너스 기호 지원
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 거리를 형식화하는 함수
def format_distance(number):
    try:
        number = float(number)
    except ValueError:
        print(f"형식 오류: {number}는 숫자가 아닙니다.")
        return str(number)

    is_negative = number < 0
    number = abs(number)
    
    km = int(number) // 1000
    remainder = number % 1000
    formatted_distance = f"{km}km{remainder:06.2f}"
    
    if is_negative:
        formatted_distance = "-" + formatted_distance
    
    return formatted_distance

# 텍스트 파일에서 지반고(GL) 정보 불러오기
def load_ground_levels():
    gl = []
    file_path = filedialog.askopenfilename(title="파일 선택", filetypes=[("텍스트 파일", "height_info.txt")])

    if not file_path:
        print("파일 선택이 취소되었습니다.")
        return gl
    
    try:
        with open(file_path, 'r', encoding='UTF-8') as file:
            reader = csv.reader(file)
            for row in reader:
                station = row[0]
                ground_elevation = float(row[1]) * -1 + elevation
                gl.append([station, ground_elevation])
    except FileNotFoundError:
        print("파일을 찾을 수 없습니다.")
    except Exception as e:
        print("파일을 읽는 중 오류가 발생했습니다:", e)

    #print("지반고(GL) 데이터:", gl)  # 디버깅 출력
    return gl

# 텍스트 파일에서 FL 정보 불러오기
def load_fl():
    fl = []
    file_path = filedialog.askopenfilename(title="파일 선택", filetypes=[("텍스트 파일", "bve_coordinates.txt")])

    if not file_path:
        print("파일 선택이 취소되었습니다.")
        return fl
    
    try:
        with open(file_path, 'r', encoding='UTF-8') as file:
            reader = csv.reader(file)
            for i, row in enumerate(reader):
                station = i * 25
                design_elevation = float(row[2]) + elevation
                fl.append([station, design_elevation])
    except FileNotFoundError:
        print("파일을 찾을 수 없습니다.")
    except Exception as e:
        print("파일을 읽는 중 오류가 발생했습니다:", e)

    #print("FL 데이터:", fl)  # 디버깅 출력
    return fl

# 비례식 계산 함수
def calculate_proportional_length(A, B):
    return (A / 100) * B

# 주어진 기점에서 주어진 경사로의 좌우 점을 구하는 함수
def calculate_slope_points(origin, length, slope_percent):
    half_length = length / 2
    vertical_change = calculate_proportional_length(slope_percent, half_length)

    left_point = Point(origin.x - half_length, origin.y - vertical_change)
    right_point = Point(origin.x + half_length, origin.y - vertical_change)
    return left_point, right_point

# 수선의 발 구하는 함수
def calculate_perpendicular_foot(A, B):
    x0, y0 = A.x, A.y
    x1, y1 = B.coords[0]
    x2, y2 = B.coords[1]
    
    dx, dy = x2 - x1, y2 - y1
    
    t = ((dx * (x0 - x1)) + (dy * (y0 - y1))) / (dx**2 + dy**2)
    
    x_p = x1 + t * dx
    y_p = y1 + t * dy
    
    return Point(x_p, y_p)

# 사면 경사 계산 함수
def calculate_slope_intersections(A, B, ground_line, slope, slope_type):
    P_A = calculate_perpendicular_foot(A, ground_line)
    P_B = calculate_perpendicular_foot(B, ground_line)
    
    nori_point_L_y = A.y - P_A.y
    nori_point_R_y = B.y - P_B.y
    
    distance_PA_C = nori_point_L_y * slope
    distance_PB_C = nori_point_R_y * slope

    if slope_type == 'fil':
        nori_point_L = Point(A.x - distance_PA_C, A.y - nori_point_L_y)
        nori_point_R = Point(B.x + distance_PB_C, B.y - nori_point_R_y)
    else:
        nori_point_L = Point(A.x + distance_PA_C, A.y - nori_point_L_y)
        nori_point_R = Point(B.x - distance_PB_C, B.y - nori_point_R_y)
    
    return nori_point_L, nori_point_R

# 횡단면도 시각화 함수
def plot_section(origin, left, right):
    x_values = [left.x, origin.x, right.x]
    y_values = [left.y, origin.y, right.y]
    ax.plot(x_values, y_values, color='skyblue', label='Section')

# 지반고(GL) 시각화 함수
def plot_ground_level(GL):
    x_values = [pt[0] for pt in GL]
    y_values = [pt[1] for pt in GL]
    ax.plot(x_values, y_values, 'g--', label='Ground Level (GL)')

# 두 점 사이의 각도 계산 함수
def calculate_angle(p1, p2):
    delta_y = p2.y - p1.y
    delta_x = p2.x - p1.x
    angle = np.arctan2(delta_y, delta_x) * (180 / np.pi)
    return angle

# 각도 텍스트 추가 함수
def add_angle_text(p1, p2, position, label):
    angle = calculate_angle(p1, p2)
    if angle < -90:
        angle += 180
    plt.text(position[0], position[1], label, fontsize=9, color='red', ha='center', rotation=angle)
    
def determate_e_type(fl, gl):
    slope_type = 'fil' if fl > gl else 'cut'
    return slope_type


# 전역 변수 설정
slope_cut = 1.5  # 절토사면경사
slope_fill = 1.5  # 성토사면경사
road_width = 8  # 노반폭
road_slope = 2  # 노반경사 2%
plot_limit = 50  # 횡단면도 좌우 범위

# Tkinter를 사용한 GUI 생성
def update_plot():
    ax.clear()
    ax.set_aspect('equal', adjustable='box')
    ax.grid(True)

    if input_station:
        selected_station = int(input_station)
    else:
        selected_station = station_var.get()
        
    if selected_station in station_dict:
        idx = station_dict[selected_station]
        fl_value = FL_list[idx]
        gl_value = GL_list[idx]


        #절성토 판단
        slope_type = determate_e_type(fl_value, gl_value)
        
        #지반고 라인 셋팅
        ground_line_points = [(-plot_limit, gl_value), (plot_limit, gl_value)]
        ground_line = LineString(ground_line_points)

        # 각 fl 값에 대해 Point 객체 생성
        fl_point = Point(0, fl_value)
        gl_point = Point(0, gl_value)

        # 노반 좌, 우측 좌표계산
        left_point, right_point = calculate_slope_points(fl_point, road_width, road_slope)
        
        # 지반고와 섹션 플로팅
        plot_section(fl_point, left_point, right_point)
        plot_ground_level(ground_line_points)

        # 사면 경사 계산 및 플로팅
        
        left_nori, right_nori = calculate_slope_intersections(left_point, right_point, ground_line, slope_cut, slope_type)

        ax.plot([left_point.x, left_nori.x], [left_point.y, left_nori.y], color='skyblue', label='Slope')
        ax.plot([right_point.x, right_nori.x], [right_point.y, right_nori.y], color='skyblue', label='Slope')

        # 각도 텍스트 추가
        add_angle_text(left_point, left_nori, ((left_point.x + left_nori.x) / 2, (left_point.y + left_nori.y) / 2), '1:1.5')
        add_angle_text(right_point, right_nori, ((right_point.x + right_nori.x) / 2, (right_point.y + right_nori.y) / 2), '1:1.5')

        # FL 및 GL 텍스트 추가
        ax.text(fl_point.x, fl_point.y, f'FL = {fl_value:.2f}', fontsize=9, color='red', ha='center')
        ax.text(gl_point.x, gl_point.y, f'GL = {gl_value:.2f}', fontsize=9, color='black', ha='center')

        # 측점 표시
        # 텍스트 그리기
        # 폰트 설정
        custom_font = ("굴림체", 12)  # 폰트 및 크기 지정
        
        # 텍스트 레이블 생성 윈도우창
        text = f'{format_distance(selected_station)}' # Change "Other Text" to whatever you want for direction not equal to 1
        text_label = tk.Label(root, text=text, bg=root.cget('bg'), fg="black", font=custom_font)
        text_label.place(x=400, y=40)

        # 플롯 설정
        ax.axhline(0, color='black', linewidth=0.5)
        ax.axvline(0, color='black', linewidth=0.5)
        ax.set_ylim(fl_value - 50, fl_value + 50)
        
        canvas.draw()
    else:
        print(f"측점 {selected_station}이(가) 목록에 없습니다.")

def load_and_setup_gui():
    global station_dict, station_list, FL_list, GL_list, slope_type_list , station_var
    global input_station
    
    # GL 및 FL 데이터 로드
    gl = load_ground_levels()
    fl = load_fl()

    # 리스트 초기화
    if not gl or not fl:
        print("GL 또는 FL 데이터가 없습니다.")
        return

    station_list = [item[0] for item in gl]
    FL_list = [item[1] for item in fl]
    GL_list = [item[1] for item in gl]
    
    # station_dict: station 이름과 인덱스의 매핑
    station_dict = {station: idx for idx, (station, _) in enumerate(gl)}

    

    # 측점 선택 콤보박스
    station_var = StringVar(root)
    station_menu = OptionMenu(root, station_var, *station_list)
    station_menu.pack()

    # 측점 직접 입력 필드
    entry_label = tk.Label(root, text="직접 측점 입력:")
    entry_label.pack()

    station_entry = Entry(root)
    station_entry.pack()
    
    # 측점 플롯 업데이트 버튼
    def on_update_button_click():
        global input_station
        input_value = station_entry.get().strip()
        print(f"입력된 값: {input_value}")  # Print input value for debugging
        # 입력된 측점이 station_dict에 있는지 확인
        try:
            input_station = int(input_value)
        except ValueError:
            print(f"입력된 측점 {input_value}이(가) 유효한 숫자가 아닙니다.")
            return

        input_station = int(input_station)
        print(type(input_station))
        if input_station in station_dict:
            update_plot()
        else:
            print(f"입력된 측점 {input_station}이(가) 목록에 없습니다.")

    update_button = Button(root, text="플롯 업데이트", command=on_update_button_click)
    update_button.pack()
    
    root.mainloop()
def exit_program():
    print("프로그램을 종료합니다.")
    
    # plot_root가 존재하는지 확인한 후 destroy() 호출
    if root.winfo_exists():
        root.destroy()
        
def save_dxf():
    pass

elevation = 345  # 시공기면고

# Tkinter GUI 구성
root = Tk()
root.title('횡단면도')
root.geometry("800x600")  # 가로 800, 세로 400

# Matplotlib 플롯을 위한 설정
fig, ax = plt.subplots()
ax.set_aspect('equal', adjustable='box')
ax.grid(True)

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Create a frame for the toolbar
toolbar_frame = tk.Frame(root)
toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)

# Add the navigation toolbar
toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
toolbar.update()

# 플롯 업데이트 버튼
plot_button = Button(root, text="측점 플롯", command=update_plot)
plot_button.pack(side=tk.LEFT, pady=5, padx=10)

#도면저장 버튼 생성
btn_save_dxf = tk.Button(root, text="도면으로 저장하기", command=save_dxf)
btn_save_dxf.pack(side=tk.LEFT, pady=5, padx=10)

# 종료 버튼 생성
exit_button = tk.Button(root, text="종료", command=exit_program)
exit_button.pack(side=tk.LEFT, pady=5, padx=10)

# GUI와 데이터 로드 및 설정 시작
load_and_setup_gui()
