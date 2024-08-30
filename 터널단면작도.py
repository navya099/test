import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import matplotlib.patches as patches
from matplotlib.patches import Circle, Arc
import math
import ezdxf
from scipy.optimize import minimize
from shapely.geometry import LineString, Polygon, Point
from shapely.affinity import rotate

import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk  # 추가
import numpy as np
from tkinter import filedialog, Tk, StringVar, ttk , messagebox, simpledialog

plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False

def draw_angle_annotation(ax, p1, p2, p3, radius=1, angle_color='black'):
    """
    두 선 사이의 각도를 표시합니다.

    Parameters:
    - ax: Matplotlib Axes 객체
    - p1, p2, p3: 각도를 나타내는 세 점 (p2는 각도의 중심점)
    - radius: 각도 호의 반지름
    - angle_color: 각도 기호의 색상
    """
    # 벡터 계산
    v1 = np.array(p1) - np.array(p2)
    v2 = np.array(p3) - np.array(p2)
    
    # 벡터의 각도 계산 (0도에서 시작)
    angle = np.arccos(np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1.0, 1.0))
    angle_deg = np.degrees(angle)
    
    # 벡터의 방향과 각도를 기반으로 호의 시작각과 끝각 계산
    angle_start = np.arctan2(v1[1], v1[0])
    angle_end = np.arctan2(v2[1], v2[0])

    # 호 그리기
    arc = patches.Arc(p2, 2 * radius, 2 * radius, angle=0, 
                      theta1=np.degrees(angle_end), theta2=np.degrees(angle_start), 
                      color=angle_color)
    ax.add_patch(arc)

    
    
    # 각도 기호 표시
    mid_angle = (angle_start + angle_end) / 2
    ax.text(p2[0] + radius * 0.7 * np.cos(mid_angle), 
            p2[1] + radius * 0.7 * np.sin(mid_angle),
            f'{angle_deg:.1f}°', color=angle_color, fontsize=12, ha='center')


def find_extreme_x_on_arc(center, radius, start_angle, end_angle):
    """
    호의 중심(center), 반지름(radius), 시작 각도(start_angle), 끝 각도(end_angle)를 기반으로
    호 위의 가장 큰 x값과 가장 작은 x값을 찾습니다.
    """
    # 각도를 라디안으로 변환
    start_angle_rad = np.radians(start_angle)
    end_angle_rad = np.radians(end_angle)
    
    # 시작 각도와 끝 각도 사이의 각도를 샘플링 (더 정밀한 값을 원할 경우 증가)
    angles = np.linspace(start_angle_rad, end_angle_rad, 1000)
    
    # x 좌표 계산
    x_values = center[0] + radius * np.cos(angles)
    
    # Y 좌표 계산
    y_values = center[1] + radius * np.sin(angles)
    
    # x 좌표의 최대값과 최소값 찾기
    max_x_index = np.argmax(x_values)
    min_x_index = np.argmin(x_values)
    
    # 최대값과 최소값에 해당하는 좌표 (x, y)
    max_x_point = (x_values[max_x_index], y_values[max_x_index])
    min_x_point = (x_values[min_x_index], y_values[min_x_index])
    
    # 좌표 반환
    return max_x_point, min_x_point

def check_polygon_closure(polygon):
    # 첫 좌표와 마지막 좌표 비교
    is_closed = polygon.exterior.is_ring
    is_valid = polygon.is_valid

    return is_closed, is_valid

def plot_polygon_with_area(polygon):
    # 폴리곤 좌표 추출
    x, y = polygon.exterior.xy
    
    # 플롯 생성
    fig, ax = plt.subplots()
    ax.plot(x, y, color='blue', linewidth=2, solid_capstyle='round', zorder=1)
    
    # 폴리곤 면적 계산
    area = polygon.area
    
    # 폴리곤 중심 좌표 계산
    centroid = polygon.centroid
    
    # 면적을 폴리곤 내부에 표시
    ax.text(centroid.x, centroid.y, f'Area: {area:.2f}', fontsize=12, ha='center')
    
    # 폴리곤을 그래프의 중앙에 배치하고 보기 좋게 스케일 조정
    minx, miny, maxx, maxy = polygon.bounds
    ax.set_xlim([minx - 0.1, maxx + 0.1])
    ax.set_ylim([miny - 0.1, maxy + 0.1])
    ax.set_aspect('equal', 'box')
    
    # 그래프 제목과 축 제거
    ax.set_title("Polygon with Area")
    ax.axis('off')
    
    plt.show()
    
