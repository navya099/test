import threading
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk  # 추가
import numpy as np
import math

plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False

def input_thread():
    global user_input
    user_input = input("사용자 입력을 기다립니다: ")

def gui_thread():
    root = tk.Tk()
    label = tk.Label(root, text="GUI 메인 루프를 실행합니다.")
    label.pack()
    root.mainloop()
    
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

def calculate_distance(x1, y1, x2, y2):
    # Calculate the distance between two points in Cartesian coordinates
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    distance_x = abs(x2 - x1)
    distance_y = abs(y2 - y1)
    return distance


def degrees_to_radians(degrees):
    return degrees * (math.pi / 180)

def radians_to_degrees(radians):
    return radians * (180 / math.pi)

def move_point(p, a, b):
    """
    주어진 점 P에서 x축으로 a만큼, y축으로 b만큼 이동한 새로운 좌표를 계산합니다.
    
    Args:
    p (tuple): 점 P의 좌표를 나타내는 튜플 (x, y).
    a (float): x축으로 이동할 거리.
    b (float): y축으로 이동할 거리.
    
    Returns:
    tuple: 이동 후의 좌표를 나타내는 튜플 (new_x, new_y).
    """
    x, y = p
    new_x = x + a
    new_y = y + b
    return new_x, new_y

def move_point_by_bearing(p, bearing_x, distance_a, bearing_y, distance_b):
    """
    주어진 점 P에서 방위각 X로 a만큼, 방위각 Y로 b만큼 이동한 새로운 좌표를 계산합니다.
    
    Args:
    p (tuple): 점 P의 좌표를 나타내는 튜플 (x, y).
    bearing_x (float): 방위각 X (도 단위).
    distance_a (float): 방위각 X로 이동할 거리.
    bearing_y (float): 방위각 Y (도 단위).
    distance_b (float): 방위각 Y로 이동할 거리.
    
    Returns:
    tuple: 이동 후의 좌표를 나타내는 튜플 (new_x, new_y).
    """
    x, y = p
    # 방위각을 라디안으로 변환
    bearing_x_rad = math.radians(bearing_x)
    bearing_y_rad = math.radians(bearing_y)
    
    # 이동 거리에 각각의 방위각에 해당하는 x, y 방향 성분 계산
    delta_x_a = distance_a * math.cos(bearing_x_rad)
    delta_y_a = distance_a * math.sin(bearing_x_rad)
    
    delta_x_b = distance_b * math.cos(bearing_y_rad)
    delta_y_b = distance_b * math.sin(bearing_y_rad)
    
    # 새로운 좌표 계산
    new_x = x + delta_x_a + delta_x_b
    new_y = y + delta_y_a + delta_y_b
    
    return new_x, new_y

