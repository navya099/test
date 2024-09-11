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

def calculate_north_bearing(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.degrees(math.atan2(dx, dy))
    if bearing < 0:
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

def calculate_O_PC_angle(v10, x10, direction):
    if direction > 0:
        return (v10 + x10 - 90) % 360
    else:
        return (v10 - x10 + 90) % 360

def calculate_simple_curve(linestring, radius_list, angles):
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
    for i in range(len(linestring.coords) - 2):
        IA_rad = math.radians(angles[i])
        CL = radius_list[i] * IA_rad
        TL = radius_list[i] * math.tan(IA_rad / 2)
        IA_DEGREE = angles[i]

        BP_XY = (linestring.coords[i][0], linestring.coords[i][1])
        IP_XY = (linestring.coords[i + 1][0], linestring.coords[i + 1][1])
        EP_XY = (linestring.coords[i + 2][0], linestring.coords[i + 2][1])

        h1 = calculate_north_bearing(BP_XY[0], BP_XY[1], IP_XY[0], IP_XY[1])
        h2 = calculate_north_bearing(IP_XY[0], IP_XY[1], EP_XY[0], EP_XY[1])

        BP_IP_BEARING = calculate_bearing(BP_XY[0], BP_XY[1], IP_XY[0], IP_XY[1])
        IP_EP_BEARING = calculate_bearing(IP_XY[0], IP_XY[1], EP_XY[0], EP_XY[1])

        Lb0 = calculate_distance(BP_XY[0], BP_XY[1], IP_XY[0], IP_XY[1])
        Lb1 = calculate_distance(IP_XY[0], IP_XY[1], EP_XY[0], EP_XY[1])

        if i == 0:
            IP_STA = BP_STA + Lb0
        else:
            X16 = TL_list[i-1]
            BP_STA = EC_STA_LIST[i-1]
            IP_STA = BP_STA + Lb0 - X16

        BC_XY = calculate_destination_coordinates(IP_XY[0], IP_XY[1], BP_IP_BEARING, -TL)
        direction = find_direction(radius_list[i], h1, h2)
        O_PC_ANGLE = calculate_O_PC_angle(h1, 0, direction)
        CURVE_CENTER_XY = (math.sin(math.radians(O_PC_ANGLE + 180)) * radius_list[i] + BC_XY[0],
                           math.cos(math.radians(O_PC_ANGLE + 180)) * radius_list[i] + BC_XY[1])

        EC_XY = calculate_destination_coordinates(IP_XY[0], IP_XY[1], IP_EP_BEARING, TL)

        BC_STA = IP_STA - TL
        EC_STA = BC_STA + CL

        BC_XY_list.append(BC_XY)
        O_XY_list.append(CURVE_CENTER_XY)
        EC_XY_list.append(EC_XY)
        direction_list.append(direction)

        BC_STA_LIST.append(BC_STA)
        EC_STA_LIST.append(EC_STA)
        TL_list.append(TL)
        IP_STA_list.append(IP_STA)
        prebearing_list.append(h1)
        nextbearing_list.append(h2)

    return BC_STA_LIST ,EC_STA_LIST, IP_STA_list, prebearing_list, nextbearing_list

def cal_parameter(radius_list):
    parameters = []
    for i in range(len(radius_list)):
        try:
            R = radius_list[i]
            B = 2.2
            D = 4.4
            
            V = (R * 160 / 11.8) ** 0.5
            if V >= 120:
                V = 120
            C = 11.8 * V ** 2 / R
            
            if C >= 160:
                C = 160
            
            L = 600 * C / 1000
            theta = math.atan(C / 1500)

            W = 24000 / R
            Qc = 4300 * math.sin(theta) - 1050 * (1 - math.cos(theta))
            S = 2400 / R
            alpha = round(W + Qc + S, -1)
            AA = B + alpha * 0.001

            parameters.append([L, B, AA, D])
        except ValueError:
            print("잘못된 입력입니다. 숫자를 입력해주세요.")
            
    return parameters

def create_dat(data, data2):
    file_path = 'C:/Users/KDB/Downloads/cloxy3w/data.dat'
    with open(file_path, 'w', encoding='utf-8') as file:
        # Extract coordinates from the LineString object
        coords = list(data[4].coords)
        ip_x = [coord[0] for coord in coords[1:-1]]  # Extract X coordinates
        ip_y = [coord[1] for coord in coords[1:-1]]  # Extract Y coordinates
        
        
        file.write(f' {len(data[2])}\n')#총 IP갯수
        for i in range(len(data[2])):
            # Write each line with appropriate formatting
            #IPNO,R,L,B,A',D
            file.write(f'    {i+1}   {data[0][i]:.6f}    {data[1][i][0]:.6f}     {data[1][i][1]:.6f}     {data[1][i][2]:.6f}      {data[1][i][3]:.6f}\n')
            file.write(f'   {data[2][i]:.6f}  {data[3][i]:.6f}\n')#IPSTA,IA
            file.write(f' {data2[0][i]:.6f}  {data2[1][i]}     20.00000\n')#BC,EC,DISTANE
            file.write('y\n')
            file.write(f'  {ip_x[i]:.6f}  {ip_y[i]:.6f}  {data[5][i]:.6f}  {data[6][i]:.6f}\n')#IPX,Y,H1,H2

def main():
    lines = read_file()
    if not lines:
        return
    
    alignment = pasing_ip(lines)
    linestring = create_Linestring(alignment)
    
    radius_list = [point[2] for point in alignment[1:-1]]
    
    ia_list = calculate_angles_and_plot(linestring)
    BC_STA_LIST, EC_STA_LIST, IP_STA_list, prebearing_list, nextbearing_list = calculate_simple_curve(linestring, radius_list, ia_list)
    parameters = cal_parameter(radius_list)
    
    print(len(parameters))
    data2 = [BC_STA_LIST, EC_STA_LIST]
    
    data = [radius_list, parameters, IP_STA_list, ia_list, linestring, prebearing_list, nextbearing_list]
    create_dat(data, data2)
    
if __name__ == '__main__':
    main()