def arc_to_linestring(center, radius, start_angle, end_angle, num_points=100):
    """Arc 객체를 다각형으로 변환하기 위해 작은 선분(LineString)으로 분리합니다."""
    angles = np.linspace(np.radians(start_angle), np.radians(end_angle), num_points)
    points = [(center[0] + radius * np.cos(angle), center[1] + radius * np.sin(angle)) for angle in angles]
    return LineString(points)

def tunnel_section_area(params):
    R1, TOP_ANGLE, R2, R2_ANGLE = params
    center_top = (0, s_R1_Y.get())
    
    # 좌우 측면의 중심 계산
    left_center, right_center = find_side_center(center_top, R1, 90 + (TOP_ANGLE / 2), 90 - (TOP_ANGLE / 2), R2)
    
    # 상단 아크
    top_arc = arc_to_linestring(center_top, R1, 90 + (TOP_ANGLE / 2), 90 - (TOP_ANGLE / 2))
    
    # 좌우 측면 아크
    left_arc = arc_to_linestring(left_center, R2, 90 + (TOP_ANGLE / 2),90 + (TOP_ANGLE / 2) + R2_ANGLE)
    right_arc = arc_to_linestring(right_center, R2, 90 - (TOP_ANGLE / 2),90 - (TOP_ANGLE / 2) - R2_ANGLE)
    
    # 아래 라인 (좌우 아크의 끝점을 연결)
    bottom_line = LineString([left_arc.coords[-1], right_arc.coords[-1]])

    
     # 모든 부분을 연결하여 폐합된 다각형 생성
    # 좌표를 올바른 순서로 나열하여 폐합된 폴리곤 생성
    polygon_coords = (
        list(left_arc.coords[::-1]) + #좌측 아크는 역순
        list(top_arc.coords) + 
        list(right_arc.coords) +
        list(bottom_line.coords[::-1]) # 아래 라인은 역순으로
        
    )
    
    # 폴리곤 생성
    polygon = Polygon(polygon_coords)
    
    return polygon

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

def find_start_point(center, radius, end_point, angle):
    end_angle = np.degrees(np.arctan2(end_point[1] - center[1], end_point[0] - center[0]))
    start_angle = end_angle - angle
    
    start_x = center[0] + radius * np.cos(np.radians(start_angle))
    start_y = center[1] + radius * np.sin(np.radians(start_angle))
    
    return (start_x, start_y)

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

# Example function to draw a vertical line at D/2
def draw_axline(ax, D):
    ax.axvline(x=-D/2, color='gray', linestyle='--', linewidth=1)  # Draw vertical line at D/2
    ax.axvline(x= origin[0], color='gray', linestyle='--', linewidth=1)  # Draw vertical line at D/2
    ax.axvline(x= D/2, color='gray', linestyle='--', linewidth=1)  # Draw vertical line at D/2
    ax.text(-D/2,7.40,'CL of 하선')
    ax.text( D/2,7.40,'CL of 상선')
    ax.text(0,7.40,'CL of 터널')
    
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

    start_point = (R1_XY[0] + R1 * np.cos(np.radians(R1_ANGLE[0])),
                   R1_XY[1] + R1 * np.sin(np.radians(R1_ANGLE[0])))

    end_point = (R1_XY[0] + R1 * np.cos(np.radians(R1_ANGLE[1])),
                 R1_XY[1] + R1 * np.sin(np.radians(R1_ANGLE[1])))
    
    left_end_point, right_end_point = draw_tunnel_section(ax, R1, [90 + (TOP_ANGLE / 2), 90 - (TOP_ANGLE / 2)], R2, R2_ANGLE, R1_XY)

    # R2 라인 그리기
    L_C, R_C = find_side_center(R1_XY, R1, R1_ANGLE[0], R1_ANGLE[1], R2)


    x_values = [left_end_point[0], left_end_point[0] + sideL, left_end_point[0] + sideL , origin[0]]
    y_values = [left_end_point[1], left_end_point[1], left_end_point[1] - FL_TO_CULVUT, left_end_point[1] - FL_TO_CULVUT]
    ax.plot(x_values,y_values)

    x_values = [right_end_point[0], right_end_point[0] - sideR, right_end_point[0] - sideR , origin[0]]
    y_values = [right_end_point[1], right_end_point[1], right_end_point[1] - FL_TO_CULVUT, right_end_point[1] - FL_TO_CULVUT]
    ax.plot(x_values,y_values)

    draw_axline(ax, D)
    
    params = [R1, TOP_ANGLE, R2, R2_ANGLE]
    params2 = [left_end_point, right_end_point]
    console_print_tunnel_spec(params, params2)
    check_tunnel_spec(params2)

    draw_R1R2_LINE(ax, params, params2)

    #R1, R2각도표시
    draw_angle_annotation(ax, start_point, R1_XY, end_point)#R1
    draw_angle_annotation(ax, left_end_point, L_C, start_point)#R2_L
    draw_angle_annotation(ax, end_point, R_C, right_end_point)#R2_R

    #공동구통로표시
    plot_safeline(left_end_point, right_end_point)
    
    initial_guess = [R1_XY[0], R1_XY[1]]
    result = minimize(objective_function, initial_guess, args=(R1, R1_ANGLE, R2, R2_ANGLE, D), method='L-BFGS-B')

    optimized_R1_XY = result.x
    print(f"찾은 R1_XY: {optimized_R1_XY[1]}")

    canvas.draw()