def calculate_spiral(design_speed,direction,BP_IP_BREAING,IP_EP_BREAING,BP_XY,EP_XY,R,IP_XY,IA):
    
    #변수설정
    gauge = 1435 #mm단위
    v_ds = design_speed #설계속도
    Rc = R #R 원곡선반경
    cant  =  (11.8 * v_ds **2 ) / R
    if cant >= 160:
        cant = 160
        
    Ls = 0 #완화곡선 길이
    Lc = 0 #원곡선 길이
    TL = 0 #원곡선 TL

    m0 = BP_XY # BP 좌표
    m1 = IP_XY #IP 좌표
    m2 = EP_XY #EP
    h1 = BP_IP_BREAING #방위각1(도)
    h2 = IP_EP_BREAING #방위각2(도)
    
    Lb0 = calculate_distance(BP_XY[0], BP_XY[1], IP_XY[0], IP_XY[1]) #BP-IP거리
    Lb1 = calculate_distance(IP_XY[0], IP_XY[1], EP_XY[0], EP_XY[1]) #IP-EP거리
    
    
    delta = math.degrees(IA) #교각IA
    deltaRad = IA #교각IA (라다안)

    thetaD = 180-delta
    thetaR = degrees_to_radians(thetaD)
    delta_C = 0
    delta_S = 0

    

    m_values = {
    70: 600,
    120: 900,
    150: 1100,
    200: 1450,
    250: 1850,
    300: 2200,
    350: 2550,
    400: 2950
    }

    m = m_values.get(v_ds, 7.31 * v_ds)
    
    x1 = m * (cant * 0.001) #X1
    theta_pc = math.atan(x1 / (2 * Rc)) #PC점의 접선각( 라디안)
    x2 = x1 - (Rc * math.sin((theta_pc))) # X2
    Ls = x1 * (1 + ((math.tan(theta_pc)**2)) / 10) #완화곡선 길이
    
    TotalY = (math.pow(x1,2))/(6*Rc) # Y1
    S = TotalY - Rc * (1- math.cos((theta_pc))) #이정량 F
    F = S * math.tan((delta) / 2) #수평좌표차 K
    W = (Rc + S)* math.tan((delta/2)* math.pi/180) # W
    IT = x2 + W # TL
    Lc = Rc * (deltaRad - 2*(theta_pc)) #원곡선 길이
    TotalL = Lc + 2 * Ls #전체 CL

    
    #3차포물선 제원 출력
    print("\n------------------\n")
    print("\n3차포물선 제원 출력\n")
    print("설계속도  =",v_ds , 'km/h' )
    print("캔트 =",cant )
    print("m =",m )
    print("x1 =",x1 )
    print("PC점의 접선각 =",degrees_to_dms(radians_to_degrees(theta_pc) ))
    print("x2 =",x2 )
    print("완화곡선 길이 L =",Ls)
    print("Y1 =",TotalY)
    print("이정량 F =",S )
    print("수평좌표차 K =",F )
    print("W =",W )
    print("TL =",IT )
    print("원곡선 길이  =",Lc )
    print("CL  =",TotalL )
    print("\n------------------\n")
    
    if delta_S < 0:
        print("교각이 작아 완화곡선을 설치 할 수 없습니다. 설계속도를 변경하세요. 현재 교각: ", round(delta * 100) / 100, "°.")
        raise ValueError("교각이 너무 작아 완화곡선을 설치할 수 없습니다.")

    '''	
    rmin1 = 1.39 * math.sqrt(Rc * Ls) # method 1
    rmin2 = math.sqrt(math.pow(v_ds,3)/(math.pow(3.6,3)*0.3*deltaRad))# method 2
    rmin = 0

    if rmin1 > rmin2:
        rmin = rmin1
    elif rmin1 < rmin2:
        rmin = rmin2
    else:			
        rmin = rmin2 # @ rmin = rmin1	
		
    if Rc < rmin:
        print('현재 교각의 최소 곡선반경은 ' + str(rmin) + ' m.' + " 설계속도를 변경하세요.")
        raise ValueError("최소곡선반경을 만족하지 않아 완화곡선을 설치할 수 없습니다.")
    '''



    
    K = Ls/2
    ntp1  = calculate_destination_coordinates(IP_XY[0], IP_XY[1],BP_IP_BREAING+180, IT) #SP점 위치
    ntp2 = calculate_destination_coordinates(IP_XY[0], IP_XY[1],IP_EP_BREAING, IT)#PS점 위치

    
    


    tditc0 = move_point(ntp1, TotalY * direction, x1)#PC점 위치
    tditc1 = move_point_by_bearing(ntp2, h2, -x1, h2-90, TotalY*direction)#CP점 위치
    
    print("\n------------------\n")
    print("\n좌표 출력\n")
    print("SP 좌표  = ",ntp1)
    print("PC 좌표  = ",tditc0)
    print("CP 좌표  = ",tditc1)
    print("PS 좌표  = ",ntp2)

    
    #좌향 + 우향 -각도
    # O_PC_ANGLE 계산
    if direction == 1:
        if convert_bearing(h1) + radians_to_degrees(theta_pc) - 90 < 0:
            result = convert_bearing(h1) + radians_to_degrees(theta_pc) - 90 + 360
        else:
            result = convert_bearing(h1) + radians_to_degrees(theta_pc) - 90
    else:
        if convert_bearing(h1) - radians_to_degrees(theta_pc) + 90 > 360:
            result = convert_bearing(h1) - radians_to_degrees(theta_pc) + 90 - 360
        else:
            result = convert_bearing(h1) - radians_to_degrees(theta_pc) + 90

    O_PC_ANGLE =  result #O>PC 방위각
    
    CURVE_CENTER_XY = (math.sin((O_PC_ANGLE+180)*math.pi/180)*Rc+tditc0[0],
                       math.cos((O_PC_ANGLE+180)*math.pi/180)*Rc+tditc0[1])
    
    
    
    print("O→PC Θ =",degrees_to_dms(O_PC_ANGLE))
    print("CURVE_CENTER = ",CURVE_CENTER_XY)

    # Cubic Parabola : TotalX = Ls  (full length of transition by assumption)
    parts = 30; # any value, higher = more precision
    ts = Ls / parts #transition segment divided by any value (for plotting)
    
    tarr = []
    tarr2 = []
    scp1 = 0
    scp2 = 0

    # plotting entering spiral curve
    for i in range(parts + 1):
        if i == 0:
            tarr.append(ntp1)
        elif i == parts:
            scp1x = calculate_destination_coordinates(ntp1[0], ntp1[1], h1, Ls)  # 임의점 x
            scp1y = calculate_destination_coordinates(scp1x[0], scp1x[1], h1 + (90 * -direction), TotalY)  # 임의점 y
            xo = calculate_bearing(tarr[i - 1][0], tarr[i - 1][1], scp1y[0], scp1y[1])  # 임의점 방위각
            xd = calculate_distance(tarr[i - 1][0], tarr[i - 1][1], scp1y[0], scp1y[1])  # 임의점 거리
            scp1 = calculate_destination_coordinates(tarr[i - 1][0], tarr[i - 1][1], xo, xd)  # 임의점 좌표
            tarr.append(scp1)
        else:
            yi = calculate_destination_coordinates(ntp1[0], ntp1[1], h1, ts * i)
            ycd = (ts * i) ** 3 / (6 * Rc * Ls)
            yd = calculate_destination_coordinates(yi[0], yi[1], h1 + (90 * -direction), ycd)
            xo = calculate_bearing(tarr[i - 1][0], tarr[i - 1][1], yd[0], yd[1])
            xd = calculate_distance(tarr[i - 1][0], tarr[i - 1][1], yd[0], yd[1])
            xi = calculate_destination_coordinates(tarr[i - 1][0], tarr[i - 1][1], xo, xd)
            tarr.append(xi)
            
    # plotting exiting spiral curve
    #direction 토목좌표계에서는 반대임
    for i in range(parts+1):   
        if i == 0 :
                tarr2.append(ntp2)	#PS	  		 	 
        elif i== parts:		
                tarr2.append(tditc1)	  	#CP	 
        else:
            yi = calculate_destination_coordinates(ntp2[0],ntp2[1], h2,-ts * i)
            ycd = (math.pow((ts * i),3))/(6 * Rc * Ls)
            yd = calculate_destination_coordinates(yi[0], yi[1], h2-(90 * -direction),-ycd)
            xo = calculate_bearing(tarr2[i-1][0], tarr2[i-1][1], yd[0], yd[1])
            xd = calculate_distance(tarr2[i-1][0], tarr2[i-1][1], yd[0], yd[1])
            xi = calculate_destination_coordinates(tarr2[i-1][0], tarr2[i-1][1], xo, xd);
            tarr2.append(xi);
            # --- end

    return IT,TotalL,ntp1,ntp2,tditc0,tditc1,Ls,Lc,CURVE_CENTER_XY,tarr,tarr2,cant

