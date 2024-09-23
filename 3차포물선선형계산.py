from tkinter import filedialog
import csv
from shapely.geometry import LineString
import math
    
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
def cal_parameter(radius_list):
    parameters = []
    for i in range(len(radius_list)):
        try:
            maxV = 250#설계속도
            track_type = '자갈도상'
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

    
    return f"{deg}° {minutes}' {seconds:.2f}\""

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
    return x1, x2, W13, L, Y, W15, F, S, K, W, TL, Lc, CL

#완화곡선 시종점 좌표계산함수
def calculate_spiral_coordinates(BP_XY, IP_XY, EP_XY, h1, h2, TL, x1, Y, SP_PC_bearing, Rc, Lc):
    """Calculate the coordinates of SP, PC, CP, and PS."""
    SP_XY = (
        math.cos(math.radians(h1 + 180)) * TL + IP_XY[0],
        math.sin(math.radians(h1 + 180)) * TL + IP_XY[1]
    )
    PC_XY = (
        SP_XY[0] + x1 * math.cos(math.radians(h1)) + Y * math.cos(math.radians(h1 + 90)),
        SP_XY[1] + x1 * math.sin(math.radians(h1)) + Y * math.sin(math.radians(h1 + 90))
    )
    CP_XY = calculate_CP_XY(PC_XY[0], PC_XY[1], Rc, SP_PC_bearing, Lc, h2)
    PS_XY = (
        math.cos(math.radians(h2)) * TL + IP_XY[0],
        math.sin(math.radians(h2)) * TL + IP_XY[1]
    )
    return SP_XY, PC_XY, CP_XY, PS_XY