def draw_line(ax, start, end, linestyle='--', color='gray'):
    """
    두 점 사이에 선을 그리고 주어진 스타일로 설정합니다.
    """
    x_values = [start[0], end[0]]
    y_values = [start[1], end[1]]
    ax.plot(x_values, y_values, linestyle=linestyle, color=color)

def add_text(ax, position, text, rotation=0, offset=(0, 0)):
    """
    텍스트를 주어진 위치에 추가하고, 회전 및 오프셋을 적용합니다.
    """
    ax.text(position[0] + offset[0], position[1] + offset[1], text, rotation=rotation)

def calculate_midpoint(p1, p2):
    """
    두 점 사이의 중점을 계산합니다.
    """
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

def draw_R1R2_LINE(ax, params, params2):
    # R1 라인 그리기
    center_top = (0, s_R1_Y.get())
    R1_ANGLE = [90 + (params[1] / 2), 90 - (params[1] / 2)]
    
    start_point = (center_top[0] + params[0] * np.cos(np.radians(R1_ANGLE[0])),
                   center_top[1] + params[0] * np.sin(np.radians(R1_ANGLE[0])))
    
    end_point = (center_top[0] + params[0] * np.cos(np.radians(R1_ANGLE[1])),
                 center_top[1] + params[0] * np.sin(np.radians(R1_ANGLE[1])))

    # 시작선과 끝선 그리기
    draw_line(ax, center_top, end_point)
    draw_line(ax, center_top, start_point)
    
    # 중점 계산 및 텍스트 추가
    mid_end = calculate_midpoint(center_top, end_point)
    add_text(ax, mid_end, f'R1 = {params[0]*1000:.0f}', rotation=R1_ANGLE[1], offset=(-0.25, 0.25))

    mid_start = calculate_midpoint(center_top, start_point)
    add_text(ax, mid_start, f'R1 = {params[0]*1000:.0f}', rotation=R1_ANGLE[0] + 180, offset=(-0.5, -0.5))
    
    # R2 라인 그리기
    L_C, R_C = find_side_center(center_top, params[0], R1_ANGLE[0], R1_ANGLE[1], params[2])

    # 시작선과 끝선 그리기
    draw_line(ax, L_C, params2[0])
    draw_line(ax, R_C, params2[1])
    
    # 중점 계산 및 텍스트 추가
    mid_start_R2 = calculate_midpoint(L_C, params2[0])
    r2_bearing_start = calculate_bearing(params2[0][0], params2[0][1], L_C[0], L_C[1])
    add_text(ax, mid_start_R2, f'R2 = {params[2]*1000:.0f}', rotation=r2_bearing_start)

    mid_end_R2 = calculate_midpoint(R_C, params2[1])
    r2_bearing_end = calculate_bearing(R_C[0], R_C[1], params2[1][0], params2[1][1])
    add_text(ax, mid_end_R2, f'R2 = {params[2]*1000:.0f}', rotation=r2_bearing_end)


    
def calculate_bearing(x1, y1, x2, y2):
    # Calculate the bearing (direction) between two points in Cartesian coordinates
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.degrees(math.atan2(dy, dx))
    return bearing