def create_number(a, b, unit):
    result = []
    a = round(a / unit) * unit
    b = round(b / unit) * unit
    for num in range(int(a), int(b) + 1):
        if num % unit == 0:
            result.append(num)

    return result

def calculate_Instantaneous_radius(cant ,R, Ls, SP_STA, PC_STA, CP_STA, PS_STA):
    Instantaneous_radius = []
    A = math.sqrt(Ls * R)
    chain = 25 #계산간격
    
    START_STA_LIST = create_number(SP_STA, PC_STA, chain)  # This function call needs to be defined
    END_STA_LIST = create_number(CP_STA, PS_STA, chain)
    FINAL_STA_LIST = []
    
    Total_L = START_STA_LIST[-1] - START_STA_LIST[0]
    Total_L2 = END_STA_LIST[-1] - END_STA_LIST[0]
    
    final_cant = []

    #캔트변수 초기화
    parts_number_cant = int(Total_L  / chain ) # 캔트체감갯수
    parts_number_cant2 = int(Total_L2  / chain ) # 종점부캔트체감갯수
    
    parts_cant = cant /  parts_number_cant #체감량
    parts_cant2 = cant /  parts_number_cant2 #종점부 체감량
    
    initial_cant = 0 #각 측점별 캔트
    
    i = 0
    
    for i in range(len(START_STA_LIST)):  # Corrected the syntax of the loop
        L = SP_STA - START_STA_LIST[i]  # Corrected the assignment
        THETA = (L ** 2) / (2 * R * Ls)  # Corrected the assignment
        radius = A / math.sqrt(2 * math.sin(THETA) * math.cos(THETA) ** 5)

        initial_cant =  parts_cant * i#각 측점별 캔트
        final_cant.append(initial_cant)
        

        
        Instantaneous_radius.append(radius)  # Corrected the appending
        if i == len(START_STA_LIST) - 1:
            Instantaneous_radius[i] = R
            break

    i = 0
    for i in range(len(END_STA_LIST)):  # Corrected the syntax of the loop
        L = PS_STA - END_STA_LIST[i]  # Corrected the assignment
        THETA = (L ** 2) / (2 * R * Ls)  # Corrected the assignment
        radius = A / math.sqrt(2 * math.sin(THETA) * math.cos(THETA) ** 5)


        initial_cant =  cant - parts_cant2 * i#각 측점별 캔트
        final_cant.append(initial_cant)
        
        # Corrected the assignment
        Instantaneous_radius.append(radius)  # Corrected the appending
        if i == len(END_STA_LIST) - 1:
            Instantaneous_radius[-1] = 0
            break
    FINAL_STA_LIST = START_STA_LIST + END_STA_LIST
    return FINAL_STA_LIST,Instantaneous_radius,final_cant

