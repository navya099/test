import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk  # 추가
import numpy as np
import math

plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False

def calculate_destination_coordinates(x1, y1, bearing, distance):
    # Calculate the destination coordinates given a starting point, bearing, and distance in Cartesian coordinates
    angle = math.radians(bearing)
    x2 = x1 + distance * math.cos(angle)
    y2 = y1 + distance * math.sin(angle)
    return x2, y2

def calculate_bearing(x1, y1, x2, y2):
    # Calculate the bearing (direction) between two points in Cartesian coordinates
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.degrees(math.atan2(dy, dx))
    return bearing

def draw_arc(start_point, end_point, center_point):
    # 시작점, 끝점, 중심점 좌표 추출
    x_start, y_start = start_point
    x_end, y_end = end_point
    x_center, y_center = center_point

    # 호의 반지름과 시작 각도, 끝 각도 계산
    radius = np.sqrt((x_center - x_start)**2 + (y_center - y_start)**2)
    start_angle = np.degrees(np.arctan2(y_start - y_center, x_start - x_center))
    end_angle = np.degrees(np.arctan2(y_end - y_center, x_end - x_center))

    # 호를 그리기 위한 각도 배열 생성
    theta = np.linspace(start_angle, end_angle, 100)

    # 호의 좌표 계산
    x_arc = x_center + radius * np.cos(np.radians(theta))
    y_arc = y_center + radius * np.sin(np.radians(theta))

    return x_arc, y_arc    

def degrees_to_dms(degrees):
    """
    Converts decimal degrees to degrees, minutes, seconds.
    
    Args:
    degrees (float): Decimal degrees value.
    
    Returns:
    tuple: Degrees, minutes, seconds.
    """
    if degrees < 0:
        degrees = degrees * -1
        
    deg = int(degrees)
    minutes = int((degrees - deg) * 60)
    seconds = (degrees - deg - minutes / 60) * 3600

    
    return f"IA = {deg}° {minutes}' {seconds:.2f}\""


    angle = angle

def format_distance(number):
    negative = False
    if number < 0:
        negative = True
        number = abs(number)
        
    km = int(number) // 1000
    remainder = "{:.2f}".format(number % 1000)
    formatted_distance = "{:d}km{:06.2f}".format(km, float(remainder))
    
    if negative:
        formatted_distance = "-" + formatted_distance
    
    return formatted_distance