def console_print_tunnel_spec(params, params2):
    
    polygon = tunnel_section_area(params)

    #plot_polygon_with_area(polygon)
    center_top = (0, s_R1_Y.get())
    TOP_of_Tunnel = center_top[1] + R1 - origin[1]
    
    # 폐합 여부 확인
    is_closed, is_valid = check_polygon_closure(polygon)

    '''
    if is_closed:
        print("Polygon is closed.")
    else:
        print("Polygon is NOT closed.")

    if is_valid:
        print("Polygon is valid.")
    else:
        print("Polygon is NOT valid.")
    '''
    
    A = abs(params2[0][0] - origin[0])
    
    R1_ANGLE = [90 + (params[1] / 2), 90 - (params[1] / 2)]
    
    L_C ,R_C = find_side_center(center_top, params[0], R1_ANGLE[0], R1_ANGLE[1], params[2])
    left_SA = find_start_point(L_C, params[2], params2[0], params[3])
    
    p1,p2 = find_extreme_x_on_arc(L_C, params[2], R1_ANGLE[0], R1_ANGLE[0] + params[3])

    ax.axhline(y=p2[1], color='gray', linestyle='--', linewidth=1)  # SL라인 그리기
    ax.text(p2[0],p2[1],'SL')

    print(f'------------------터널제원출력----------------\n')
    print(f'내공단면적 {polygon.area:.2f}m^2')
    print(f'R1 : {params[0]:.2f}')
    print(f'Top Angle {params[1]}')
    print(f'R2 : {params[2]}')
    print(f'R2 Angle: {params[3]}')
    print(f'A: {A:.2f}')
    print(f'SL: {p2[1]:.2f}')
    print(f'R2/R1비 : {R2/R1:.2f}')
    print(f'편평률: {TOP_of_Tunnel / (A*2):.2f}')
    
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
    print('------------------출력종료--------------------------')
    
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

def set_slider_value(slider, label):
    # 사용자에게 값을 입력받아 슬라이더 값 설정
    value = simpledialog.askfloat("입력", f"{label} 값을 입력하세요:", initialvalue=slider.get())
    if value is not None:
        slider.set(value)
        update_plot()

def exit_program():
    print("프로그램을 종료합니다.")
    
    # plot_root가 존재하는지 확인한 후 destroy() 호출
    if plot_root.winfo_exists():
        plot_root.destroy()
    
    # slider_root가 존재하는지 확인한 후 destroy() 호출
    if slider_root.winfo_exists():
        slider_root.destroy()
    
def plot_safeline(left_end_point, right_end_point):#안전라인 그리기
    #좌측
    x = [left_end_point[0], left_end_point[0] ,left_end_point[0] + sideL, left_end_point[0] +sideL]
    y = [left_end_point[1], left_end_point[1] + safeheight, left_end_point[1] + safeheight, left_end_point[1]]
    ax.plot(x,y, color='gray', linestyle='--')

    #X표시
    x2 = [left_end_point[0], left_end_point[0] + sideL]
    y2 = [left_end_point[1] + safeheight,left_end_point[1]]
    ax.plot(x2,y2, color='gray', linestyle='--')
    #X표시
    x2 = [left_end_point[0] + sideL,  left_end_point[0]]
    y2 = [left_end_point[1] + safeheight,left_end_point[1]]
    ax.plot(x2,y2, color='gray', linestyle='--')
    
    #우측
    x = [right_end_point[0], right_end_point[0] ,right_end_point[0] - sideL, right_end_point[0] - sideL]
    y = [right_end_point[1], right_end_point[1] + safeheight, right_end_point[1] + safeheight, left_end_point[1]]
    ax.plot(x,y, color='gray', linestyle='--')

    #X표시
    x2 = [right_end_point[0], right_end_point[0] - sideL]
    y2 = [right_end_point[1] + safeheight,right_end_point[1]]
    ax.plot(x2,y2, color='gray', linestyle='--')
    #X표시
    x2 = [right_end_point[0] - sideL,  right_end_point[0]]
    y2 = [right_end_point[1] + safeheight,right_end_point[1]]
    ax.plot(x2,y2, color='gray', linestyle='--')
#초기값          
origin = (0,0) #원점
FL = 0 #시공기면
RL = FL + 0.472 #레일면고
sideL = 0.8 #좌측 공동구 점검원 통로폭
sideR = 0.8 #우측 공동구 점검원 통로폭
safeheight = 2.1#안전반경높이
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
# 윈도우 크기 설정 (가로 x 세로)
slider_root.geometry("200x700")  # 가로 800, 세로 400

