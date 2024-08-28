import math
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
from tkinter import filedialog
import csv
import numpy as np

# matplotlib 설정: 한글 폰트 및 마이너스 기호 지원
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 거리를 형식화하는 함수
def format_distance(number):
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
    file_path = filedialog.askopenfilename(title="파일 선택", filetypes=[("텍스트 파일", "*.txt")])

    if not file_path:
        print("파일 선택이 취소되었습니다.")
        return gl
    
    try:
        with open(file_path, 'r', encoding='UTF-8') as file:
            reader = csv.reader(file)
            for i, row in enumerate(reader):
                station = i * 25
                ground_elevation = float(row[2])
                gl.append([station, ground_elevation])
    except FileNotFoundError:
        print("파일을 찾을 수 없습니다.")
    except Exception as e:
        print("파일을 읽는 중 오류가 발생했습니다:", e)

    return gl

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
    plt.plot(x_values, y_values, color='skyblue', label='Section')

# 지반고(GL) 시각화 함수
def plot_ground_level(GL):
    x_values = [pt[0] for pt in GL]
    y_values = [pt[1] for pt in GL]
    plt.plot(x_values, y_values, 'g--', label='Ground Level (GL)')

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

# 전역 변수 설정
slope_cut = 1.5  # 절토사면경사
slope_fill = 1.5  # 성토사면경사
road_width = 8  # 노반폭
road_slope = 2  # 노반경사 2%
plot_limit = 50  # 횡단면도 좌우 범위

# 메인 코드
station = float(input('측점 입력: '))
fl = float(input('FL 입력: '))
gl = float(input('GL 입력: '))

slope_type = 'fil' if fl > gl else 'cut'

ground_line_points = [(-plot_limit, gl), (plot_limit, gl)]
ground_line = LineString(ground_line_points)

fl_point = Point(0, fl)
gl_point = Point(0, gl)

left_point, right_point = calculate_slope_points(fl_point, road_width, road_slope)

plot_section(fl_point, left_point, right_point)
plot_ground_level(ground_line_points)

# 사면 경사 계산 및 시각화
left_nori, right_nori = calculate_slope_intersections(left_point, right_point, ground_line, slope_cut, slope_type)

plt.plot([left_point.x, left_nori.x], [left_point.y, left_nori.y], color='skyblue', label='Slope')
plt.plot([right_point.x, right_nori.x], [right_point.y, right_nori.y], color='skyblue', label='Slope')

# 각도 텍스트 추가
add_angle_text(left_point, left_nori, ((left_point.x + left_nori.x) / 2, (left_point.y + left_nori.y) / 2), '1:1.5')
add_angle_text(right_point, right_nori, ((right_point.x + right_nori.x) / 2, (right_point.y + right_nori.y) / 2), '1:1.5')

# FL, GL 텍스트 추가
plt.text(fl_point.x, fl_point.y, f'FL = {fl}', fontsize=9, color='red', ha='center')
plt.text(gl_point.x, gl_point.y, f'GL = {gl}', fontsize=9, color='black', ha='center')

# 측점 표시
plt.text(fl_point.x, fl_point.y + 15, f'{format_distance(station)}', fontsize=9, color='red', ha='center')

# 플롯 설정
plt.axhline(0, color='black', linewidth=0.5)
plt.axvline(0, color='black', linewidth=0.5)
plt.ylim(fl - 50, fl + 50)
plt.grid(True)
plt.legend()
plt.gca().set_aspect('equal')
plt.title('횡단면도(1)')
plt.show()