def convert_bearing(bearing):
    # 방위각을 북측 방위각으로 변환
    bearing = bearing - 90
    if bearing < 0:
        bearing = bearing + 360
    return bearing

#코드의 맨처음

#메인함수
def update_plot(event=None):
    ax.clear()  # Clear the current plot
    
    # Get values from widgets
    BC = float(bc_sta_entry.get())
    EC = float(ec_sta_entry.get())
    R = float(radius_var.get())
    design_speed =  float(design_speed_var.get())
    direction = toggle_reverse_curve()
    
    CL= EC-BC
    IA = CL/R
    TL = R * math.tan(IA/2)

    IA_DEGREE = math.degrees(IA)
    IA_DMS = degrees_to_dms(IA_DEGREE)

    IP_STA = BC + TL


    BC_XY = (0,0)
    if direction < 0:
        O_XY = (-R,0)
        EC_XY = calculate_destination_coordinates(O_XY[0], O_XY[1], IA_DEGREE, R)
    else:    
        O_XY = (R,0)
        EC_XY = calculate_destination_coordinates(O_XY[0], O_XY[1], 180-IA_DEGREE, R)

    IP_XY = (0,TL)

    BP_IP_BREAING = calculate_bearing(BC_XY[0],BC_XY[1], IP_XY[0], IP_XY[1])

    BP_XY = calculate_destination_coordinates(IP_XY[0], IP_XY[1],BP_IP_BREAING + 180 , 2*TL)


    BP_BC_distance = calculate_distance(BP_XY[0], BP_XY[1], BC_XY[0], BC_XY[1])
    BP_STA = BC - BP_BC_distance



    IP_EP_BREAING = calculate_bearing(IP_XY[0], IP_XY[1], EC_XY[0],EC_XY[1])
    EP_XY = calculate_destination_coordinates(IP_XY[0], IP_XY[1], IP_EP_BREAING, 2*TL)


    EC_EP_distance = calculate_distance(EC_XY[0], EC_XY[1], EP_XY[0], EP_XY[1])
    EP_STA = EC + EC_EP_distance

    IP_EP_distance = calculate_distance(IP_XY[0], IP_XY[1], EP_XY[0], EP_XY[1])

    O_BC_BEARING = calculate_bearing(R,0,BC_XY[0],BC_XY[1])
    O_BC_BEARING_RAD = math.radians(O_BC_BEARING)

    O_SP_BEARING = O_BC_BEARING - IA_DEGREE/2
    O_SP_BEARING_RAD = math.radians(O_BC_BEARING)

    """
    print("\nBP_IP_BREAING : ",BP_IP_BREAING)
    print("\nBP좌표 : ",BP_XY)
    print("\BP_BC_distance : ",BP_BC_distance)
    print("\BP 측점 : ",BP_STA)
    print("\nEP좌표 : ",EP_XY)

    print("O_BC_BEARING : ",O_BC_BEARING)
    print("O_BC_BEARING_RAD : ",O_BC_BEARING_RAD)
    print("O_SP_BEARING : ",O_SP_BEARING)
    print("O_SP_BEARING_RAD : ",O_SP_BEARING_RAD)
    """

    SP_XY = calculate_destination_coordinates(R, 0, O_SP_BEARING, R)



    print("\n------------------\n")
    print("\n기본 제원 출력\n")
    print("BP좌표 = " ,BP_XY)
    print("IP좌표 = " ,IP_XY)
    print("EP좌표 = " ,EP_XY)
    print("곡선반경  = " ,str(R)+"m")
    print("방위각 1 = " ,degrees_to_dms(convert_bearing(BP_IP_BREAING)))
    print("방위각 2 = " ,degrees_to_dms(convert_bearing(IP_EP_BREAING)))
    print("IA = " ,degrees_to_dms(IA_DEGREE))

    #완화곡선 계산함수호출
    try:
        IT, TotalL, ntp1, ntp2, tditc0, tditc1, Ls, Lc, CURVE_CENTER_XY,tarr,tarr2,cant = calculate_spiral(design_speed, direction,BP_IP_BREAING, IP_EP_BREAING, BP_XY, EP_XY, R, IP_XY, IA)

    except ValueError as e:
        print(e)
        print("이전 단계로 돌아갑니다.")
        show_error_message(e)
        
    PS_EP_distance = calculate_distance(ntp2[0], ntp2[1], EP_XY[0], EP_XY[1])

    SP_STA = IP_STA - IT
    PC_STA = SP_STA + Ls
    CP_STA = PC_STA + Lc
    PS_STA = CP_STA + Ls

    NEW_EP_STA = PS_STA + PS_EP_distance

    print("\n------------------\n")
    print("\n계산 결과\n")
    print("\n완화곡선 설치 전\n")
    print("IA : ",IA_DMS)
    print("R : ",R)
    print("TL : ",f"{TL:.2f}")
    print("CL : ",f"{CL:.2f}")
    print("IP 정측점 : ",format_distance(IP_STA))
    print("IP 역측점 : ",format_distance(BC + CL/2))
    print("BP : ",format_distance(BP_STA))
    print("BC : ",format_distance(BC))
    print("EC : ",format_distance(EC))
    print("EP : ",format_distance(EP_STA))

    print("\n------------------\n")
    print("\n완화곡선 설치 후\n")
    print("IA : ",IA_DMS)
    print("R : ",R)
    print("TL : ",f"{IT:.2f}")
    print("CL : ",f"{TotalL:.2f}")
    print("IP 정측점 : ",format_distance(IP_STA))
    print("IP 역측점 : ",format_distance(PC_STA + Lc/2))
    print("BP : ",format_distance(BP_STA))
    print("SP : ",format_distance(SP_STA))
    print("PC : ",format_distance(PC_STA))
    print("CP : ",format_distance(CP_STA))
    print("PS : ",format_distance(PS_STA))
    print("EP : ",format_distance(NEW_EP_STA))
    print("\n------------------\n")

    #openbve 곡선반경 계산
    FINAL_STA_LIST,Instantaneous_radius,final_cant = calculate_Instantaneous_radius(cant ,R,Ls,SP_STA,PC_STA,CP_STA,PS_STA)

    #구문 출력
    print("\n------------------\n")
    print("\n구문 출력\n")
    for i in range(len(FINAL_STA_LIST)):
        if direction == -1:
            print(f"{FINAL_STA_LIST[i]},.curve -{Instantaneous_radius[i]:.2f};{final_cant[i]:.0f}")
        else:
            print(f"{FINAL_STA_LIST[i]},.curve {Instantaneous_radius[i]:.2f};{final_cant[i]:.0f}")
    print("\n------------------\n")


    
    # 선 생성
    ax.plot(*zip(*[BP_XY, IP_XY, EP_XY]), linestyle='--', color='GREEN')
    ax.plot(*zip(*[BC_XY, IP_XY, EC_XY]), linestyle='-', color='BLACK')


    # 점 생성
    ax.scatter(*zip(*[BC_XY, EC_XY]), color='blue', marker='o')
    ax.scatter(*zip(*[BP_XY, IP_XY,EP_XY]), color='BLACK', marker='o')
    ax.scatter(*zip(*[ntp1, tditc0,tditc1,ntp2]), color='red', marker='o')


    # 시작점, 끝점, 중심점 좌표
    start_point = BC_XY
    end_point = EC_XY
    center_point = O_XY


    # 그래프에 호를 그림
    x_arc, y_arc = draw_arc(BC_XY, EC_XY, O_XY)
    ax.plot(x_arc, y_arc, label='기존 선형', color='BLUE')

    x_arc2, y_arc2 = draw_arc(tditc0, tditc1, CURVE_CENTER_XY)
    ax.plot(x_arc2, y_arc2, label='변경 선형', color='red')


    #3차포물선 그리기
    #SP~PC
    x_values = [point[0] for point in tarr]
    y_values = [point[1] for point in tarr]
    ax.plot(x_values, y_values, color='red')

    #CP~PS
    x_values2 = [point[0] for point in tarr2]
    y_values2 = [point[1] for point in tarr2]
    ax.plot(x_values2, y_values2, color='red')


    IA_POS = (R/2 * direction ,R/2)
    R_POS = (IA_POS[0], IA_POS[1]-30)
    TL_POS = (IA_POS[0], IA_POS[1]-60)
    CL_POS = (IA_POS[0], IA_POS[1]-90)
    X_POS = (IA_POS[0], IA_POS[1]-120)
    Y_POS = (IA_POS[0], IA_POS[1]-150)

    NEW_TL_POS = (IA_POS[0]+150, IA_POS[1]-60)
    NEW_CL_POS = (IA_POS[0]+150, IA_POS[1]-90)


    R_TEXT = f"R = {R}"
    TL_TEXT = f"TL = {TL:.2f}"
    CL_TEXT = f"CL = {CL:.2f}"
    X_TEXT = f"X = {IP_XY[1]:.3f}"
    Y_TEXT = f"Y = {IP_XY[0]:.3f}"

    BC_STA = f"BC = {format_distance(BC)}"
    EC_STA = f"EC = {format_distance(EC)}"

    #기존
    ax.text(*BP_XY, 'BP = '+ format_distance(BP_STA), fontsize=12, ha='left',color='BLACK')
    ax.text(*IP_XY, 'IP', fontsize=12, ha='right',color='BLACK')
    ax.text(*EP_XY, 'EP = '+ format_distance(EP_STA), fontsize=12, ha='left',color='BLUE')



    # 폰트 설정
    custom_font = ("굴림체", 12)  # 폰트 및 크기 지정
    
    # 텍스트 레이블 생성 윈도우창
    
    text_label = tk.Label(root, text=IA_DMS, bg=root.cget('bg'), fg="black",font = custom_font)
    text_label.place(x=650, y=450)  # 텍스트를 (100, 100) 좌표에 배치
    text_label = tk.Label(root, text=R_TEXT, bg=root.cget('bg'), fg="black",font = custom_font)
    text_label.place(x=650, y=470)  # 텍스트를 (100, 100) 좌표에 배치 20간격
    text_label = tk.Label(root, text=TL_TEXT, bg=root.cget('bg'), fg="black",font = custom_font)
    text_label.place(x=650, y=490)
    text_label = tk.Label(root, text=CL_TEXT, bg=root.cget('bg'), fg="black",font = custom_font)
    text_label.place(x=650, y=510)
    text_label = tk.Label(root, text=X_TEXT, bg=root.cget('bg'), fg="black",font = custom_font)
    text_label.place(x=650, y=530)
    text_label = tk.Label(root, text=Y_TEXT, bg=root.cget('bg'), fg="black",font = custom_font)
    text_label.place(x=650, y=550)

    
    ax.text(*BC_XY, BC_STA, fontsize=12, ha='left',color='BLUE')
    ax.text(*EC_XY, EC_STA, fontsize=12, ha='left' ,color='BLUE')

    #완화곡선
    ax.text(*EP_XY, 'EP = '+ format_distance(NEW_EP_STA), fontsize=12, ha='right',color='RED')

    ax.text(*ntp1, "SP = "+format_distance(SP_STA), fontsize=12, ha='left',color='RED')
    ax.text(*ntp2, "PS = "+format_distance(PS_STA), fontsize=12, ha='left',color='RED')
    ax.text(*tditc0, "PC = "+format_distance(PC_STA), fontsize=12, ha='left',color='RED')
    ax.text(*tditc1, "CP = "+format_distance(CP_STA), fontsize=12, ha='left',color='RED')
    
    text_label = tk.Label(root, text=f"({IT:.2f})", bg=root.cget('bg'), fg="RED",font = custom_font)
    text_label.place(x=750, y=490)

    text_label = tk.Label(root, text=f"({TotalL:.2f})", bg=root.cget('bg'), fg="RED",font = custom_font)
    text_label.place(x=750, y=510)


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
    design_speed_var.set(150)
    update_plot()