# 플롯 창 생성
plot_root = tk.Toplevel(slider_root)
plot_root.title("Plot Window")
# 윈도우 크기 설정 (가로 x 세로)
plot_root.geometry("600x700")  # 가로 800, 세로 400

# Matplotlib 플롯을 위한 설정
fig, ax = plt.subplots()
ax.set_aspect('equal', adjustable='box')
ax.grid(True)

canvas = FigureCanvasTkAgg(fig, master=plot_root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Create a frame for the toolbar
toolbar_frame = tk.Frame(plot_root)
toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)

# Add the navigation toolbar
toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
toolbar.update()


# 슬라이더 생성 (초기에는 command가 없음)
s_R1 = tk.Scale(slider_root, label='R1', from_=1.0, to=20.0, resolution=0.1, orient=tk.HORIZONTAL)
s_R1.set(7.166)
s_R1.pack(fill=tk.X, padx=5, pady=5)

s_TOP_ANGLE = tk.Scale(slider_root, label='TOP_ANGLE', from_=0.0, to=180.0, resolution=1.0, orient=tk.HORIZONTAL)
s_TOP_ANGLE.set(90)
s_TOP_ANGLE.pack(fill=tk.X, padx=5, pady=5)

s_R2 = tk.Scale(slider_root, label='R2', from_=1.0, to=20.0, resolution=0.1, orient=tk.HORIZONTAL)
s_R2.set(5.54)
s_R2.pack(fill=tk.X, padx=5, pady=5)

s_R2_ANGLE = tk.Scale(slider_root, label='R2_ANGLE', from_=0.0, to=180.0, resolution=1.0, orient=tk.HORIZONTAL)
s_R2_ANGLE.set(69)
s_R2_ANGLE.pack(fill=tk.X, padx=5, pady=5)

s_D = tk.Scale(slider_root, label='선로중심간격', from_=0.0, to=30.0, resolution=0.1, orient=tk.HORIZONTAL)
s_D.set(4.4)
s_D.pack(fill=tk.X, padx=5, pady=5)

s_R1_Y = tk.Scale(slider_root, label='R1_Y', from_=-10.0, to=10.0, resolution=0.01, orient=tk.HORIZONTAL)
s_R1_Y.set(1.572)
s_R1_Y.pack(fill=tk.X, padx=5, pady=5)

# 슬라이더에 command 설정
s_R1.config(command=lambda x: update_plot())
s_TOP_ANGLE.config(command=lambda x: update_plot())
s_R2.config(command=lambda x: update_plot())
s_R2_ANGLE.config(command=lambda x: update_plot())
s_D.config(command=lambda x: update_plot())
s_R1_Y.config(command=lambda x: update_plot())

# 버튼 생성 및 슬라이더와 연결
tk.Button(slider_root, text="R1 입력", command=lambda: set_slider_value(s_R1, 'R1')).pack(fill=tk.X, padx=5, pady=5)
tk.Button(slider_root, text="TOP_ANGLE 입력", command=lambda: set_slider_value(s_TOP_ANGLE, 'TOP_ANGLE')).pack(fill=tk.X, padx=5, pady=5)
tk.Button(slider_root, text="R2 입력", command=lambda: set_slider_value(s_R2, 'R2')).pack(fill=tk.X, padx=5, pady=5)
tk.Button(slider_root, text="R2_ANGLE 입력", command=lambda: set_slider_value(s_R2_ANGLE, 'R2_ANGLE')).pack(fill=tk.X, padx=5, pady=5)
tk.Button(slider_root, text="선로중심간격 입력", command=lambda: set_slider_value(s_D, '선로중심간격')).pack(fill=tk.X, padx=5, pady=5)
tk.Button(slider_root, text="R1_Y 입력", command=lambda: set_slider_value(s_R1_Y, 'R1_Y')).pack(fill=tk.X, padx=5, pady=5)


# 다시그리기 버튼 생성
btn_save_dxf = tk.Button(slider_root, text="도면으로 저장하기", command=save_dxf)
btn_save_dxf.pack(side=tk.LEFT, pady=5, padx=10)

# 종료 버튼 생성
exit_button = tk.Button(slider_root, text="종료", command=exit_program)
exit_button.pack(side=tk.LEFT, pady=5, padx=10)

# tkinter 메인 루프 시작
slider_root.mainloop()