def calculate_simple_curve(BC,EC,R,NEW_R):

    if  R == 0 or NEW_R == 0 :
        print('입력값 오류 곡선반경은 0보다 커야함')
        return
    if BC > EC:
        print('입력값 오류 BC는 EC보다 커야함')
        return
    
    CL= EC-BC
    IA = CL/R
    TL = R * math.tan(IA/2)

    IA_DEGREE = math.degrees(IA)
    IA_DMS = degrees_to_dms(IA_DEGREE)

    IP_STA = BC + TL

    NEW_TL = NEW_R * math.tan(IA/2)
    NEW_CL = NEW_R * IA

    NEW_BC = IP_STA - NEW_TL
    NEW_EC = NEW_BC + NEW_CL

    BC_XY = (0,0)
    O_XY = (R,0)
    IP_XY = (0,TL)
    EC_XY = calculate_destination_coordinates(R, 0, 180-IA_DEGREE, R)


    NEW_BC_XY = calculate_destination_coordinates(IP_XY[0], IP_XY[1], 270, NEW_TL)
    NEW_O_XY = (NEW_BC_XY[0]+NEW_R ,NEW_BC_XY[1])

    NEW_EC_XY = calculate_destination_coordinates(NEW_O_XY[0], NEW_O_XY[1], 180-IA_DEGREE, NEW_R)


    BP_IP_BREAING = calculate_bearing(0, 0, 0, TL)
    print("\nBP_IP_BREAING : ",BP_IP_BREAING)
    IP_EP_BREAING = calculate_bearing(0, TL, 0, TL)

    O_BC_BEARING = calculate_bearing(R,0,BC_XY[0],BC_XY[1])
    O_BC_BEARING_RAD = math.radians(O_BC_BEARING)

    O_SP_BEARING = O_BC_BEARING - IA_DEGREE/2
    O_SP_BEARING_RAD = math.radians(O_BC_BEARING)

    print("O_BC_BEARING : ",O_BC_BEARING)
    print("O_BC_BEARING_RAD : ",O_BC_BEARING_RAD)
    print("O_SP_BEARING : ",O_SP_BEARING)
    print("O_SP_BEARING_RAD : ",O_SP_BEARING_RAD)

    SP_XY = calculate_destination_coordinates(R, 0, O_SP_BEARING, R)
    NEW_SP_XY = calculate_destination_coordinates(NEW_O_XY[0], NEW_O_XY[1], O_SP_BEARING, NEW_R)


    print("IP_XY" ,IP_XY)
    print("O_XY" ,O_XY)
    print("EC_XY" ,EC_XY)
    print("SP_XY" ,SP_XY)



    print("\n변경전\n")
    print(IA_DMS)
    print("R : ",R)
    print("TL : ",TL)
    print("CL : ",CL)
    print("IP 정측점 : ",IP_STA)
    print("IP 역측점 : ",BC + CL/2)

    print("\n변경후\n")
    print(IA_DMS)
    print("R : ",NEW_R)
    print("TL : ",NEW_TL)
    print("CL : ",NEW_CL)
    print("IP 정측점 : ",IP_STA)
    print("IP 역측점 : ",NEW_BC + NEW_CL/2)
    print("새 BC : ",NEW_BC)
    print("새 EC : ",NEW_EC)


    print("\nOPENBVE 구문 복사\n")
    print(NEW_BC,",.CURVE ",NEW_R)
    print(NEW_EC,",.CURVE 0")

    return IA_DMS ,BC_XY , IP_XY, EC_XY , O_XY , TL , CL, NEW_BC_XY , NEW_EC_XY ,NEW_O_XY ,NEW_TL , NEW_CL,NEW_BC , NEW_EC