def reset_draw():
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

def toggle_reverse_curve():
    if direction_var.get() == 1:
        direction = -1
    else:
        direction = 1
    canvas.draw()
    return direction
def show_error_message(error_message):
    # 새로운 창 생성
    error_window = tk.Toplevel(root)
    error_window.title("에러 발생")
    
    # 에러 메시지 표시 레이블
    error_label = tk.Label(error_window, text=error_message, bg="white", fg="red")
    error_label.pack(padx=20, pady=10)
    

root = tk.Tk()
root.title("OPENBVE 완화곡선 설치")

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

'''
tk.Label(root, text="기존 곡선반경:").grid(row=2, column=0, sticky="e")
radius_var = tk.DoubleVar(value=600)
radius_slider = tk.Scale(root, from_=0, to=9999, orient=tk.HORIZONTAL, variable=radius_var, command=update_plot, resolution=10)
radius_slider.grid(row=2, column=1)

# 직접 입력할 수 있는 입력 상자
radius_entry = tk.Entry(root, textvariable=radius_var)
radius_entry.grid(row=2, column=2)
radius_entry.bind('<KeyRelease>', update_plot)
'''
# 기존 곡선반경 스핀 버튼
tk.Label(root, text="기존 곡선반경:").grid(row=2, column=0, sticky="e")
radius_var = tk.DoubleVar(value=600)
radius_spinner = tk.Spinbox(root, from_=0, to=50000, textvariable=radius_var, increment=100)
radius_spinner.grid(row=2, column=1)
radius_spinner.bind('<KeyRelease>', update_plot)
'''
tk.Label(root, text="설계속도:").grid(row=3, column=0, sticky="e")
design_speed_var = tk.DoubleVar(value=150)
design_speed_slider = tk.Scale(root, from_=10, to=300, orient=tk.HORIZONTAL, variable=design_speed_var, command=update_plot, resolution=10)
design_speed_slider.grid(row=3, column=1)
'''

