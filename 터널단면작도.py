import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import matplotlib.patches as patches
from matplotlib.patches import Circle, Arc
import numpy as np
import math
import ezdxf
from scipy.optimize import minimize

import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False

def tunnel_section_area(params):
    R1, R1_ANGLE, R2, R2_ANGLE = params

    # 상부 원호의 면적 (반원호의 면적 계산)
    top_area = 0.5 * np.pi * R1**2 * (R1_ANGLE / 360)

    # 측벽 원호의 면적 (각도에 따른 면적 계산)
    side_area = R2**2 * np.radians(R2_ANGLE) / 2

    # 총 면적 계산
    total_area = top_area + 2 * side_area  # 양쪽 측벽의 면적을 더함

    return total_area

def drawcad(ax, translate_x=0, translate_y=0):
    # DWG 파일 열기
    dxf_file = "c:/temp/건축한계.dxf"
    doc = ezdxf.readfile(dxf_file)

    # 레이아웃 선택 (예: ModelSpace)
    msp = doc.modelspace()

    # 도형을 Matplotlib에 플롯
    for entity in msp:
        if entity.dxftype() == 'LINE':
            start_point = entity.dxf.start
            end_point = entity.dxf.end
            ax.plot([start_point.x + translate_x, end_point.x + translate_x],
                    [start_point.y + translate_y, end_point.y + translate_y], 'k-')

        elif entity.dxftype() == 'CIRCLE':
            center = entity.dxf.center
            radius = entity.dxf.radius
            circle = plt.Circle((center.x + translate_x, center.y + translate_y), radius, color='r', fill=False)
            ax.add_patch(circle)

        elif entity.dxftype() == 'ARC':
            center = entity.dxf.center
            radius = entity.dxf.radius
            start_angle = entity.dxf.start_angle
            end_angle = entity.dxf.end_angle
            arc = patches.Arc((center.x + translate_x, center.y + translate_y), 2*radius, 2*radius, angle=0,
                              theta1=start_angle, theta2=end_angle, color='g')
            ax.add_patch(arc)


def draw_arc(ax, center_point, radius, start_angle, end_angle, color='b', direction=1):
    x_center, y_center = center_point

    # Ensure angles are positive
    if start_angle > end_angle:
        start_angle, end_angle = end_angle, start_angle
        end_angle += 360
    else:
        end_angle += 360 if end_angle < start_angle else 0

    # Adjust for direction
    if direction == -1:
        start_angle, end_angle = end_angle, start_angle

    # Create Arc patch
    arc = patches.Arc(
        (x_center, y_center),
        2 * radius,  # width
        2 * radius,  # height
        angle=0,
        theta1=start_angle,
        theta2=end_angle,
        color=color
    )

    # Add Arc to the plot
    ax.add_patch(arc)

    return arc  # Return the Arc object for further processing


def find_side_center(top_center, top_radius, top_start_angle, top_end_angle, side_radius):
    top_start_x = top_center[0] + top_radius * np.cos(np.radians(top_start_angle))
    top_start_y = top_center[1] + top_radius * np.sin(np.radians(top_start_angle))

    top_end_x = top_center[0] + top_radius * np.cos(np.radians(top_end_angle))
    top_end_y = top_center[1] + top_radius * np.sin(np.radians(top_end_angle))

    direction_x = top_start_x - top_center[0]
    direction_y = top_start_y - top_center[1]

    end_direction_x = top_end_x - top_center[0]
    end_direction_y = top_end_y - top_center[1]
    
    norm = np.sqrt(direction_x**2 + direction_y**2)
    direction_x /= norm
    direction_y /= norm

    end_norm = np.sqrt(end_direction_x**2 + end_direction_y**2)
    end_direction_x /= end_norm
    end_direction_y /= end_norm
    
    left_center = (top_start_x - direction_x * side_radius, top_start_y - direction_y * side_radius)
    right_center = (top_end_x - end_direction_x * side_radius, top_end_y - end_direction_y * side_radius)
    
    return left_center, right_center

def find_end_point(center, radius, start_point, angle):
    start_angle = np.degrees(np.arctan2(start_point[1] - center[1], start_point[0] - center[0]))
    end_angle = start_angle + angle
    
    end_x = center[0] + radius * np.cos(np.radians(end_angle))
    end_y = center[1] + radius * np.sin(np.radians(end_angle))
    
    return (end_x, end_y)

