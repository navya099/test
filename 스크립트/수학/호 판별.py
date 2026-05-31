import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk  # 추가
import numpy as np
import math

def calculate_destination_coordinates(x1, y1, bearing, distance):
    # Calculate the destination coordinates given a starting point, bearing, and distance in Cartesian coordinates
    angle = math.radians(bearing)
    x2 = x1 + distance * math.cos(angle)
    y2 = y1 + distance * math.sin(angle)
    return x2, y2

def draw_arc(direction, start_point, end_point, center_point):
    x_start, y_start = start_point
    x_end, y_end = end_point
    x_center, y_center = center_point

    start_angle = np.degrees(np.arctan2(y_start - y_center, x_start - x_center))
    end_angle = np.degrees(np.arctan2(y_end - y_center, x_end - x_center))

    

    # Calculate radius
    radius = np.sqrt((x_center - x_start)**2 + (y_center - y_start)**2)
   
    
    # Adjust start_angle and end_angle if necessary
    if start_angle < 0:
        start_angle +=360
    if end_angle < 0:
        end_angle +=360
    print('start_angle',start_angle)
    print('end_angle',end_angle)
    
       
    fii = end_angle - start_angle #시계방향
    fii2 = 360 - abs(end_angle - start_angle) #반시계방향
    
    print('fii',fii)
    print('fii2',fii2)
    
    num_angles = 100
    
    unit =  fii / (num_angles -1)
    unit2 =  fii2 / (num_angles -1)
    
    print('unit',unit)
    print('unit2',unit2)
    
    array = []
    if direction == 1: #시계방향
        if start_angle > end_angle:
            for i in range(num_angles):
                angle = start_angle + unit * i
                array.append(angle)

        else:
            for i in range(num_angles):
                angle = start_angle - unit2 * i
                array.append(angle)
                
        print('시계방향')
        color = 'red'
        
    else: #반시계방향 덧셈
        if start_angle > end_angle:
            for i in range(num_angles):
                angle = start_angle + unit2 * i
                array.append(angle)
        else:
            for i in range(num_angles):
                angle = start_angle + unit * i
                array.append(angle)
        print('반시계방향')
        color ='blue'
        
    theta = np.radians(array)
    
    # Calculate arc coordinates
    x_arc = x_center + radius * np.cos(theta)
    y_arc = y_center + radius * np.sin(theta)

    print("곡선반경 = ",radius)
    
    a = np.degrees(theta[-1] - theta[0])
    
    print("CL = ",abs(radius * math.radians(a)))
    return x_arc, y_arc, color

def update_plot(event=None):
    ax.clear()  # Clear the current plot

    R = float(radius_var.get())
    start_angle = float(start_angle_var.get())
    end_angle = float(end_angle_var.get())
    direction = toggle_direction()
    
    center_point = (float(center_point_X_entry.get()),float(center_point_Y_entry.get()))
    start_point = calculate_destination_coordinates(center_point[0],center_point[1], start_angle, R)
    end_point = calculate_destination_coordinates(center_point[0],center_point[1], end_angle, R)

    x_arc, y_arc, color = draw_arc(direction,start_point, end_point, center_point)

    # Plot the arc
    plt.plot(x_arc, y_arc, label='Circular Arc',color= color)
    plt.scatter(*zip(*[start_point, center_point, end_point]), color=color, marker='o')
    plt.text(*start_point, 'BC', fontsize=12, ha='left',color=color)
    plt.text(*end_point, 'EC', fontsize=12, ha='left',color=color)

    print('BC좌표 :' , start_point)
    print('EC좌표 :' , end_point)
    
    ax.grid(True)
    
    canvas.draw()
    
def toggle_direction():
    result = 0
    if direction_var.get() == 1:
        result = 1
    else:
        result = 0
    canvas.draw()
    
    return result

def reset_values():
    center_point_X_entry.delete(0, tk.END)
    center_point_X_entry.insert(0, "193128.198511629")
    center_point_Y_entry.delete(0, tk.END)
    center_point_Y_entry.insert(0, "543059.548890971")
    
    radius_var.set(600)
    update_plot()

def exit_program():
    print("프로그램을 종료합니다.")
    root.destroy()
    
# Modify fig.canvas.mpl_connect('motion_notify_event', motion) as follows:
root = tk.Tk()
root.title("호 그리기")

#텍스트박스
tk.Label(root, text="중심 좌표 X:").grid(row=0, column=2, sticky="e")
center_point_X_entry = tk.Entry(root)
center_point_X_entry.grid(row=0, column=3)
center_point_X_entry.insert(0, "193128.198511629")
center_point_X_entry.bind('<KeyRelease>', update_plot)

tk.Label(root, text="중심 좌표 Y:").grid(row=1, column=2, sticky="e")
center_point_Y_entry = tk.Entry(root)
center_point_Y_entry.grid(row=1, column=3)
center_point_Y_entry.insert(0, "543059.548890971")
center_point_Y_entry.bind('<KeyRelease>', update_plot)

tk.Label(root, text="시작 각도:").grid(row=0, column=0, sticky="e")
start_angle_var = tk.DoubleVar(value=0)
start_angle_slider = tk.Scale(root, from_=0, to=360, orient=tk.HORIZONTAL, variable=start_angle_var, command=update_plot, resolution=10)
start_angle_slider.grid(row=0, column=1)

tk.Label(root, text="끝 각도:").grid(row=1, column=0, sticky="e")
end_angle_var = tk.DoubleVar(value=0)
end_angle_slider = tk.Scale(root, from_=0, to=360, orient=tk.HORIZONTAL, variable=end_angle_var, command=update_plot, resolution=10)
end_angle_slider.grid(row=1, column=1)

tk.Label(root, text="곡선반경:").grid(row=2, column=0, sticky="e")
radius_var = tk.DoubleVar(value=0)
radius_slider = tk.Scale(root, from_=0, to=9999, orient=tk.HORIZONTAL, variable=radius_var, command=update_plot, resolution=10)
radius_slider.grid(row=2, column=1)

#체크박스 변수
# Create the checkbox
direction_var = tk.IntVar(value=0)
direction_checkbox = tk.Checkbutton(root, text="시계방향", variable=direction_var, command=toggle_direction)
direction_checkbox.grid(row=2, column=3, columnspan=2, pady=10)

# Initialize the plot
fig = plt.figure(figsize=(6, 6))
ax = fig.add_subplot()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=6, columnspan=2)

#버튼 추가
# 초기화버튼 생성
reset_button = tk.Button(root, text="초기화", command=reset_values)
reset_button.grid(row=3, column=0, pady=10)

# 종료 버튼 생성
exit_button = tk.Button(root, text="종료", command=exit_program)
exit_button.grid(row=2, column=0, pady=10)

# 툴바 추가
# NavigationToolbar2Tk를 사용하여 그래프 위젯에 툴바 추가
# Create a frame to contain both the canvas and the toolbar
toolbar_frame = tk.Frame(root)
toolbar_frame.grid(row=5, columnspan=2)

toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
toolbar.update()
toolbar.grid(row=0, column=0, sticky="we") 

# Run the GUI
root.geometry("900x800")

root.mainloop()
