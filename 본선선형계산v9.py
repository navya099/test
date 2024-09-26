from tkinter import filedialog
import csv
from shapely.geometry import LineString
import math
import pandas as pd
from openpyxl import Workbook, load_workbook
import time

def save_with_retry(workbook, filename, max_retries=100, delay=1):
    # Try saving the file, retrying if there's a PermissionError
    for attempt in range(max_retries):
        try:
            workbook.save(filename)
            print(f"File saved successfully: {filename}")
            break
        except PermissionError:
            print(f"Attempt {attempt + 1}: Permission denied while saving {filename}. Retrying in {delay} seconds...")
            time.sleep(delay)
    else:
        print(f"Failed to save the file after {max_retries} attempts.")
        
def pasing_ip(lines):
    alignment = []
    for line in lines:
        try:
            IP_X_Coordinate = float(line[1])
            IP_Y_Coordinate = float(line[0])
            Radius = float(line[2])
            
        except IndexError:
            Radius = 0
        
        alignment.append([IP_X_Coordinate, IP_Y_Coordinate, Radius])
        
    return alignment

def create_Linestring(alignment):
    coords = [(point[0], point[1]) for point in alignment]
    return LineString(coords)

def read_file():
    file_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("txt files", "*.txt"), ("All files", "*.*")])
    print('현재파일:', file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            lines = list(reader)
    except UnicodeDecodeError:
        print('현재파일은 utf-8인코딩이 아닙니다. euc-kr로 시도합니다.')
        try:
            with open(file_path, 'r', encoding='euc-kr') as file:
                reader = csv.reader(file)
                lines = list(reader)
        except UnicodeDecodeError:
            print('현재파일은 euc-kr인코딩이 아닙니다. 파일을 읽을 수 없습니다.')
            return []
    return lines

def calculate_angles_and_plot(line_string):
    angles = []
    for i in range(1, len(line_string.coords) - 1):
        prev_vector = (line_string.coords[i][0] - line_string.coords[i - 1][0],
                       line_string.coords[i][1] - line_string.coords[i - 1][1])
        current_vector = (line_string.coords[i + 1][0] - line_string.coords[i][0],
                          line_string.coords[i + 1][1] - line_string.coords[i][1])
        angle_diff = calculate_inner_angle(prev_vector, current_vector)
        angles.append(angle_diff)
    return angles

def calculate_inner_angle(v1, v2):
    angle1 = math.atan2(v1[1], v1[0])
    angle2 = math.atan2(v2[1], v2[0])
    angle_diff = abs(angle2 - angle1)
    if angle_diff > math.pi:
        angle_diff = 2 * math.pi - angle_diff
    return math.degrees(angle_diff)

def calculate_bearing(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.degrees(math.atan2(dy, dx))
    return bearing

def calculate_bearingN(x1, y1, x2, y2):
    # 방위각 계산함수
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.degrees(math.atan2(dy, dx))
    if bearing <=0:
        bearing += 360
    return bearing

def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def calculate_destination_coordinates(x1, y1, bearing, distance):
    angle = math.radians(bearing)
    x2 = x1 + distance * math.cos(angle)
    y2 = y1 + distance * math.sin(angle)
    return x2, y2

def find_direction(d10, v10, v11):
    if d10 == 0:
        return 0
    elif math.sin(math.radians(v11 - v10)) >= 0:
        return 1
    else:
        return -1
    
def calculate_V(Cm, Cd, R, maxV):
    V = int(math.sqrt((Cm +  Cd) * R / 11.8))  # 정수로 변환
    return min(V, maxV)  # V가 maxV를 초과하지 않도록 제한

#최대 설정캔트와 최대 부족캔트
def get_cant_limits(V, track_type):
    """
    설계속도(V)와 도상 유형(track_type)에 따른 최대 설정캔트와 최대 부족캔트를 반환하는 함수.
    
    track_type: '자갈도상' 또는 '콘크리트도상'
    """
    if track_type == "자갈도상":
        if 350 < V <= 400:
            return 180, 130#이 설계속도에서는 콘크리트도상 적용
        elif 250 < V <= 350:
            return 160, 80
        elif V <= 250:
            return 160, 100
    elif track_type == "콘크리트도상":
        if 350 < V <= 400:
            return 180, 130
        elif 250 < V <= 350:
            return 180, 130
        elif V <= 250:
            return 180, 130
    else:
        return "Invalid track type"

#M,Z,V계산
def cal_parameter(radius_list, maxV=250, track_type='자갈도상'):
    parameters = []
    for i in range(len(radius_list)):
        try:
            
            
            Cm, Cd = get_cant_limits(maxV, track_type)#최대 설정캔트와 최대 부족캔트
            
            R = radius_list[i]
            
            
            V = int(calculate_V(Cm, Cd, R, maxV))
            
            # 10의 배수로 조정
            V = round(V / 10) * 10
            
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

            M = int(m_values.get(V, 7.31 * V))
            # 50의 배수로 조정
            M = round(M / 50) * 50
            
            Z = 11.8 * V ** 2 / R
            
            if Z >= Cm:
                Z = Cm

            # 10의 배수로 조정
            Z = round(Z / 10) * 10
            
            parameters.append([M,Z,V])
        except ValueError:
            print("잘못된 입력입니다. 숫자를 입력해주세요.")
            
    return parameters

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

    
    return f"{deg}도  {minutes}분  {seconds:.2f}초"

#SP>PC 방위각
def calculate_SP_PC_bearing(W13, V10, X10):
    if W13 < 0:
        result = V10 - X10
        if result < 0:
            result += 360
    else:
        result = V10 + X10
        if result > 360:
            result -= 360

    return result

#CP좌표계산
def calculate_CP_XY(K21, N21, W13, W18, P10, V11):
    part1 = W13 * math.cos(math.radians(W18 + 90))  # (W18 + 90) * PI() / 180
    part2 = W13 * math.cos(math.radians(W18 - 90 + (180 * P10) / (math.pi * W13)))  # (W18 - 90 + (180 * P10 / PI() / W13)) * PI() / 180
    part3 = W13 * math.sin(math.radians(W18 + 90))
    part4 = W13 * math.sin(math.radians(W18 - 90 + (180 * P10) / (math.pi * W13)))  # (W18 - 90 + (180 * P10 / PI() / W13)) * PI() / 180
    
    result1 = K21 + part1 + part2
    result2 = N21 + part3 + part4
    
    return (result1, result2)


#O>PC방위각
def calculate_O_PC_bearing(V10, X10, W13):
    '''args
    W13 = W13
    V10 = 방위각1
    X10 = THITA
    '''
    X10 = math.degrees(X10)
    
    if W13 > 0:
        if V10 + X10 - 90 < 0:
            return V10 + X10 - 90 + 360
        else:
            return V10 + X10 - 90
    else:
        if V10 - X10 + 90 > 360:
            return V10 - X10 + 90 - 360
        else:
            return V10 - X10 + 90

#PC점의 접선각
def calculate_theta_pc(m, z, Rc):
    """Calculate the PC point's tangent angle in radians."""
    x1 = m * (z * 0.001) #X1
    theta_pc = math.atan(x1 / (2 * Rc))
    return theta_pc

#3차포물선 제원계산
def calculate_cubic_parabola_parameter(m, z, direction, theta_pc, Rc, IA_rad):
    """Calculate various lengths used in the spiral calculation."""
    x1 = m * (z * 0.001) #X1
    x2 = x1 - (Rc * math.sin(theta_pc))#x2
    W13 = Rc * direction#-R
    L = x1 * (1 + (math.tan(theta_pc) ** 2) / 10)#완화곡선 길이
    Y = (x1 ** 2) / (6 * Rc)#Y1
    W15  = (x1 ** 2) / (6 * W13)#W-Y
    F = Y - Rc * (1 - math.cos(theta_pc))#이정량 F
    S = 1 / math.cos(IA_rad / 2) * F #S
    K = F * math.tan(IA_rad / 2) #수평좌표차K
    W = (Rc + F) * math.tan(IA_rad / 2)#W
    TL = x2 + W #TL
    Lc = Rc * (IA_rad - 2 * theta_pc) #원곡선 길이
    CL = Lc + 2 * L #전체곡선길이
    SL = Rc * (1 / (math.cos(IA_rad / 2)) - 1) + S
    RIA = IA_rad - (2 * theta_pc)#원곡선교각
    C = math.atan(Y / x1)#C
    XB = math.pi/2 - theta_pc#XB
    B = math.pi/2 - C - XB
    parameter = [x1, x2, W13, L, Y, W15, F, S, K, W, TL, Lc, CL, SL, RIA , C, B]
    
    return parameter

def calculate_simplecurve_parameter(direction, Rc, IA_rad):
    TL = Rc * math.tan(IA_rad/2)
    CL = Rc * IA_rad
    SL = Rc * (1 / (math.cos(IA_rad / 2)) - 1)
    S = Rc * (1 - math.cos(IA_rad / 2))
    W13 = Rc * direction
    parameter = [TL,CL,SL,S, W13]
    return parameter

#완화곡선 시종점 좌표계산함수
def calculate_spiral_coordinates(BP_XY, IP_XY, EP_XY, h1, h2, TL, x1, Y, SP_PC_bearing, Rc, Lc, W13):
    """Calculate the coordinates of SP, PC, CP, and PS."""
    SP_XY = (
        math.cos(math.radians(h1 + 180)) * TL + IP_XY[0],
        math.sin(math.radians(h1 + 180)) * TL + IP_XY[1]
    )
    PC_XY = (
        SP_XY[0] + x1 * math.cos(math.radians(h1)) + Y * math.cos(math.radians(h1 + 90)),
        SP_XY[1] + x1 * math.sin(math.radians(h1)) + Y * math.sin(math.radians(h1 + 90))
    )
    CP_XY = calculate_CP_XY(PC_XY[0], PC_XY[1], W13, SP_PC_bearing, Lc, h2)
    PS_XY = (
        math.cos(math.radians(h2)) * TL + IP_XY[0],
        math.sin(math.radians(h2)) * TL + IP_XY[1]
    )
    return SP_XY, PC_XY, CP_XY, PS_XY

def dictionary_cubicparabola(v):
    '''
    완화곡선을 삽입하지 않는 최소곡선반경
    '''
    not_spiral_min_radius_dic = {
        250: 24000,
        200: 12000,
        150: 5000,
        120: 2500,
        70: 600
    }

    cdlim_dic = {
        400: 20,
        350: 25,
        300: 27,
        250: 32,
        200: 40,
        150: 57,
        120: 69,
        100: 83,
        70: 100
    }

    # cdlim_dic에서 이미 존재하는 값일 경우 그대로 반환
    if v in cdlim_dic:
        cdlim = cdlim_dic[v]
    else:
        # 값이 사전에 없을 경우 선형 보간 수행
        sorted_keys = sorted(cdlim_dic.keys())

        # 입력값이 범위 밖에 있을 경우 예외 처리
        if v < sorted_keys[0] or v > sorted_keys[-1]:
            raise ValueError(f"입력 속도 {v}는 지원되는 범위 밖에 있습니다. {sorted_keys[0]}에서 {sorted_keys[-1]} 사이의 값을 입력하세요.")

        # 선형 보간을 위한 인접한 두 값 찾기
        for i in range(len(sorted_keys) - 1):
            if sorted_keys[i] <= v <= sorted_keys[i + 1]:
                # 두 지점 사이의 보간
                x1, y1 = sorted_keys[i], cdlim_dic[sorted_keys[i]]
                x2, y2 = sorted_keys[i + 1], cdlim_dic[sorted_keys[i + 1]]
                
                # 선형 보간 공식 사용
                cdlim = y1 + (v - x1) * (y2 - y1) / (x2 - x1)
                break

    # not_spiral_min_radius_dic에서 값 찾기
    if v in not_spiral_min_radius_dic:
        not_spiral_min_radius = not_spiral_min_radius_dic[v]
    else:
        # 해당 값이 없으면 공식으로 계산
        not_spiral_min_radius = 11.8 * (v**2 / cdlim)

    return not_spiral_min_radius


#메인계산함수
def calculate_curve(linestring, Radius_list, angles, parameters, unit=20, start_STA=0):

    final_result = []
    
    O_XY_list = []
    cubic_parabola_XY_list = []
    cubic_parabola_STA_list = []

    simplecurve_XY_list = []
    simplecurve_STA_list = []
    
    TL_LIST = []
    IP_STA_list = []
    
    direction_list = []
    prebearing_list = []
    nextbearing_list = []
    
    BP_STA = start_STA
    BP_STA_LIST = [0]

    station_coordlist = []

    END_STA_list = []
    END_XY_list =[]

    alignment_report_variable_list = []
    
    for i in range(len(linestring.coords)-2):
        IA_rad = math.radians(angles[i])
        IA_DEGREE = angles[i]
        
        #토목좌표
        BP_XY = (linestring.coords[i][0], linestring.coords[i][1])
        IP_XY = (linestring.coords[i + 1][0], linestring.coords[i + 1][1])
        EP_XY = (linestring.coords[i + 2][0], linestring.coords[i + 2][1])

        h1 = calculate_bearingN(BP_XY[0], BP_XY[1], IP_XY[0], IP_XY[1])#방위각1(도)
        h2 = calculate_bearingN(IP_XY[0], IP_XY[1], EP_XY[0], EP_XY[1])#방위각2(도)

        IP_distnace1 = calculate_distance(BP_XY[0], BP_XY[1], IP_XY[0], IP_XY[1]) #ip연장1
        IP_distnace2 = calculate_distance(IP_XY[0], IP_XY[1], EP_XY[0], EP_XY[1]) #연장2

        
        
        Rc = Radius_list[i]
        m, z, v = parameters[i]
        
        not_spiral_min_radius = dictionary_cubicparabola(v)#완화곡선을 삽입하지 않는 최소곡선반경

        if Rc >= not_spiral_min_radius:
            curvetype = 'simplecurve'#단곡선
        else:
            curvetype = 'cubic'#3차포물선
        
        direction = find_direction(Rc, h1, h2)

        if direction == 1:
            curvedirection = 'RIGHT CURVE'
        else:
            curvedirection = 'LEFT CURVE'
        
        if curvetype == 'simplecurve':#단곡선
            theta_pc = 0
            #O>PC 방위각(도)
            
            simplecurve_parameter = calculate_simplecurve_parameter(direction, Rc, IA_rad)
            TL, CL, SL, S, W13 = simplecurve_parameter# 파라매터

            O_PC_bearing = calculate_O_PC_bearing(h1, theta_pc, W13)
            SP_PC_bearing = h1#SP>PC방위각(도)
            simplecurve_coord = calculate_simplecurve_coordinates(h1, h2, TL, IP_XY)#BC,EC좌표반환함수
            BC_XY , EC_XY = simplecurve_coord#BC,EC좌표
            
            CURVE_CENTER = (math.cos(math.radians(O_PC_bearing + 180)) * Rc + BC_XY[0],
                            math.sin(math.radians(O_PC_bearing + 180)) * Rc + BC_XY[1])#CURVE CENTER

            simplecurve_XY_list.append([BC_XY, EC_XY])

            END_XY_list.append(EC_XY)
            
            if i == 0:
                simplecurve_STA_list.append([0, 0])#인덱스 오류 방지로 0 할당
                # 첫 번째 값을 덮어쓰기
                IP_STA = BP_STA + IP_distnace1
                BC_STA = IP_STA - TL
                EC_STA = BC_STA + CL

                simplecurve_STA_list[0] = [BC_STA, EC_STA]  # 첫 번째 값 덮어쓰기

                END_STA_list.append(EC_STA)
            else:
                BP_STA = END_STA_list[i-1]  # 이전 PS_STA 값
                IP_STA = BP_STA + IP_distnace1 - TL_LIST[i - 1]

                BC_STA = IP_STA - TL
                EC_STA = BC_STA + CL

                simplecurve_STA_list.append([BC_STA, EC_STA])
                
                END_STA_list.append(EC_STA)
                if i == len(linestring.coords) - 3:#마지막IP
                    EC_EP_distance = calculate_distance(EC_XY[0], EC_XY[1], EP_XY[0], EP_XY[1]) #EC와 EP거리
                    EP_STA = EC_STA + EC_EP_distance
        else:#3차포물선
            theta_pc = calculate_theta_pc(m, z, Rc)#pc점의 접선각 라디안
            
            
            cubic_parameter = calculate_cubic_parabola_parameter(m, z, direction, theta_pc, Rc, IA_rad)#파라매터
        
            x1, x2, W13, L, Y, W15, F, S, K, W, TL, Lc, CL, SL, RIA, C, B = cubic_parameter

            O_PC_bearing = calculate_O_PC_bearing(h1, theta_pc, W13)#O>PC 방위각(도)
            
            SP_PC_bearing = calculate_SP_PC_bearing(W13, h1, math.degrees(theta_pc))#SP>PC방위각(도)

            SP_XY, PC_XY, CP_XY, PS_XY = calculate_spiral_coordinates(BP_XY, IP_XY, EP_XY, h1, h2, TL, x1, W15, SP_PC_bearing, Rc, Lc, W13)

            CURVE_CENTER = (math.cos(math.radians(O_PC_bearing + 180)) * Rc + PC_XY[0],
                            math.sin(math.radians(O_PC_bearing + 180)) * Rc + PC_XY[1])#CURVE CENTER
            
            cubic_parabola_XY_list.append([SP_XY,PC_XY,CP_XY,PS_XY])

            END_XY_list.append(PS_XY)
            
            if i == 0:
                cubic_parabola_STA_list.append([0, 0, 0, 0])#인덱스 오류 방지로 0 할당
                # 첫 번째 값을 덮어쓰기
                IP_STA = BP_STA + IP_distnace1
                SP_STA = IP_STA - TL
                PC_STA = SP_STA + L
                CP_STA = PC_STA + Lc
                PS_STA = CP_STA + L

                cubic_parabola_STA_list[0] = [SP_STA, PC_STA, CP_STA, PS_STA]  # 첫 번째 값 덮어쓰기

                END_STA_list.append(PS_STA)
                
            else:
                # 두 번째 이상의 경우 새로운 값을 append
                BP_STA = END_STA_list[i-1]  # 이전 PS_STA 값
                IP_STA = BP_STA + IP_distnace1 - TL_LIST[i - 1]

                SP_STA = IP_STA - TL
                PC_STA = SP_STA + L
                CP_STA = PC_STA + Lc
                PS_STA = CP_STA + L

                cubic_parabola_STA_list.append([SP_STA, PC_STA, CP_STA, PS_STA])
                
                END_STA_list.append(PS_STA)

                if i == len(linestring.coords) - 3:#마지막IP
                    EC_EP_distance = calculate_distance(PS_XY[0], PS_XY[1], EP_XY[0], EP_XY[1]) #EC와 EP거리
                    EP_STA = PS_STA + EC_EP_distance

        TL_LIST.append(TL)
        
        
            
        
            
        ###좌표 계산로직###
        # unit 간격으로 PS_STA까지 스테이션 리스트 생성
        
        #리스트 초기화
        station_coordlist = []
        
        # Ensure BP_STA and PS_STA are integers

        if curvetype == 'simplecurve':#단곡선
            BP_STA_int = int(round(BP_STA))
            EC_STA_int = int(round(EC_STA))


            # unit 간격으로 PS_STA까지 스테이션 리스트 생성
            if i == len(linestring.coords) - 3:  # 마지막IP
                EP_STA_int = int(round(EP_STA))
                station_list = generate_integers(BP_STA_int, EP_STA_int, unit)
            else:
                station_list = generate_integers(BP_STA_int, EC_STA_int, unit)

            #BC와 EC측점 추가
            station_list.extend([BP_STA, BC_STA, EC_STA])

            #리스트 정렬
            station_list.sort()

            # 스테이션 리스트에 있는 각 sta에 대해 좌표 계산
            for j, sta in enumerate(station_list):
                if j ==0:
                    lable = 'BP'
                else:
                    if i == len(linestring.coords) - 3:  # 마지막IP
                        lable = get_station_label(curvetype, sta, BC_STA, BC_STA, EC_STA, EC_STA, EP_STA)  # 제원문자
                    else:
                        lable = get_station_label(curvetype, sta, BC_STA, BC_STA, EC_STA, EC_STA, EC_STA)#제원문자
                #print(lable)
                if j ==0:
                    StationOffset = 0
                else:
                    StationOffset = calculate_station_offset(sta, BC_STA, BC_STA, EC_STA, EC_STA, BP_STA)#측거
                #print(StationOffset)
                shiftx =  0
                #print(shiftx)
                shifty =  0
                #print(shifty)
                if i ==0:
                    PBP_XY = BP_XY
                else:
                    PBP_XY = END_XY_list[i-1]
                coord = calculate_coordinates(sta,
                                              BC_STA, BC_STA, EC_STA, EC_STA,
                                              h1, h2, SP_PC_bearing,
                                              StationOffset, W13,
                                              shiftx, shifty,
                                              PBP_XY[0], PBP_XY[1],
                                              BC_XY[0], BC_XY[1],
                                              CURVE_CENTER[0], CURVE_CENTER[1],
                                              EC_XY[0], EC_XY[1])
                # 각 sta에 대한 좌표를 추가
                # Create a list for the current station's data
                station_coordlist.append([lable, sta, StationOffset, coord, shiftx, shifty])
        else:#3차포물선
            BP_STA_int = int(round(BP_STA))
            PS_STA_int = int(round(PS_STA))


            # unit 간격으로 PS_STA까지 스테이션 리스트 생성
            if i == len(linestring.coords) - 3:  # 마지막IP
                EP_STA_int = int(round(EP_STA))
                station_list = generate_integers(BP_STA_int, EP_STA_int, unit)
            else:

                station_list = generate_integers(BP_STA_int, PS_STA_int, unit)

            #BP, SP,PC,CP ,PS점 추가
            station_list.extend([BP_STA, SP_STA, PC_STA, CP_STA, PS_STA])

            if i == len(linestring.coords) - 3:  # 마지막IP
                station_list.append(EP_STA)

            #리스트 정렬
            station_list.sort()

            # 스테이션 리스트에 있는 각 sta에 대해 좌표 계산
            for j, sta in enumerate(station_list):
                if j ==0:
                    lable = 'B  P'
                else:
                    if i == len(linestring.coords) - 3:  # 마지막IP
                        lable = get_station_label(curvetype, sta, SP_STA, PC_STA, CP_STA, PS_STA, EP_STA)  # 제원문자
                    else:
                        lable = get_station_label(curvetype, sta, SP_STA, PC_STA, CP_STA, PS_STA, PS_STA)#제원문자
                #print(lable)
                if j ==0:
                    StationOffset = 0
                else:
                    StationOffset = calculate_station_offset(sta, SP_STA, PC_STA, CP_STA, PS_STA, BP_STA)#측거
                #print(StationOffset)
                shiftx =  cal_spiral_shiftx(sta, SP_STA, PC_STA, CP_STA, PS_STA, StationOffset, W13, L)
                #print(shiftx)
                shifty =  cal_spiral_shifty(sta, SP_STA, PC_STA, CP_STA, PS_STA, shiftx, W13, x1)
                #print(shifty)
                if i ==0:
                    PBP_XY = BP_XY
                else:
                    PBP_XY = END_XY_list[i-1]
                coord = calculate_coordinates(sta,
                                              SP_STA, PC_STA, CP_STA, PS_STA,
                                              h1, h2, SP_PC_bearing,
                                              StationOffset, W13,
                                              shiftx, shifty,
                                              PBP_XY[0], PBP_XY[1],
                                              SP_XY[0], SP_XY[1],
                                              CURVE_CENTER[0], CURVE_CENTER[1],
                                              PS_XY[0], PS_XY[1])

                # 각 sta에 대한 좌표를 추가
                # Create a list for the current station's data
                station_coordlist.append([lable, sta, StationOffset, coord, shiftx, shifty])
        final_result.append([station_coordlist])

        ######선형계산서 리스트 저장#######
        if curvetype == 'simplecurve':#단곡선
            
            alignment_report_variable_list.append(
                [
                    i+1,
                    IP_XY,
                    curvetype,
                    curvedirection,
                    h1, h2,
                    IA_DEGREE,
                    CURVE_CENTER,
                    Rc,
                    IP_distnace1, IP_distnace2,
                    m, z, v,
                    simplecurve_parameter,
                    O_PC_bearing,
                    SP_PC_bearing,
                    theta_pc,
                    IP_STA,
                    BC_STA, EC_STA,  # Corrected typo here
                    BC_XY, EC_XY
                ]
            )
        else:#3차포물선
            alignment_report_variable_list.append(
                [
                    i+1,
                    IP_XY,
                    curvetype,
                    curvedirection,
                    h1, h2,
                    IA_DEGREE,
                    CURVE_CENTER,
                    Rc,
                    IP_distnace1, IP_distnace2,
                    m, z, v,
                    cubic_parameter,
                    O_PC_bearing,
                    SP_PC_bearing,
                    theta_pc,
                    IP_STA,
                    SP_STA, PC_STA, CP_STA, PS_STA,# Corrected typo here
                    SP_XY, PC_XY ,CP_XY, PS_XY
                ]
            )
            
                                            
    return final_result, alignment_report_variable_list

def calculate_simplecurve_coordinates(V10, V11, D12, IP):
    '''
    Args:
    v10 = 방위각1
    V11 = 방위각2
    d12 = TL
    F5 =IPX
    L5 = IPY
    
    '''
    F5 = IP[0]
    L5 = IP[1]
    
    BC_XY = (math.cos(math.radians(V10+180))*(D12) + F5,
             math.sin(math.radians(V10+180))*(D12) + L5)
    EC_XY = (math.cos(math.radians(V11+180))*(D12) + F5,
             math.sin(math.radians(V10+180))*(D12) + L5)

    coords = [BC_XY, EC_XY]
    return coords
#이정량 x,y                
def cal_spiral_shiftx(B27, H20, H21, H22, H23, D27, W13, D13, epsilon=1e-9):
    '''
    Args:
    B27 = 측점
    H20, H21, H22, H23 = 특정 스테이션 값
    D27 = 측거
    W13 = -곡선반경
    D13 = 캔트
    epsilon = tolerance for floating-point comparison

    Returns:
    A calculated value based on the conditions in the Excel formula.
    '''

    if H20 >= B27:
        return 0
    elif H21 > B27:
        return D27 - (D27 ** 5 / (40 * W13 ** 2 * D13 ** 2))
    elif H22 >= B27:
        return 0
    elif H23 >= B27:
        return D27 - (D27 ** 5 / (40 * W13 ** 2 * D13 ** 2))
    else:
        return 0

#이정량Y
def cal_spiral_shifty(B27, H20, H21, H22, H23, V27, W13, P11, epsilon=1e-9):
    '''
    Args:
    B27 = 측점
    H20, H21, H22, H23 = 특정 스테이션 값
    V27 = 이정량x
    W13 = -곡선반경
    P11 = x1
    epsilon = tolerance for floating-point comparison

    Returns:
    A calculated value based on the conditions in the Excel formula.
    '''

    if H20 >= B27:
        return 0
    elif H21 > B27:
        return V27 ** 3 / (6 * W13 * P11)
    elif H22 >= B27:
        return 0
    elif H23 >= B27:
        return V27 ** 3 / (6 * W13 * P11)
    else:
        return 0


def get_station_label(curve_type, station, SP_STA, PC_STA, CP_STA, PS_STA, EP_STA, epsilon=1e-9):
    """
    Args:
    curve_type (str): 곡선타입 ('simplecurve', 'cubic')
    station (float): 측점
    SP_STA, PC_STA, CP_STA, PS_STA, EP_STA (float): 각각 SP, PC, CP, PS, EP 좌표
    epsilon (float): 부동소수점 비교를 위한 허용 오차

    Returns:
    str: 해당 측점의 레이블 ('BC', 'SP', 'PC', 'CP', 'PS', 'EC', 'EP') or 빈 문자열 ("")
    """
    if abs(station - SP_STA) < epsilon:
        return 'BC' if curve_type == 'simplecurve' else 'SP'
    elif abs(station - PC_STA) < epsilon:
        return 'BC' if curve_type == 'simplecurve' else 'PC'
    elif abs(station - CP_STA) < epsilon:
        return 'EC' if curve_type == 'simplecurve' else 'CP'
    elif abs(station - PS_STA) < epsilon:
        return 'EC' if curve_type == 'simplecurve' else 'PS'
    elif abs(station - EP_STA) < epsilon:
        return "EP"
    else:
        return ""


#측거
def calculate_station_offset(B28, H20, H21, H22, H23, X13, epsilon=1e-9):
    '''
    Args:
    B28 = 측점 (Station point)
    H20, H21, H22, H23 = 스테이션 값 (Station values)
    X13 = BP STA (Base point)
    epsilon = tolerance for floating-point comparison
    
    Returns:
    A calculated offset value.
    '''
    
    if abs(B28 - H20) < epsilon or abs(B28 - H21) < epsilon or abs(B28 - H22) < epsilon or abs(B28 - H23) < epsilon:
        return 0

    if B28 <= H20:
        return B28 - X13
    elif B28 < H21:
        return B28 - H20
    elif B28 <= H22:
        return B28 - H21
    elif B28 <= H23:
        return H23 - B28
    else:
        return B28 - H23


#선형 좌표계산함수
def calculate_coordinates(B27, H20, H21, H22, H23, V10, V11, W18, D27, W13, V27, W27, X14, X15, K20, N20, J9, N9, K23, N23):
    '''
    args
    B27 = 측점
    H20, H21, H22, H23 = 완화곡선 측점
    V10, V11 = 방위각 1,2
    W18 = sp, pc 방위각
    D27 = 측거
    W13 = -곡선반경
    
    V27 = 이정량 x
    W27 = 이정량 y
    X14, X15 = BP X, BP Y
    K20, K23 = SP[X], PS[X]
    J9, N9 = CENTER X, CENTER Y
    N20, N23 = SP[Y], PS[Y]
    '''
    if B27 == "":
        return (0,0)

    # X coordinate calculation
    if B27 <= H20:
        X_result = math.cos(math.radians(V10)) * D27 + X14
    elif B27 < H21:
        X_result = (math.cos(math.radians(V10 + 90)) * W27 +
                    math.cos(math.radians(V10)) * V27 +
                    K20)
    elif B27 <= H22:
        X_result = (math.cos(math.radians(W18 - 90 + (180 * D27) / math.pi / W13)) * W13 +
                    J9)
    elif B27 <= H23:
        X_result = (math.cos(math.radians(V11 + 90)) * W27 +
                    math.cos(math.radians(V11 + 180)) * V27 +
                    K23)
    else:
        X_result = (math.cos(math.radians(V11)) * D27 + K23)

    # Y coordinate calculation
    if B27 <= H20:
        Y_result = math.sin(math.radians(V10)) * D27 + X15
    elif B27 < H21:
        Y_result = (math.sin(math.radians(V10 + 90)) * W27 +
                    math.sin(math.radians(V10)) * V27 +
                    N20)
    elif B27 <= H22:
        Y_result = (math.sin(math.radians(W18 - 90 + (180 * D27) / math.pi / W13)) * W13 +
                    N9)
    elif B27 <= H23:
        Y_result = (math.sin(math.radians(V11 + 90)) * W27 +
                    math.sin(math.radians(V11 + 180)) * V27 +
                    N23)
    else:
        Y_result = math.sin(math.radians(V11)) * D27 + N23

    return (X_result, Y_result)

def generate_integers(start, end, inc):
    # Round the start to the nearest increment
    start_rounded = (start + inc - 1) // inc * inc
    # Round the end to the nearest increment
    end_rounded = end // inc * inc
    
    return list(range(start_rounded, end_rounded + inc, inc))

    
def calculate_distance(x1, y1, x2, y2):
    # 거리계산함수
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    distance_x = abs(x2 - x1)
    distance_y = abs(y2 - y1)
    return distance



def write_data(data):
    """
    Writes the given data to a CSV file in the specified format:
    type, sta, stationoffset, coordx, coordy, shiftx, shifty

    Args:
    - data (list of lists): The data to be written to the file. Each inner list represents a station's data.
    """
    file_path = 'C:/temp/data.csv'
    
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write the header
            writer.writerow(['type', 'sta', 'stationoffset', 'coordx', 'coordy', 'shiftx', 'shifty'])
            
            # Flatten the final_result and write data
            for station_group in data:
                for station_data in station_group:
                    for row in station_data:  # Iterate through the innermost list
                        if len(row) == 6:
                            lable, sta, station_offset, coord, shiftx, shifty = row
                            coordx, coordy = coord  # Unpack the coord tuple
                            
                            # Write the data into the CSV file
                            writer.writerow([lable, sta, station_offset, coordx, coordy, shiftx, shifty])
                        else:
                            print(f"Unexpected data format: {row}")
        
        print(f'Data successfully written to {file_path}')
    except Exception as e:
        print(f'An error occurred while writing to the file: {e}')

def write_report(data, data2):
    """
    Saves the alignment report to an Excel file, writing data into specific sheets using openpyxl.
    
    Parameters:
    data (list): The list of report variables for each curve.
    """

    #환경변수 설정
    km_precision = 3 #측점 자릿수
    coord_precision = 4 #좌표 자릿수
    dimention = 3#기타 숫자 자릿수
    filename = 'c:/temp/alignmentreport.xlsx'

    # Create a new workbook or load an existing one
    # Create a new workbook, overwriting any existing file
    workbook = Workbook()
    
    for i, entry in enumerate(data):
        # Create a new sheet or access the existing one dynamically based on i (IP1, IP2, ...)
        sheetname = f'IP{entry[0]}' # Dynamic sheet name like IP1, IP2, etc.

        # Check if the sheet already exists, if not create a new one
        if sheetname in workbook.sheetnames:
            sheet = workbook[sheetname]
        else:
            sheet = workbook.create_sheet(title=sheetname)

        if entry[2] == 'simplecurve':  # Simple curve case
            
            sheet['A3'] = f"'===================〈 IP  NO. {entry[0]} >==================="#IPNO
            sheet['A4'] = f'I P [ X ] = {entry[1][0]:.{coord_precision}f}' # Write IP_X to cell F5
            sheet['D4'] = f'I P [ Y ] = {entry[1][1]:.{coord_precision}f}' # Write IP_Y to cell L5
            sheet['G6'] = '단곡선' #curvetype
            sheet['E6'] = f'({entry[3]})' #curvedirection
            sheet['A5'] = f"방위각 1 = {degrees_to_dms(entry[4])}" #방위각1
            sheet['E5'] = f"방위각 2 = {degrees_to_dms(entry[5])}" #방위각2
            sheet['A6'] = f'교각(IA) = {degrees_to_dms(entry[6])}'  #교각
            sheet['A7'] = 'CURVE CENTER'
            sheet['C7'] = f'X = {entry[7][0]:.{coord_precision}f}' # CENTER X
            sheet['F7'] = f'Y = {entry[7][1]:.{coord_precision}f}' # CENTER X
            sheet['A8'] = f'R = {entry[8]:.{dimention}f}' # R
            sheet['C8'] = f'IP 연장1 = {entry[9]:.{dimention}f}' #ip연장1
            
            sheet['A9'] = f'M = 0:.{dimention}f' #M
            sheet['C9'] = f'V = {entry[13]:.{dimention}f}' #V
            sheet['F9'] = f'Z = {entry[12] * 0.001:.{dimention}f}' #Z
            sheet['A10'] = f'TL = {entry[14][0]:.{dimention}f}' #TL
            sheet['C10'] = f'CL = {entry[14][1]:.{dimention}f}' #CL
            sheet['F10'] = f'SL = {entry[14][2]:.{dimention}f}' #SL
            sheet['A11'] = f'IP 정측점 = {format_distance(entry[18], decimal_places=km_precision)}' #IP정측점
            sheet['B12'] = f'BC = {format_distance(entry[19], decimal_places=km_precision)}' #BC측점
            sheet['B13'] = f'EC = {format_distance(entry[20], decimal_places=km_precision)}' #EC측점
            sheet['D12'] = f'{entry[21][0]:.{coord_precision}f}' #BC_X
            sheet['F12'] = f'{entry[21][1]:.{coord_precision}f}' #BC_Y
            sheet['D13'] = f'{entry[22][0]:.{coord_precision}f}' #EC_X
            sheet['F13'] = f'{entry[22][1]:.{coord_precision}f}' #EC_Y
            
        else:  # Cubic parabola case
            sheet['A3'] = f"'===================< IP  NO. {entry[0]} >==================="#IPNO
            sheet['A4'] = f'I P [ X ]  = {entry[1][0]:.{coord_precision}f}' # Write IP_X to cell F5
            sheet['D4'] = f'I P [ Y ]  = {entry[1][1]:.{coord_precision}f}' # Write IP_Y to cell L5
            sheet['G6'] = '3차포물선' #curvetype
            sheet['E6'] = f'({entry[3]})' #curvedirection
            sheet['A5'] = f"방위각 1  = {degrees_to_dms(entry[4])}" #방위각1
            sheet['E5'] = f"방위각 2  = {degrees_to_dms(entry[5])}" #방위각2
            sheet['A6'] = f'교각(IA)  = {degrees_to_dms(entry[6])}'  #교각
            sheet['A7'] = 'CURVE CENTER'
            sheet['C7'] = f'X  = {entry[7][0]:.{coord_precision}f}' # CENTER X
            sheet['F7'] = f'Y  = {entry[7][1]:.{coord_precision}f}' # CENTER X
            sheet['A8'] = f'R  = {entry[8]:.{dimention}f}' # R
            sheet['C8'] = f'IP 연장1  = {entry[9]:.{dimention}f}' #ip연장1
            
            sheet['A9'] = f'M  = {entry[11]:.{dimention}f}' #M
            sheet['C9'] = f'V  = {entry[13]:.{dimention}f}' #V
            sheet['F9'] = f'Z  = {entry[12] * 0.001:.{dimention}f}' #Z
            sheet['A12'] = f'X1  = {entry[14][0]:.{dimention}f}' #X1
            sheet['A10'] = f'TL  = {entry[14][10]:.{dimention}f}' #TL
            sheet['C10'] = f'CL  = {entry[14][12]:.{dimention}f}' #CL
            sheet['A11'] = f'LC  = {entry[14][11]:.{dimention}f}' #lc
            sheet['C12'] = f'Y1  = {entry[14][4]:.{dimention}f}' #Y1
            sheet['C11'] = f'L  = {entry[14][3]:.{dimention}f}' #L
            sheet['F10'] = f'SL  = {entry[14][13]:.{dimention}f}' #SL
            
            #sheet['H13'] = f'W = {entry[14][9]:.3f}' #W
            #sheet['L13'] = f'X2 = {entry[14][1]:.3f}' #X2
            #sheet['P13'] = f'S = {entry[14][7]:.3f}' #S
            #sheet['P14'] = f'F = {entry[14][6]:.3f}' #F
            sheet['D13'] = f'THITA = {degrees_to_dms(math.degrees(entry[17]))}' #PC점의 접선각
            #sheet['H16'] = f'Θ3 = {degrees_to_dms(entry[16])}' #SP>PC점의 방위각
            #sheet['M16'] = f'O→PC = {degrees_to_dms(entry[15])}' #O>PC점 방위각

            sheet['A13'] = f'B  = {degrees_to_dms(math.degrees(entry[14][16]))}'#B
            
            sheet['A14'] = f'C  = {degrees_to_dms(math.degrees(entry[14][15]))}'#C
            sheet['D14'] = f'원곡선교각  = {degrees_to_dms(math.degrees(entry[14][14]))}'#원곡선교각


            
            sheet['A15'] = f'IP 정측점  = {format_distance(entry[18], decimal_places=km_precision)}' #IP정측점
            sheet['D15'] = f'IP 역측점  = {format_distance(entry[18], decimal_places=km_precision)}' #IP정측점
            
            sheet['B16'] = f'SP  = {format_distance(entry[19], decimal_places=km_precision)}' #SP측점
            sheet['B17'] = f'PC  = {format_distance(entry[20], decimal_places=km_precision)}' #PC측점
            sheet['B18'] = f'CP  = {format_distance(entry[21], decimal_places=km_precision)}' #CP측점
            sheet['B19'] = f'PS  = {format_distance(entry[22], decimal_places=km_precision)}' #PS측점
            sheet['D16'] = f'X  = {entry[23][0]:.{coord_precision}f}' #SP_X
            sheet['F16'] = f'Y  = {entry[23][1]:.{coord_precision}f}' #SP_Y
            sheet['D17'] = f'X  = {entry[24][0]:.{coord_precision}f}' #PC_X
            sheet['F17'] = f'Y  = {entry[24][1]:.{coord_precision}f}' #PC_Y
            sheet['D18'] = f'X  = {entry[25][0]:.{coord_precision}f}' #CP_X
            sheet['F18'] = f'Y  = {entry[25][1]:.{coord_precision}f}' #CP_Y
            sheet['D19'] = f'X  = {entry[26][0]:.{coord_precision}f}' #PS_X
            sheet['F19'] = f'Y  = {entry[26][1]:.{coord_precision}f}' #PS_Y

        #공통
        sheet['B21'] = 'CHAINAGE'
        sheet['D21'] = 'X(North)'
        sheet['F21'] = 'Y(East)'
        # Write the relevant station data for the current entry
        if i < len(data2):  # Ensure you do not exceed data2 bounds
            station_group = data2[i]  # Get the corresponding station group for the current entry
            start_row = 22  # Start writing station data from row 21

            for station_data in station_group:
                for row in station_data:  # Iterate through the innermost list
                    lable, sta, station_offset, coord, shiftx, shifty = row
                    # Write values into the sheet
                    sheet[f'A{start_row}'] = lable
                    sheet[f'B{start_row}'] = sta
                    #sheet[f'C{start_row}'] = station_offset
                    sheet[f'D{start_row}'] = coord[0]
                    sheet[f'F{start_row}'] = coord[1]
                    #sheet[f'F{start_row}'] = shiftx
                    #sheet[f'G{start_row}'] = shifty

                    start_row += 1  # Move to the next row
            
    # Remove default sheet if it exists (usually "Sheet" when a new workbook is created)
    if 'Sheet' in workbook.sheetnames:
        del workbook['Sheet']

    # Save the workbook
    save_with_retry(workbook, filename, max_retries=100, delay=1)
    #workbook.save(filename)
    print(f"Data successfully written to {filename}")

'''
def format_distance(number, decimal_places=2):
    negative = False
    if number < 0:
        negative = True
        number = abs(number)
        
    km = int(number) // 1000
    remainder = number % 1000  # Keep the full remainder without pre-formatting

    # Dynamically generate the format string using variables for field width and precision
    format_string = f"{{:d}}km{{:06.{decimal_places}f}}"
    
    # Use the dynamically created format string
    formatted_distance = format_string.format(km, remainder)
    
    if negative:
        formatted_distance = "-" + formatted_distance
    
    return formatted_distance
'''
def format_distance(number, decimal_places=2):
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

def main():
    #변수입력받기
    user_input1 = input('계산 간격 입력: (기본값 20) ')
    unit = int(user_input1) if user_input1 else 20
    
    user_input2 = input('시작 측점 입력: (기본값 0) ')
    start_STA = float(user_input2) if user_input2 else 0
    
    user_input3 = input('설계최고속도 입력: (기본값 250) ')
    designSpeed = int(user_input3) if user_input3 else 250
    
    user_input4 = input('구간내 적용 도상입력 0자갈도상 1콘크리트도상 : (기본값 자갈도상) ')
    
    if user_input4 ==0:
        ballast = '자갈도상'
    else:
        ballast = '콘크리트도상'
    
    user_input5 = input('M,Z,V 수동입력?: y or n (기본값 아니오) Z단위:MM ').strip().lower()
    
    # Check if the input is "yes" or "y" (indicating manual input)
    ismanualmzv = user_input5 in ['y', 'yes']
    
    lines = read_file()
    if not lines:
        print('입력된 선형 없음')
        return
    
    alignment = pasing_ip(lines)
    linestring = create_Linestring(alignment)
    
    Radius_list = [point[2] for point in alignment[1:-1]]
    
    ia_list = calculate_angles_and_plot(linestring)

    if user_input5:#수동입력
        parameters = []
        for i in range(len(Radius_list)):
            inputvariable = input('Enter M,Z,V (쉼표로 구분): ').split(',')  # Split the input
            print(f'현재 입력값 IP{i+1}  M = {inputvariable[0]}, Z = {inputvariable[1]} , V= {inputvariable[2]}')
            
            
            inputvariable = [float(x) for x in inputvariable]  # Convert each value to float
            parameters.append(inputvariable)
        #잠시 대기
        print('입력이 완료되었습니다. 계산을 수행합니다.')    
    else:#자동입력
        parameters = cal_parameter(Radius_list, designSpeed, ballast)
    
    
    final_result, alignment_report_variable_list = calculate_curve(linestring, Radius_list, ia_list, parameters, unit, start_STA)
    
    #좌표출력
    #write_data(final_result)
    #print(final_result)
    
    #선형계산서 출력
    write_report(alignment_report_variable_list, final_result)
    
    print('작업완료')
if __name__ == '__main__':
    main()
