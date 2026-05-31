import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk  # 추가
import numpy as np

plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False

def degrees_to_radians(degrees):
    return degrees * (np.pi / 180)

def radians_to_degrees(radians):
    return radians * (180 / np.pi)

def calculate_destination_coordinates(x1, y1, bearing, distance):
    angle = np.radians(bearing)
    x2 = x1 + distance * np.cos(angle)
    y2 = y1 + distance * np.sin(angle)
    return x2, y2

def calculate_bearing(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    bearing = np.degrees(np.arctan2(dy, dx))
    return bearing

def draw_arc(start_point, end_point, center_point):
    x_start, y_start = start_point
    x_end, y_end = end_point
    x_center, y_center = center_point

    radius = np.sqrt((x_center - x_start)**2 + (y_center - y_start)**2)
    start_angle = np.degrees(np.arctan2(y_start - y_center, x_start - x_center))
    end_angle = np.degrees(np.arctan2(y_end - y_center, x_end - x_center))
    
    theta = np.linspace(start_angle, end_angle, 100)
    
    x_arc = x_center + radius * np.cos(np.radians(theta))
    y_arc = y_center + radius * np.sin(np.radians(theta))

    print('시작 각도',start_angle)
    print('끝 각도',end_angle)
    
    return x_arc, y_arc

def calculate_arc_points(h1, start_point, radius, arc_length):
    R = radius
    CL = arc_length
    IA = arc_length / radius
    IA_DEGREE = radians_to_degrees(IA)
    TL = R * np.tan(IA/2)

    if IA_DEGREE >= 360:
        print("원")
        return
    
    if R > 0:
        bc_o_bearing = h1 - 90
        o_bc_bearing = bc_o_bearing - 180
        O_EC_bearing = o_bc_bearing - IA_DEGREE
        center_xy = calculate_destination_coordinates(start_point[0], start_point[1], bc_o_bearing, R)
        end_xy = calculate_destination_coordinates(center_xy[0], center_xy[1], O_EC_bearing, R)
        mid_xy = calculate_destination_coordinates(center_xy[0], center_xy[1], o_bc_bearing -  IA_DEGREE/2, R)
    else:
        bc_o_bearing = h1 + 90
        o_bc_bearing = bc_o_bearing - 180
        O_EC_bearing = o_bc_bearing - IA_DEGREE
        center_xy = calculate_destination_coordinates(start_point[0], start_point[1], bc_o_bearing, -R)
        end_xy = calculate_destination_coordinates(center_xy[0], center_xy[1], O_EC_bearing, -R)
        mid_xy = calculate_destination_coordinates(center_xy[0], center_xy[1], o_bc_bearing -  IA_DEGREE/2, -R)
    
    return center_xy, end_xy ,mid_xy

def update_plot(event=None):
    ax.clear()  # Clear the current plot

    # Get values from widgets
    bc_sta = float(bc_sta_entry.get())
    ec_sta = float(ec_sta_entry.get())
    radius = float(radius_var.get())
    h1 = float(h1_var.get())

    start_point = (float(start_pointx_entry.get()),float(start_pointy_entry.get()))
    arc_length = ec_sta - bc_sta

    
    # Calculate arc points
    center, end_point ,mid_point = calculate_arc_points(h1, start_point, radius, arc_length)
    center2, end_point2 , mid_point2 = calculate_arc_points(h1, start_point, -radius, arc_length)
    print('\n---------------\n')
    print('\n우향곡선\n')
    print('곡선 시작점 좌표 : ',start_point)
    print('우향곡선 중간점  좌표 : ',mid_point)
    print('우향곡선 끝 좌표 : ',end_point)
    print('우향곡선 중심 좌표 : ',center)
    print('\n좌향곡선\n')
    print('곡선 시작점 좌표 : ',start_point)
    print('좌향곡선 중간점  좌표 : ',mid_point2)
    print('좌향곡선 끝 좌표 : ',end_point2)
    print('좌향곡선 중심 좌표 : ',center2)   
    print('\n---------------\n')
    
    # Draw plot
    ax.set_aspect('equal')
    ax.scatter(*zip(*[start_point, end_point , mid_point]), color='blue', marker='o')
    ax.scatter(*zip(*[start_point, end_point2, mid_point2]), color='red', marker='o')
    
    x_arc, y_arc = draw_arc(start_point, end_point, center)
    x_arc2, y_arc2 = draw_arc(start_point, end_point2, center2)
    ax.plot(x_arc, y_arc, label='우향', color='blue')
    ax.plot(x_arc2, y_arc2, label='좌향', color='red')

    ax.text(*start_point, 'BC', fontsize=12, ha='left',color='BLACK')
    ax.text(*end_point, 'EC', fontsize=12, ha='left',color='BLUE')
    ax.text(*end_point2, 'EC', fontsize=12, ha='left',color='RED')
    
    ax.set_title('시작점과 곡선반경 길이로 끝점 찾기')
    ax.set_xlabel('X-axis')
    ax.set_ylabel('Y-axis')
    ax.legend()
    ax.grid(True)

    canvas.draw()  # Redraw the plot

# GUI setup
root = tk.Tk()
root.title("시작점과 곡선반경 길이로 끝점 찾기")

# Labels and entries
tk.Label(root, text="시점:").grid(row=0, column=0, sticky="e")
bc_sta_entry = tk.Entry(root)
bc_sta_entry.grid(row=0, column=1)
bc_sta_entry.insert(0, "123.456")
bc_sta_entry.bind('<KeyRelease>', update_plot)

tk.Label(root, text="종점:").grid(row=1, column=0, sticky="e")
ec_sta_entry = tk.Entry(root)
ec_sta_entry.grid(row=1, column=1)
ec_sta_entry.insert(0, "789.123")
ec_sta_entry.bind('<KeyRelease>', update_plot)

# Labels and entries
tk.Label(root, text="시작 x좌표:").grid(row=0, column=1, sticky="e")
start_pointx_entry = tk.Entry(root)
start_pointx_entry.grid(row=0, column=2)
start_pointx_entry.insert(0, "0")
start_pointx_entry.bind('<KeyRelease>', update_plot)


# Labels and entries
tk.Label(root, text="시작 y좌표:").grid(row=1, column=1, sticky="e")
start_pointy_entry = tk.Entry(root)
start_pointy_entry.grid(row=1, column=2)
start_pointy_entry.insert(0, "0")
start_pointy_entry.bind('<KeyRelease>', update_plot)

tk.Label(root, text="곡선반경:").grid(row=2, column=0, sticky="e")
radius_var = tk.DoubleVar(value=600)
radius_slider = tk.Scale(root, from_=0, to=9999, orient=tk.HORIZONTAL, variable=radius_var, command=update_plot, resolution=100)
radius_slider.grid(row=2, column=1)

# 직접 입력할 수 있는 입력 상자
radius_entry = tk.Entry(root, textvariable=radius_var)
radius_entry.grid(row=2, column=2)
radius_entry.bind('<KeyRelease>', update_plot)

tk.Label(root, text="h1:").grid(row=3, column=0, sticky="e")
h1_var = tk.DoubleVar(value=90)
h1_slider = tk.Scale(root, from_=0, to=360, orient=tk.HORIZONTAL, variable=h1_var, command=update_plot)
h1_slider.grid(row=3, column=1)

# 직접 입력할 수 있는 입력 상자
h1_entry = tk.Entry(root, textvariable=h1_var)
h1_entry.grid(row=3, column=2)
h1_entry.bind('<KeyRelease>', update_plot)

# Initialize the plot
fig = plt.figure()
ax = fig.add_subplot()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=4, columnspan=2)

# Run the GUI
root.mainloop()