def draw_tunnel_section(ax, R1, R1_ANGLE, R2, R2_ANGLE, center_top):
    left_center, right_center = find_side_center(center_top, R1, R1_ANGLE[0], R1_ANGLE[1], R2)
    
    start_point = (center_top[0] + R1 * np.cos(np.radians(R1_ANGLE[0])),
                   center_top[1] + R1 * np.sin(np.radians(R1_ANGLE[0])))

    end_point = (center_top[0] + R1 * np.cos(np.radians(R1_ANGLE[1])),
                 center_top[1] + R1 * np.sin(np.radians(R1_ANGLE[1])))
    
    left_end_point = find_end_point(left_center, R2, start_point, R2_ANGLE)
    right_end_point = find_end_point(right_center, R2, end_point, -R2_ANGLE)
    
    draw_arc(ax, center_top, R1, R1_ANGLE[0], R1_ANGLE[1], color='r', direction=1)
    
    left_start_angle = np.degrees(np.arctan2(start_point[1] - left_center[1], start_point[0] - left_center[0]))
    left_end_angle = np.degrees(np.arctan2(left_end_point[1] - left_center[1], left_end_point[0] - left_center[0]))

    draw_arc(ax, left_center, R2, left_start_angle, left_end_angle, color='b', direction=-1)
    
    right_start_angle = np.degrees(np.arctan2(end_point[1] - right_center[1], end_point[0] - right_center[0]))
    right_end_angle = np.degrees(np.arctan2(right_end_point[1] - right_center[1], right_end_point[0] - right_center[0]))

    draw_arc(ax, right_center, R2, right_start_angle, right_end_angle, color='g', direction=1)

    return left_end_point, right_end_point

def update_plot():
    ax.clear()
    ax.set_aspect('equal', adjustable='box')
    ax.grid(True)

    R1 = s_R1.get()
    TOP_ANGLE = s_TOP_ANGLE.get()
    R2 = s_R2.get()
    R2_ANGLE = s_R2_ANGLE.get()
    D = s_D.get()
    R1_XY = (0, s_R1_Y.get())

    R1_ANGLE = [90 + (TOP_ANGLE / 2), 90 - (TOP_ANGLE / 2)]

    drawcad(ax, translate_x=-D/2, translate_y=+RL)
    drawcad(ax, translate_x=D/2, translate_y=+RL)
    left_end_point, right_end_point = draw_tunnel_section(ax, R1, [90 + (TOP_ANGLE / 2), 90 - (TOP_ANGLE / 2)], R2, R2_ANGLE, R1_XY)

    x_values = [left_end_point[0], left_end_point[0] + side, left_end_point[0] + side , origin[0]]
    y_values = [left_end_point[1], left_end_point[1], left_end_point[1] - FL_TO_CULVUT, left_end_point[1] - FL_TO_CULVUT]
    ax.plot(x_values,y_values)

    x_values = [right_end_point[0], right_end_point[0] - side, right_end_point[0] - side , origin[0]]
    y_values = [right_end_point[1], right_end_point[1], right_end_point[1] - FL_TO_CULVUT, right_end_point[1] - FL_TO_CULVUT]
    ax.plot(x_values,y_values)

    params = [R1, TOP_ANGLE, R2, R2_ANGLE]
    params2 = [left_end_point, right_end_point]
    console_print_tunnel_spec(params, params2)
    check_tunnel_spec(params2)

    initial_guess = [R1_XY[0], R1_XY[1]]
    result = minimize(objective_function, initial_guess, args=(R1, R1_ANGLE, R2, R2_ANGLE, D), method='L-BFGS-B')

    optimized_R1_XY = result.x
    print(f"찾은 R1_XY: {optimized_R1_XY[1]}")

    canvas.draw()

def console_print_tunnel_spec(params, params2):
    
    total_area = tunnel_section_area(params)
    
    print(f'내공단면적 {total_area:.2f}m^2')
    print(f'R1 : {params[0]:.2f}')
    print(f'Top Angle {params[1]}')
    print(f'R2 : {params[2]}')
    print(f'R2 Angle: {params[3]}')
    print(f'A: {abs(params2[0][0] - origin[0]):.2f}')
    
def check_tunnel_spec(params):
    tolerance = 0.02
    new_FL = params[0][1] - FL_TO_CULVUT #FL Y좌표

    print(f"현재 FL 값: {new_FL:.2f}")
    
    if abs(new_FL - FL) <= tolerance:
        print('검토결과 : OK')
    elif new_FL > FL:
        print('검토결과 : 미달 FL을 내려야 함.')
    else:
        print('검토결과 : 미달 FL을 올려야 함.')

def objective_function(params, *args):
    R1, R1_ANGLE, R2, R2_ANGLE, D = args
    R1_XY = params
    center_top = (0, R1_XY[1])
    
    # 최적화 문제에서 사용할 계산 로직
    left_center, right_center = find_side_center(center_top, R1, R1_ANGLE[0], R1_ANGLE[1], R2)
    
    # 측벽의 시작점과 끝점 계산
    start_point = (center_top[0] + R1 * np.cos(np.radians(R1_ANGLE[0])),
                   center_top[1] + R1 * np.sin(np.radians(R1_ANGLE[0])))
    end_point = (center_top[0] + R1 * np.cos(np.radians(R1_ANGLE[1])),
                 center_top[1] + R1 * np.sin(np.radians(R1_ANGLE[1])))

    # 좌측 및 우측 원호의 끝점 계산
    left_end_point = find_end_point(left_center, R2, start_point, R2_ANGLE)
    right_end_point = find_end_point(right_center, R2, end_point, -R2_ANGLE)

    # FL 값 계산
    new_FL = left_end_point[1] - FL_TO_CULVUT

    return abs(new_FL)

