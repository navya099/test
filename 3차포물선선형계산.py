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

def calculate_bearingN(V8, V9, F5, L5):
    angle = math.degrees(math.atan2(F5 - V8, L5 - V9))  # ATAN2 및 DEGREES 계산
    if angle < 0:
        angle += 360  # 음수일 경우 360을 더해 양의 각도로 변환
    return angle

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

def calculate_O_PC_angle(v10, x10, direction):
    if direction > 0:
        return (v10 + x10 - 90) % 360
    else:
        return (v10 - x10 + 90) % 360
    
def calculate_V(Cm, Cd, R, maxV):
    V = int(math.sqrt((Cm +  Cd) * R / 11.8))  # 정수로 변환
    return min(V, maxV)  # V가 maxV를 초과하지 않도록 제한

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

def calculate_spiral(linestring, Radius_list, angles, parameters):
    O_XY_list = []
    BC_XY_list = []
    EC_XY_list = []
    BC_STA_LIST = []
    EC_STA_LIST = []
    TL_list = []
    IP_STA_list = []
    direction_list = []
    prebearing_list = []
    nextbearing_list = []
    
    BP_STA = 0
    for i in range(len(linestring.coords)-2):
        IA_rad = math.radians(angles[i])
        IA_DEGREE = angles[i]

        BP_XY = (linestring.coords[i][0], linestring.coords[i][1])
        IP_XY = (linestring.coords[i + 1][0], linestring.coords[i + 1][1])
        EP_XY = (linestring.coords[i + 2][0], linestring.coords[i + 2][1])

        h1 = calculate_bearingN(BP_XY[0], BP_XY[1], IP_XY[0], IP_XY[1])
        h2 = calculate_bearingN(IP_XY[0], IP_XY[1], EP_XY[0], EP_XY[1])

        BP_IP_BEARING = calculate_bearing(BP_XY[0], BP_XY[1], IP_XY[0], IP_XY[1])
        IP_EP_BEARING = calculate_bearing(IP_XY[0], IP_XY[1], EP_XY[0], EP_XY[1])

        Lb0 = calculate_distance(BP_XY[0], BP_XY[1], IP_XY[0], IP_XY[1])
        Lb1 = calculate_distance(IP_XY[0], IP_XY[1], EP_XY[0], EP_XY[1])
        
        Rc = Radius_list[i]
        m = parameters[i][0]
        z = parameters[i][1]
        v = parameters[i][2]
        
        x1 = m * (z * 0.001) #X
        theta_pc = math.atan(x1 / (2 * Rc)) #PC점의 접선각( 라디안)
        x2 = x1 - (Rc * math.sin((theta_pc))) # X2
        L = x1 * (1 + ((math.tan(theta_pc)**2)) / 10) #완화곡선 길이
        
        Y = (math.pow(x1,2))/(6*Rc) # Y
        F = Y - Rc * (1- math.cos((theta_pc))) #이정량 F
        K = F * math.tan((IA_rad) / 2) #수평좌표차 K
        W = (Rc + F)* math.tan((IA_rad/2)* math.pi/180) # W
        TL = x2 + W # TL
        Lc = Rc * (IA_rad - 2*(theta_pc)) #원곡선 길이
        CL = Lc + 2 * L #전체 CL

        '''
        #3차포물선 제원 출력
        print("\n------------------\n")
        print("\n3차포물선 제원 출력\n")
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

        '''

        print(f'BP = {BP_XY}')
        print(f'방위각1 = {h1}')
        print(f'방위각2 = {h2}')
        SP_XY = (math.cos(math.radians(h1+180))*TL+IP_XY[1],
                 math.sin(math.radians(h1+180))*TL+IP_XY[0])
        PC_XY = 0
        CP_XY = 0
        PS_XY = 0
        print(f'SP좌표 = {SP_XY}')
        
def calculate_bearing(x1, y1, x2, y2):
    # 방위각 계산함수
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.degrees(math.atan2(dy, dx))
    return bearing


def calculate_distance(x1, y1, x2, y2):
    # 거리계산함수
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    distance_x = abs(x2 - x1)
    distance_y = abs(y2 - y1)
    return distance



def create_dat(data, data2):
    file_path = 'C:/Users/KDB/Downloads/cloxy3w/data.dat'
    with open(file_path, 'w', encoding='utf-8') as file:
        # Extract coordinates from the LineString object
        coords = list(data[4].coords)
        ip_x = [coord[0] for coord in coords[1:-1]]  # Extract X coordinates
        ip_y = [coord[1] for coord in coords[1:-1]]  # Extract Y coordinates
        
        
        file.write(f'{" " * 1}{len(data[2])}\n')#총 IP갯수
        for i in range(len(data[2])):
            # Write each line with appropriate formatting
            #IPNO,R,L,B,A',D
            file.write(f'{" " * 4}{i+1}{" " * 3}{data[0][i]:.6f}{" " * 4}{data[1][i][0]:.6f}{" " * 5}{data[1][i][1]:.6f}{" " * 5}{data[1][i][2]:.6f}{" " * 6}{data[1][i][3]:.6f}\n')
            if i == 0:
                file.write(f'{" " * 3}{data[2][i]:.6f}{" " * 2}{data[3][i]:.6f}\n')#IPSTA,IA
            else:
                file.write(f'{" " * 2}{data[2][i]:.6f}{" " * 2}{data[3][i]:.6f}\n')#IPSTA,IA
            file.write(f'{" " * 1}{data2[0][i]:.6f}{" " * 2}{data2[1][i]}{" " * 5}20.00000\n')#BC,EC,DISTANE
            file.write('y\n')
            if i == 0:
                file.write(f'{" " * 2}{ip_x[i]:.6f}{" " * 2}{ip_y[i]:.6f}{" " * 2}{data[5][i]:.6f}{" " * 2}{data[6][i]:.6f}\n')#IPX,Y,H1,H2
            else:
                file.write(f'{" " * 2}{ip_x[i]:.6f}{" " * 2}{ip_y[i]:.6f}{" " * 3}{data[5][i]:.6f}{" " * 2}{data[6][i]:.6f}\n')#IPX,Y,H1,H2
            
def main():
    lines = read_file()
    if not lines:
        return
    
    alignment = pasing_ip(lines)
    linestring = create_Linestring(alignment)
    
    Radius_list = [point[2] for point in alignment[1:-1]]
    
    ia_list = calculate_angles_and_plot(linestring)
    
    parameters = cal_parameter(Radius_list)
    print(parameters)
    
    calculate_spiral(linestring, Radius_list, ia_list, parameters)
    
    #data = [radius_list, parameters, IP_STA_list, ia_list, linestring, prebearing_list, nextbearing_list]
    #create_dat(data, data2)
    
    print('작업완료')
if __name__ == '__main__':
    main()