#메인 3차포물선 계산함수
def calculate_spiral(linestring, Radius_list, angles, parameters):

    final_result = []
    
    O_XY_list = []
    cubic_parabola_XY_list = []
    cubic_parabola_STA_list = []
    
    TL_LIST = []
    IP_STA_list = []
    
    direction_list = []
    prebearing_list = []
    nextbearing_list = []
    
    BP_STA = 0
    BP_STA_LIST = [0]

    station_coordlist = []
    for i in range(len(linestring.coords)-2):
        IA_rad = math.radians(angles[i])
        IA_DEGREE = angles[i]
        
        #토목좌표
        BP_XY = (linestring.coords[i][0], linestring.coords[i][1])
        IP_XY = (linestring.coords[i + 1][0], linestring.coords[i + 1][1])
        EP_XY = (linestring.coords[i + 2][0], linestring.coords[i + 2][1])

        h1 = calculate_bearingN(BP_XY[0], BP_XY[1], IP_XY[0], IP_XY[1])#방위각1(도)
        h2 = calculate_bearingN(IP_XY[0], IP_XY[1], EP_XY[0], EP_XY[1])#방위각2(도)

        BP_IP_BEARING = calculate_bearing(BP_XY[0], BP_XY[1], IP_XY[0], IP_XY[1])
        IP_EP_BEARING = calculate_bearing(IP_XY[0], IP_XY[1], EP_XY[0], EP_XY[1])

        IP_distnace1 = calculate_distance(BP_XY[0], BP_XY[1], IP_XY[0], IP_XY[1]) #ip연장1
        IP_distnace2 = calculate_distance(IP_XY[0], IP_XY[1], EP_XY[0], EP_XY[1]) #연장2

        
        
        Rc = Radius_list[i]
        direction = find_direction(Rc, h1, h2)
        
        m, z, v = parameters[i]
        theta_pc = calculate_theta_pc(m, z, Rc)#pc점의 접선각
        
        x1, x2, W13, L, Y, W15, F, S, K, W, TL, Lc, CL = calculate_cubic_parabola_parameter(m, z, direction, theta_pc, Rc, IA_rad)#파라매터

        
        O_PC_bearing = calculate_O_PC_bearing(h1, theta_pc, W13)#O>PC 방위각(도)
        
        SP_PC_bearing = calculate_SP_PC_bearing(W13, h1, math.degrees(theta_pc))#SP>PC방위각(도)

        TL_LIST.append(TL)
        
        if direction == 1:
            curvedirection = 'RIGHT CURVE'
        else:
            curvedirection = 'LEFT CURVE'
        if 0:
            #3차포물선 제원 출력
            print("\n------------------\n")
            print("\n3차포물선 제원 출력\n")
            print(f"\n-----IPNO.{i+1}-----\n")
            print(f"\n{curvedirection}\n")
            print("설계속도  =",v , 'km/h' )
            print("캔트 =",z )
            print("m =",m )
            print("x1 =",x1 )
            print("PC점의 접선각 =",degrees_to_dms(math.degrees(theta_pc) ))
            print("x2 =",x2 )
            print("완화곡선 길이 L =",L)
            print("Y1 =",Y)
            print("이정량 F =",F)
            print("수평좌표차 K =",K )
            print("W =",W )
            print("TL =", TL)
            print("원곡선 길이  =",Lc )
            print("CL  =",CL )
            print("\n------------------\n")

        

        #좌표계산
        SP_XY, PC_XY, CP_XY, PS_XY = calculate_spiral_coordinates(BP_XY, IP_XY, EP_XY, h1, h2, TL, x1, W15, SP_PC_bearing, Rc, Lc)

        CURVE_CENTER = (math.cos(math.radians(O_PC_bearing + 180)) * Rc + PC_XY[0], #CURVE CENTER
                        math.sin(math.radians(O_PC_bearing + 180)) * Rc + PC_XY[1])
        cubic_parabola_XY_list.append([SP_XY,PC_XY,CP_XY,PS_XY])

        

        
        if i == 0:
            cubic_parabola_STA_list.append([0, 0, 0, 0])#인덱스 오류 방지로 0 할당
            # 첫 번째 값을 덮어쓰기
            IP_STA = BP_STA + IP_distnace1
            SP_STA = IP_STA - TL
            PC_STA = SP_STA + L
            CP_STA = PC_STA + Lc
            PS_STA = CP_STA + L

            cubic_parabola_STA_list[0] = [SP_STA, PC_STA, CP_STA, PS_STA]  # 첫 번째 값 덮어쓰기
        else:
            # 두 번째 이상의 경우 새로운 값을 append
            BP_STA = cubic_parabola_STA_list[i-1][3]  # 이전 PS_STA 값
            IP_STA = BP_STA + IP_distnace1 - TL_LIST[i - 1]

            SP_STA = IP_STA - TL
            PC_STA = SP_STA + L
            CP_STA = PC_STA + Lc
            PS_STA = CP_STA + L

            cubic_parabola_STA_list.append([SP_STA, PC_STA, CP_STA, PS_STA])
        
        
        if 0:
            print(f'IPNO.{i+1}')
            print(f'BP = {BP_XY}')
            print(f'방위각1 = {h1}')
            print(f'방위각2 = {h2}')
            print(f'BP = {BP_STA}')
            print(f'IP정측점 = {IP_STA}')
            print(f'SP좌표 = {SP_XY}')
            print(f'PC좌표 = {PC_XY}')
            print(f'CP좌표 = {CP_XY}')
            print(f'PS좌표 = {PS_XY}')
            print(f'SP = {SP_STA}')
            print(f'PC = {PC_STA}')
            print(f'CP = {CP_STA}')
            print(f'PS = {PS_STA}')
            
        
        # unit 간격으로 PS_STA까지 스테이션 리스트 생성
        # Ensure BP_STA and PS_STA are integers
        BP_STA_int = int(round(BP_STA))
        PS_STA_int = int(round(PS_STA))

        # unit 간격으로 PS_STA까지 스테이션 리스트 생성
        unit = 40
        station_list = generate_integers(BP_STA_int, PS_STA_int, unit)

        # 최종적으로 station과 coord의 리스트 리턴
        station_coordlist = []

        # 스테이션 리스트에 있는 각 sta에 대해 좌표 계산
        for j, sta in enumerate(station_list):
            if j ==0:
                lable = 'B  P'
            else:
                lable = get_station_label(sta, SP_STA, PC_STA, CP_STA, PS_STA, PS_STA)#제원문자
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
                PBP_XY = cubic_parabola_XY_list[i-1][3]
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
    return final_result

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


#측점제원문자
def get_station_label(B28, H20, H21, H22, H23, W21, epsilon=1e-9):
    '''
    Args:
    B28 = 측점
    H20, H21, H22, H23 = sp, pc, cp, ps 측점
    W21 = ps 측점
    epsilon = tolerance for floating-point comparison
    
    Returns:
    A string representing the station label.
    '''
    
    if abs(B28 - H20) < epsilon:
        return "S P"
    elif abs(B28 - H21) < epsilon:
        return "P C"
    elif abs(B28 - H22) < epsilon:
        return "C P"
    elif abs(B28 - H23) < epsilon:
        return "P S"
    elif abs(B28 - W21) < epsilon:
        return "E P"
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
        
def main():
    lines = read_file()
    if not lines:
        return
    
    alignment = pasing_ip(lines)
    linestring = create_Linestring(alignment)
    
    Radius_list = [point[2] for point in alignment[1:-1]]
    
    ia_list = calculate_angles_and_plot(linestring)
    
    parameters = cal_parameter(Radius_list)
    
    
    final_result = calculate_spiral(linestring, Radius_list, ia_list, parameters)

    write_data(final_result)
    
    print('작업완료')
if __name__ == '__main__':
    main()