#메인함수
def update_plot(event=None):

    ax.clear()  # Clear the current plot
    
    # Get values from widgets
    BC = float(bc_sta_entry.get())
    EC = float(ec_sta_entry.get())
    R = float(radius_var.get())

    NEW_R = float(new_radius_var.get())

    IA_DMS , BC_XY , IP_XY, EC_XY , O_XY , TL , CL, NEW_BC_XY , NEW_EC_XY ,NEW_O_XY ,NEW_TL , NEW_CL ,NEW_BC , NEW_EC= calculate_simple_curve(BC,EC,R,NEW_R)
    
    # Plot the arc and points
    
    
    ax.scatter(*zip(*[BC_XY, IP_XY, EC_XY]), color='blue', marker='o')
    ax.scatter(*zip(*[NEW_BC_XY, NEW_EC_XY]), color='red', marker='o')

    # Connect the points with a line
    if R<NEW_R and R>0:
        
        ax.plot(*zip(*[NEW_BC_XY, IP_XY, NEW_EC_XY]), linestyle='--', color='GREEN')

        ax.plot(*zip(*[BC_XY, IP_XY, EC_XY]), linestyle='-', color='BLACK')
    elif R>NEW_R and R<0:
        ax.plot(*zip(*[NEW_BC_XY, IP_XY, NEW_EC_XY]), linestyle='--', color='GREEN')

        ax.plot(*zip(*[BC_XY, IP_XY, EC_XY]), linestyle='-', color='BLACK')
    else:  
        ax.plot(*zip(*[BC_XY, IP_XY, EC_XY]), linestyle='-', color='BLACK')
        

    # 시작점, 끝점, 중심점 좌표
    start_point = BC_XY
    end_point = EC_XY
    center_point = O_XY

    new_start_point = NEW_BC_XY
    new_end_point = NEW_EC_XY
    new_center_point = NEW_O_XY

    # 그래프에 호를 그림
    # Draw the arc
    x_arc, y_arc = draw_arc(BC_XY, EC_XY, O_XY)
    new_x_arc, new_y_arc = draw_arc(NEW_BC_XY, NEW_EC_XY, NEW_O_XY)

    ax.plot(x_arc, y_arc, label='기존 선형', color='BLUE')
    ax.plot(new_x_arc, new_y_arc, label='변경 선형', color='RED')

    # 호 그리기
    draw_arc(start_point, end_point, center_point)
    draw_arc(new_start_point, new_end_point, new_center_point)

    IA_POS = (R/2,R/2)
    R_POS = (IA_POS[0], IA_POS[1]-R)
    TL_POS = (IA_POS[0], IA_POS[1]-R*2)
    CL_POS = (IA_POS[0], IA_POS[1]-R*3)
    X_POS = (IA_POS[0], IA_POS[1]-R*4)
    Y_POS = (IA_POS[0], IA_POS[1]-R*5)

    NEW_R_POS = (IA_POS[0]+100, IA_POS[1]-30)
    NEW_TL_POS = (IA_POS[0]+150, IA_POS[1]-60)
    NEW_CL_POS = (IA_POS[0]+150, IA_POS[1]-90)

    R_TEXT = f"R = {R:.0f}"
    TL_TEXT = f"TL = {TL:.2f}"
    CL_TEXT = f"CL = {CL:.2f}"
    X_TEXT = f"X = {IP_XY[1]:.3f}"
    Y_TEXT = f"Y = {IP_XY[0]:.3f}"

    BC_STA = f"BC = {format_distance(BC)}"
    EC_STA = f"EC = {format_distance(EC)}"

    NEW_BC_STA = f"BC = {format_distance(NEW_BC)}"
    NEW_EC_STA = f"EC = {format_distance(NEW_EC)}"

    #기존
    ax.text(*IP_XY, 'IP', fontsize=12, ha='right',color='BLACK')


    # 폰트 설정
    custom_font = ("굴림체", 12)  # 폰트 및 크기 지정
    
    # 텍스트 레이블 생성 윈도우창에
    text_label = tk.Label(root, text=IA_DMS, bg=root.cget('bg'), fg="black",font = custom_font)
    text_label.place(x=250, y=450)  # 텍스트를 (100, 100) 좌표에 배치
    text_label = tk.Label(root, text=R_TEXT, bg=root.cget('bg'), fg="black",font = custom_font)
    text_label.place(x=250, y=470)  # 텍스트를 (100, 100) 좌표에 배치 20간격
    text_label = tk.Label(root, text=TL_TEXT, bg=root.cget('bg'), fg="black",font = custom_font)
    text_label.place(x=250, y=490)
    text_label = tk.Label(root, text=CL_TEXT, bg=root.cget('bg'), fg="black",font = custom_font)
    text_label.place(x=250, y=510)
    text_label = tk.Label(root, text=X_TEXT, bg=root.cget('bg'), fg="black",font = custom_font)
    text_label.place(x=250, y=530)
    text_label = tk.Label(root, text=Y_TEXT, bg=root.cget('bg'), fg="black",font = custom_font)
    text_label.place(x=250, y=550)
    
    ax.text(*BC_XY, BC_STA, fontsize=12, ha='left',color='BLUE')
    ax.text(*EC_XY, EC_STA, fontsize=12, ha='right' ,color='BLUE')

    #뉴


    text_label = tk.Label(root, text=f"({NEW_R:.0f})", bg=root.cget('bg'), fg="RED",font = custom_font)
    text_label.place(x=350, y=470)
    
    text_label = tk.Label(root, text=f"({NEW_TL:.2f})", bg=root.cget('bg'), fg="RED",font = custom_font)
    text_label.place(x=350, y=490)

    text_label = tk.Label(root, text=f"({NEW_CL:.2f})", bg=root.cget('bg'), fg="RED",font = custom_font)
    text_label.place(x=350, y=510)

    

    ax.text(*NEW_BC_XY, NEW_BC_STA, fontsize=12, ha='left',color='RED')

    ax.text(*NEW_EC_XY, NEW_EC_STA, fontsize=12, ha='right' ,color='RED')

    ax.set_title('BVE 곡선반경 측점 찾기')
    ax.set_xlabel('X-axis')
    ax.set_ylabel('Y-axis')
    ax.legend()
    ax.grid(True)

    canvas.draw()  # Redraw the plot