# 설계속도 스핀 버튼
tk.Label(root, text="설계속도:").grid(row=3, column=0, sticky="e")
design_speed_var = tk.DoubleVar(value=150)
design_speed_spinner = tk.Spinbox(root, from_=10, to=300, textvariable=design_speed_var, increment=10)
design_speed_spinner.grid(row=3, column=1)
design_speed_spinner.bind('<KeyRelease>', update_plot)

# 버튼 생성
reset_button = tk.Button(root, text="초기화", command=reset_values)
reset_button.grid(row=3, column=0, pady=10)

# 종료 버튼 생성
exit_button = tk.Button(root, text="종료", command=exit_program)
exit_button.grid(row=2, column=0, pady=10)

# 버튼 생성
redraw_button = tk.Button(root, text="다시그리기", command=reset_draw)
redraw_button.grid(row=1, column=0, pady=10)

# Create a variable to store the checkbox state
aspect_var = tk.IntVar(value=0)

# Create the checkbox
aspect_checkbox = tk.Checkbutton(root, text="비율 동일하게", variable=aspect_var, command=toggle_aspect_ratio)
aspect_checkbox.grid(row=0, column=3, columnspan=2, pady=10)

# Create a variable to store the checkbox state
direction_var = tk.IntVar(value=0)

# Create the checkbox
direction_checkbox = tk.Checkbutton(root, text="좌향곡선", variable=direction_var, command=toggle_reverse_curve)
direction_checkbox.grid(row=1, column=3, columnspan=2, pady=10)

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
root.geometry("900x800")

root.mainloop()