# 버튼 클릭 이벤트 핸들러
def save_dxf(event=None):
    filename = "C:/TEMP/TUNEEL_output.dxf"  # 저장할 DXF 파일 이름
    save_plot_to_dxf(filename, ax)
    print(f"플롯 상태가 {filename} 파일로 저장되었습니다.")

def save_plot_to_dxf(filename, ax):
    doc = ezdxf.new()
    msp = doc.modelspace()

    # 선 추가
    for line in ax.lines:
        x_data, y_data = line.get_data()
        for i in range(len(x_data) - 1):
            start_point = (x_data[i], y_data[i])
            end_point = (x_data[i + 1], y_data[i + 1])
            msp.add_line(start=start_point, end=end_point)

    # 원과 원호 추가
    for patch in ax.patches:
        if isinstance(patch, Circle):
            center = patch.center
            radius = patch.radius
            msp.add_circle(center=center, radius=radius)

        elif isinstance(patch, Arc):
            center = patch.center
            width = patch.width
            height = patch.height
            radius = width / 2
            
            # Matplotlib의 Arc는 시작 각도와 끝 각도를 0도에서 360도 사이로 사용
            start_angle = patch.theta1
            end_angle = patch.theta2

            # DXF의 경우, 시계방향으로 각도를 계산
            if end_angle < start_angle:
                end_angle += 360
            
            # Arc의 끝 각도가 360도를 넘어가는 경우, 시작 각도와 끝 각도를 조정
            if end_angle > 360:
                end_angle -= 360

            # DXF 아크의 각도는 0도에서 360도 사이로 정의
            start_angle = (start_angle % 360)
            end_angle = (end_angle % 360)

            msp.add_arc(center=center, radius=radius, start_angle=start_angle, end_angle=end_angle)

    doc.saveas(filename)

    
#초기값          
origin = (0,0) #원점
FL = 0 #시공기면
RL = FL + 0.472 #레일면고
side = 0.8 #공동구 점검원 통로폭
FL_TO_CULVUT = 0.472 #공동구 상단에서 FL까지의 높이
D = 4.4 #선로중심간격
T = 0.4 #라이닝 두께

R1_XY = (0, 1.572) #R1원점 FL에서 R1까지 높이
R1 = 7.166# R1반경
TOP_ANGLE = 90 #R1각도
R2 = 5.54 #R2반경
R2_ANGLE = 69 #R2각도

# 슬라이더가 위치할 창을 위한 tkinter 설정
slider_root = tk.Tk()
slider_root.title("Slider Control")

# 플롯 창 생성
plot_root = tk.Toplevel(slider_root)
plot_root.title("Plot Window")

# Matplotlib 플롯을 위한 설정
fig, ax = plt.subplots()
ax.set_aspect('equal', adjustable='box')
ax.grid(True)

canvas = FigureCanvasTkAgg(fig, master=plot_root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# 슬라이더를 위한 tkinter.Scale 위젯 생성
s_R1 = tk.Scale(slider_root, label='R1', from_=5.0, to=20.0, resolution=0.1, orient=tk.HORIZONTAL, command=lambda x: update_plot())
s_R1.set(7.166)
s_R1.pack(fill=tk.X, padx=5, pady=5)

s_TOP_ANGLE = tk.Scale(slider_root, label='TOP_ANGLE', from_=60.0, to=120.0, resolution=1.0, orient=tk.HORIZONTAL, command=lambda x: update_plot())
s_TOP_ANGLE.set(90)
s_TOP_ANGLE.pack(fill=tk.X, padx=5, pady=5)

s_R2 = tk.Scale(slider_root, label='R2', from_=4.0, to=20.0, resolution=0.1, orient=tk.HORIZONTAL, command=lambda x: update_plot())
s_R2.set(5.54)
s_R2.pack(fill=tk.X, padx=5, pady=5)

s_R2_ANGLE = tk.Scale(slider_root, label='R2_ANGLE', from_=30.0, to=90.0, resolution=1.0, orient=tk.HORIZONTAL, command=lambda x: update_plot())
s_R2_ANGLE.set(69)
s_R2_ANGLE.pack(fill=tk.X, padx=5, pady=5)

s_D = tk.Scale(slider_root, label='선로중심간격', from_=3.8, to=30.0, resolution=0.1, orient=tk.HORIZONTAL, command=lambda x: update_plot())
s_D.set(4.4)
s_D.pack(fill=tk.X, padx=5, pady=5)

s_R1_Y = tk.Scale(slider_root, label='R1_Y', from_=0.0, to=5.0, resolution=0.1, orient=tk.HORIZONTAL, command=lambda x: update_plot())
s_R1_Y.set(1.572)
s_R1_Y.pack(fill=tk.X, padx=5, pady=5)

# 다시그리기 버튼 생성
btn_save_dxf = tk.Button(slider_root, text="도면으로 저장하기", command=save_dxf)
btn_save_dxf.pack(side=tk.LEFT, pady=5, padx=10)
    
# 초기 플롯 그리기
update_plot()

# tkinter 메인 루프 시작
slider_root.mainloop()