def reset_values():
    bc_sta_entry.delete(0, tk.END)
    bc_sta_entry.insert(0, "123.456")
    ec_sta_entry.delete(0, tk.END)
    ec_sta_entry.insert(0, "789.123")
    radius_var.set(600)
    new_radius_var.set(700)
    update_plot()

def exit_program():
    print("프로그램을 종료합니다.")
    root.destroy()

def toggle_aspect_ratio():
    if aspect_var.get() == 1:
        ax.set_aspect('equal', adjustable='box')
    else:
        ax.set_aspect('auto', adjustable='box')
    canvas.draw()
    
root = tk.Tk()
root.title("BVE 곡선반경 측점 찾기")

# Labels and entries
tk.Label(root, text="BC:").grid(row=0, column=0, sticky="e")
bc_sta_entry = tk.Entry(root)
bc_sta_entry.grid(row=0, column=1)
bc_sta_entry.insert(0, "123.456")
bc_sta_entry.bind('<KeyRelease>', update_plot)

tk.Label(root, text="EC:").grid(row=1, column=0, sticky="e")
ec_sta_entry = tk.Entry(root)
ec_sta_entry.grid(row=1, column=1)
ec_sta_entry.insert(0, "789.123")
ec_sta_entry.bind('<KeyRelease>', update_plot)

tk.Label(root, text="기존 곡선반경:").grid(row=2, column=0, sticky="e")
radius_var = tk.DoubleVar(value=600)
radius_slider = tk.Scale(root, from_=0, to=9999, orient=tk.HORIZONTAL, variable=radius_var, command=update_plot, resolution=10)
radius_slider.grid(row=2, column=1)

# 직접 입력할 수 있는 입력 상자
radius_entry = tk.Entry(root, textvariable=radius_var)
radius_entry.grid(row=2, column=2)
radius_entry.bind('<KeyRelease>', update_plot)


tk.Label(root, text="새 곡선반경:").grid(row=3, column=0, sticky="e")
new_radius_var = tk.DoubleVar(value=700)
new_radius_slider = tk.Scale(root, from_=0, to=9999, orient=tk.HORIZONTAL, variable=new_radius_var, command=update_plot, resolution=10)
new_radius_slider.grid(row=3, column=1)

# 직접 입력할 수 있는 입력 상자
new_radius_entry = tk.Entry(root, textvariable=new_radius_var)
new_radius_entry.grid(row=3, column=2)
new_radius_entry.bind('<KeyRelease>', update_plot)

# 버튼 생성
reset_button = tk.Button(root, text="초기화", command=reset_values)
reset_button.grid(row=3, column=0, pady=10)

# 종료 버튼 생성
exit_button = tk.Button(root, text="종료", command=exit_program)
exit_button.grid(row=2, column=0, pady=10)

# Create a variable to store the checkbox state
aspect_var = tk.IntVar(value=0)

# Create the checkbox
aspect_checkbox = tk.Checkbutton(root, text="비율 동일하게", variable=aspect_var, command=toggle_aspect_ratio)
aspect_checkbox.grid(row=0, column=3, columnspan=2, pady=10)

# Initialize the plot
fig = plt.figure(figsize=(6, 6))
ax = fig.add_subplot()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=4, columnspan=2)

# 툴바 추가
# NavigationToolbar2Tk를 사용하여 그래프 위젯에 툴바 추가
# Create a frame to contain both the canvas and the toolbar
toolbar_frame = tk.Frame(root)
toolbar_frame.grid(row=5, columnspan=2)

toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
toolbar.update()
toolbar.grid(row=0, column=0, sticky="we") 

# Run the GUI
root.mainloop()
