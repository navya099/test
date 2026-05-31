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

def draw_arc(direction,start_point, end_point, center_point):
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

    return x_arc, y_arc

# Create a tkinter window

def update_plot(event=None):
    ax.clear()  # Clear the current plot

    R = float(radius_var.get())
    X1 = float(x1_var.get())
    D = float(delta_var.get())
    
    Y1= X1**3 / (6 * R * X1)

    theta_pc = math.atan(X1 / (2 * R)) #PC점의 접선각( 라디안)
    theta_pc_D = np.degrees(theta_pc)

    direction = -1

    PC = (X1,Y1)
    SP = (0,0)
    O = calculate_destination_coordinates(X1, Y1, theta_pc_D  + 90, R)
    CP = calculate_destination_coordinates(O[0], O[1], D, R)

    ax.set_xlim(0,CP[0])
    ax.set_ylim(0,CP[1])

    

    
    # Plot some data (you can replace this with your own plot)

    x = np.linspace(0, X1, 100)

    # y 값 계산
    y = x**3 / (6 * R * X1)

    ax.plot(x, y, linestyle='-', color='blue')
    #ax.plot(*zip(*[PC, O]), linestyle='-', color='BLACK')

    #ax.scatter(O[0],O[1])

    ax.scatter(CP[0],CP[1])
    ax.scatter(O[0],O[1])

    # Create a point P on the graph (initial position: x=5, y=x**3 / (6*R*X1))
    point, = ax.plot([X1], [X1**3 / (6 * R * X1)], 'ro', markersize=5)
    xarc, yarc = draw_arc(direction,PC, CP, O)
    ax.plot(xarc, yarc, label='Circular Arc',color='RED')
    for text in ax.texts:
        text.remove()
    ax.text(PC[0],PC[1],'PC', fontsize=12, color='red')
    ax.text(SP[0],SP[1],'SP', fontsize=12, color='red')
    ax.text(CP[0],CP[1],'CP', fontsize=12, color='red')

    print('Y1 : ',Y1)
    print('DELTA : ',D -270)
    print('PC점의 접선각 : ',theta_pc_D)
    ax.grid(True)
    
    canvas.draw()
    
# Modify fig.canvas.mpl_connect('motion_notify_event', motion) as follows:
root = tk.Tk()
root.title("3차포물선 개형")

tk.Label(root, text="R:").grid(row=0, column=0, sticky="e")
radius_var = tk.DoubleVar(value=600)
radius_slider = tk.Scale(root, from_=0, to=9999, orient=tk.HORIZONTAL, variable=radius_var, command=update_plot, resolution=10)
radius_slider.grid(row=0, column=1)

tk.Label(root, text="X1:").grid(row=1, column=0, sticky="e")
x1_var = tk.DoubleVar(value=160)
x1_slider = tk.Scale(root, from_=0, to=630, orient=tk.HORIZONTAL, variable=x1_var, command=update_plot, resolution=10)
x1_slider.grid(row=1, column=1)

tk.Label(root, text="DELTA:").grid(row=2, column=0, sticky="e")
delta_var = tk.DoubleVar(value=160)
delta_slider = tk.Scale(root, from_=270, to=360, orient=tk.HORIZONTAL, variable=delta_var, command=update_plot, resolution=10)
delta_slider.grid(row=2, column=1)

# Initialize the plot
fig = plt.Figure(figsize=(6, 6))

ax = fig.add_subplot()
ax.set_aspect('auto')
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=4, columnspan=2)

ax.grid(True)

ax.set_xlabel('x')
ax.set_ylabel('y')

# 툴바 추가
# NavigationToolbar2Tk를 사용하여 그래프 위젯에 툴바 추가
# Create a frame to contain both the canvas and the toolbar
toolbar_frame = tk.Frame(root)
toolbar_frame.grid(row=5, columnspan=2)

toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
toolbar.update()
toolbar.grid(row=0, column=0, sticky="we") 

# Run the Tkinter event loop
root.mainloop()

