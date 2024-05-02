import tkinter as tk
from tkinter import filedialog, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk  # 추가
import numpy as np
import math
import simplekml
import os
import pyproj
from lxml import etree
import csv
import ezdxf
from tkinter.ttk import Combobox
from collections import Counter

def create_dxf(filename, coordinates, *args):
    doc = ezdxf.new()
    msp = doc.modelspace()

    # Create a polyline entity
    polyline = msp.add_lwpolyline(coordinates)

    # Set the color of the polyline to red (color index 1)
    '''#ACI인덱스
    0: BYBLOCK
    1: Red
    2: Yellow
    3: Green
    4: Cyan
    5: Blue
    6: Magenta
    7: White
    8: Gray
    9: BYLAYER
    '''
    
    # Set polyline properties if needed
    polyline.dxf.layer = 'MyLayer'
    
    # Set the color of the polyline to red
    red_color_index = 1  # Get color index for 'red'
    polyline.dxf.color = red_color_index
    
    text_color_index = 7
    text_height = 3
    
    labels1, labels2 = args
    
    # Add text labels at each coordinate
    for coord, label in zip(coordinates, labels1):
        msp.add_text(label, dxfattribs={'insert': coord, 'height': text_height, 'color': 11})

    # Add text labels at each coordinate
    for coord, label in zip(coordinates, labels2):
        if label.strip():  # Check if the label is not empty after stripping whitespace
            msp.add_text(label, dxfattribs={'insert': coord, 'height': 5, 'color': 11})

        
    # Save the DXF document to a file
    doc.saveas("C:/temp/" + filename)

#TM좌표를 경위도 좌표로 변환함수(좌표배열)
def calc_pl2xy_array(coords_array):
    transformed_coords = []

    # Define CRS
    p1_type = pyproj.CRS.from_epsg(5186)#TM
    p2_type = pyproj.CRS.from_epsg(4326)#위도

    # Create transformer
    transformer = pyproj.Transformer.from_crs(p1_type, p2_type, always_xy=True)

    # Iterate over each coordinate tuple in the array
    for coords in coords_array:
        # Unpack array into x and y coordinates
        x, y = coords[0], coords[1]

        # Transform coordinates
        x, y = transformer.transform(x, y)

        # Append transformed coordinates to the result array
        transformed_coords.append((x, y))
    return transformed_coords  # [m]

#TM좌표를 경위도 좌표로 변환함수(좌표)
def calc_pl2xy(long, lat):
    p1_type = pyproj.CRS.from_epsg(5186)
    p2_type = pyproj.CRS.from_epsg(4326)
    transformer = pyproj.Transformer.from_crs(p1_type, p2_type, always_xy=True)
    x, y = transformer.transform(long, lat)
    
    return x, y  # [m]


#경위도좌표를 TM 좌표로 변환함수(좌표배열)
def calc_latlon2TM_array(coords_array):
    transformed_coords = []

    # Define CRS
    p1_type = pyproj.CRS.from_epsg(4326)#위도
    p2_type = pyproj.CRS.from_epsg(5186)#TM

    # Create transformer
    transformer = pyproj.Transformer.from_crs(p1_type, p2_type, always_xy=True)

    # Iterate over each coordinate tuple in the array
    for coords in coords_array:
        # Unpack array into x and y coordinates
        x, y, z = coords[0], coords[1], coords[2]

        # Transform coordinates
        x, y, z = transformer.transform(x, y, z)

        # Append transformed coordinates to the result array
        transformed_coords.append((x, y, z))
    return transformed_coords  # [m]

plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False

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

  
#파일 읽기 함수
def read_file():
    global lines
     # Hide the main window
    file_path = filedialog.askopenfilename() # Open file dialog
    print('현재파일 ',file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='euc-kr') as file:
            lines = file.readlines()
    
    return lines


#다른파일 열기
def read_other_file():
    global lines
    lines = read_file()
    update_plot()
    canvas.draw()

#,를 개행리스트로 반환
def preprocess_line(lines):
    processed_lines = []
    for line in lines:
        processed_lines.extend(line.strip().split(','))
    return processed_lines

#루트파서
def parse_track(lines):

    
    i = 0
    stations = []
    radius = []
    radius_station = []
    sta = [] #정거장명
    sta_station= [] #정거장 측점
    pitch = []
    pitch_station = []
    try:
        while i < len(lines):
            line = lines[i].strip()
            if line.strip() and line[0].isdigit():  # 공백이 아니고, 첫 번째 문자가 숫자인지 확인
                ixnumber = float(line.strip())
                stations.append(ixnumber) 
            elif line.startswith('.curve'):
                try:
                    # check if the previous line only contains numbers
                    prev_line = lines[i-1].strip()
                    if prev_line.isdigit():

                        if line.split()[-1].isdigit():
                            number = int(prev_line)
                            value = float(line.split()[-1])
                            radius_station.append(number)
                            radius.append(value)
                        else:
                            number = int(prev_line)
                            value = float(line.split()[-1].split(';')[0])
                            radius_station.append(number)
                            radius.append(value)
                    else:
                        # go up and find the previous line that contains only numbers
                        j = i - 1
                        while j >= 0:
                            prev_line = lines[j].strip()
                            if prev_line.isdigit():

                                if line.split()[-1].isdigit():
                                    number = int(prev_line)
                                    value = float(line.split()[-1])
                                    radius_station.append(number)
                                    radius.append(value)
                                else:
                                    number = int(prev_line)
                                    value = float(line.split()[-1].split(';')[0])
                                    radius_station.append(number)
                                    radius.append(value)
                                break
                            j -= 1
                except IndexError:
                    pass

            elif line.lower().startswith('.sta'):
                try:
                    # check if the previous line only contains numbers
                    prev_line = lines[i-1].strip()
                    if prev_line.isnumeric():
                        number = int(prev_line)
                        # Find the substring after '.sta' and before the first semicolon (;)
                        value1 = line.split('.sta', 1)[-1].split(';', 1)[0].strip()
                        value1 = value1[5:]
                        sta_station.append(number)
                        sta.append(value1)
                    else:
                        # go up and find the previous line that contains only numbers
                        j = i - 1
                        while j >= 0:
                            prev_line = lines[j].strip()
                            if prev_line.isnumeric():
                                number = int(prev_line)
                                # Find the substring after '.sta' and before the first semicolon (;)
                                value1 = line.split('.sta', 1)[-1].split(';', 1)[0].strip()
                                value1 = value1[5:]
                                sta_station.append(number)
                                sta.append(value1)
                                break
                            j -= 1
                except IndexError:
                    pass
            elif line.startswith('.pitch'):
                try:
                    # check if the previous line only contains numbers
                    prev_line = lines[i-1].strip()
                    if prev_line.isdigit():

                        if line.split()[-1].isdigit():
                            number = int(prev_line)
                            value = float(line.split()[-1])
                            pitch_station.append(number)
                            pitch.append(value)
                        else:
                            number = int(prev_line)
                            value = float(line.split()[-1].split(';')[0])
                            pitch_station.append(number)
                            pitch.append(value)
                    else:
                        # go up and find the previous line that contains only numbers
                        j = i - 1
                        while j >= 0:
                            prev_line = lines[j].strip()
                            if prev_line.isdigit():

                                if line.split()[-1].isdigit():
                                    number = int(prev_line)
                                    value = float(line.split()[-1])
                                    pitch_station.append(number)
                                    pitch.append(value)
                                else:
                                    number = int(prev_line)
                                    value = float(line.split()[-1].split(';')[0])
                                    pitch_station.append(number)
                                    pitch.append(value)
                                break
                            j -= 1
                except IndexError:
                    pass
            i += 1
    except ValueError as e:
        print(f'ValueError : {e} acount at line {i+1}')
        
    start_station = min(stations)
    end_station = max(stations)
    
    radius_station.insert(0,start_station)
    radius_station.append(end_station)
    
    radius.insert(0,0)
    radius.append(0)
    
    return radius_station, radius, sta_station,sta,pitch_station,pitch

    
def calculate_coordinates(x1,y1,bearing,distance):
    angle = math.radians(bearing)
    x2 = x1 + distance * math.cos(angle)
    y2 = y1 + distance * math.sin(angle)
    return x2,y2
    
def calculate_bearing(x1, y1, x2, y2):
    # Calculate the bearing (direction) between two points in Cartesian coordinates
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.degrees(math.atan2(dy, dx))
    return bearing

def calculate_bearingN(x1, y1, x2, y2):
    # Calculate the bearing (direction) between two points in Cartesian coordinates
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.degrees(math.atan2(dx, dy))
    if bearing < 0:
        bearing = 360 + bearing
    return bearing

def calculate_interval_distance(stations,radius):

    CL = []

    for i in range(len(stations)):

        if i == 0:

            CL.append(0)

        else:

             CL.append(stations[i] - stations[i-1])



    return CL

    
#곡선타입 계산함수

def calculate_curve_type(stations,radius):

    curve_type = []

    for i in range(len(stations)):

        if i == 0:

            curve_type.append("BP")

        elif i == len(stations) -1 :

            curve_type.append("EP")

        elif radius[i] == 0:

            curve_type.append("EC")

        elif radius[i-1] == 0 and radius[i] != 0:

            curve_type.append("BC")

        else:

            curve_type.append("PCC")

    return curve_type


def Create_KML(point1,point2,acr1,acr2, BC, EC,stations):# 단곡선용 kml작성함수
    
    kml = simplekml.Kml()
    
    arc = []
    for i in range(len(acr1)):
        arc.append((acr1[i],acr2[i]))

    
    final_coords = [point1] + arc + [point2]
    
    # Convert coordinates to latitude and longitude
    final_coords_latlong = calc_pl2xy_array(final_coords)

    # Add a point
    pointA = kml.newpoint(name="BP= " + format_distance(stations[0]), coords=[calc_pl2xy(point1[0], point1[1])])

    for i in range(len(BC)):
        pointB = kml.newpoint(name="BC= " + format_distance(stations[2 * i + 1]), coords=[calc_pl2xy(BC[i][0], BC[i][1])])

        pointC = kml.newpoint(name="EC= " + format_distance(stations[2 * i + 2]), coords=[calc_pl2xy(EC[i][0],EC[i][1])])
                              
    pointD = kml.newpoint(name="EP= "+ format_distance(stations[-1]), coords=[calc_pl2xy(point2[0],point2[1])])
    
    
    # Create a single linestring to connect all points
    linestring = kml.newlinestring(name="Sample Polyline", coords=final_coords_latlong)
    linestring.style.linestyle.color = simplekml.Color.red
    linestring.style.linestyle.width = 4
    
    # Save the KML file
    kml_file = "sample.kml"
    kml.save(kml_file)

    # Open the saved KML file
    os.system(f'start {kml_file}')  # This command works on Windows


    
def Create_KML2(acr1,acr2,poly_XY,stations,curve_type):# 복심곡선용 kml작성함수
    
    kml = simplekml.Kml()
    
    arc = []
    for i in range(len(acr1)):
        arc.append((acr1[i],acr2[i]))

    
    final_coords = [poly_XY[0]] + arc + [poly_XY[-1]]
    
    # Convert coordinates to latitude and longitude
    final_coords_latlong = calc_pl2xy_array(final_coords)

    # Add a point
    pointA = kml.newpoint(name="BP= " + format_distance(stations[0]), coords=[calc_pl2xy(poly_XY[0][0],poly_XY[0][1])])

    for i in range(len(stations)):
        if 'BC' in curve_type[i]:
            pointB = kml.newpoint(name="BC= " + format_distance(stations[i]), coords=[calc_pl2xy(poly_XY[i][0], poly_XY[i][1])])
        elif 'EC' in curve_type[i]:
            pointC = kml.newpoint(name="EC= " + format_distance(stations[i]), coords=[calc_pl2xy(poly_XY[i][0],poly_XY[i][1])])
        else:
            pass
    pointD = kml.newpoint(name="EP= "+ format_distance(stations[-1]), coords=[calc_pl2xy(poly_XY[-1][0],poly_XY[-1][1])])
    
    
    # Create a single linestring to connect all points
    linestring = kml.newlinestring(name="Sample Polyline", coords=final_coords_latlong)
    linestring.style.linestyle.color = simplekml.Color.red
    linestring.style.linestyle.width = 4
    
    # Save the KML file
    kml_file = "sample.kml"
    kml.save(kml_file)

    # Open the saved KML file
    os.system(f'start {kml_file}')  # This command works on Windows

    
def define_dirction(radius):
    result = []
    for a in radius:
        if a < 0:
            result.append(-1)
        elif a > 0:
            result.append(1)
        else:
            pass
    return result


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

    
    fii = end_angle - start_angle #시계방향
    fii2 = 360 - abs(end_angle - start_angle) #반시계방향

    num_angles = 100
    
    unit =  fii / (num_angles -1)
    unit2 =  fii2 / (num_angles -1)

    
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
        
        color ='blue'
    theta = np.radians(array)
    
    # Calculate arc coordinates
    x_arc = x_center + radius * np.cos(theta)
    y_arc = y_center + radius * np.sin(theta)

    return x_arc, y_arc 


def calculate_coord(BP_XY, BP_bearing, stations, radius, curve_type, interval_distance):
    IA = []
    O_XY = []
    BC_XY = []
    EC_XY = []
    EP_XY = []
    IP_XY = []
    BC_O_bearing = 0
    bearing = 0
    O_EC_bearing = 0  # O_EC_bearing 초기화

    O_XY_list = []
    BC_XY_list = []
    EC_XY_list = []
    bearing_list = []
    IP_XY_list = []
    
    IP_NUMBER = radius.count(0)
    IP_COUNT = len(radius) - IP_NUMBER

    for i in range(len(stations)):
        if i == 0:  # 초기 BC_XY 계산
            continue  # 첫 번째 반복에서는 계산하지 않고 넘어갑니다.

        if radius[i] == 0:  # 반지름이 0인 경우
            IA = 0
        else:
            IA = interval_distance[i+1] / radius[i]

        if IA != 0:
            IA_DMS = math.degrees(IA)

            
            if curve_type[i] == 'PCC':#복심곡선
                BC_XY = EC_XY
            elif i != 1:#초기 BC
                BC_XY = EP_XY
            else:#그 외의경우
                BC_XY = calculate_coordinates(BP_XY[0], BP_XY[1], BP_bearing, interval_distance[i])
            
            BC_O_bearing = bearing - 90 if i !=1 else BP_bearing - 90
            O_BC_bearing = BC_O_bearing + 180
            O_XY = calculate_coordinates(BC_XY[0], BC_XY[1], BC_O_bearing, radius[i])
            O_EC_bearing = O_BC_bearing - IA_DMS
            EC_XY = calculate_coordinates(O_XY[0], O_XY[1], O_EC_bearing, radius[i])
            bearing = O_EC_bearing - 90
            EP_XY = calculate_coordinates(EC_XY[0], EC_XY[1], bearing, interval_distance[i+2])
            TL = radius[i] * math.tan(IA/2)
            strate_bearing = bearing + IA_DMS #bc점 방위각
            
            IP_XY = calculate_coordinates(BC_XY[0], BC_XY[1], strate_bearing, TL)
            
            #여기에 출력
            print('--------------\n')
            print('IP NO ', i // 2 + 1)
            print('IA= ', degrees_to_dms(IA_DMS))
            print('R= ', radius[i])
            print('TL= ', f"{TL:.2f}")
            print('CL= ', f"{interval_distance[i+1]:.0f}")
            print('X= ', f"{IP_XY[1]:.4f}")
            print('Y=', f"{IP_XY[0]:.4f}")
            
            #print('BC_XY', BC_XY)
            #print('BC_O_bearing', BC_O_bearing)
            #print('O_XY', O_XY)
            #print('O_EC_bearing', O_EC_bearing)
            #print('EC_XY', EC_XY)
            #print('bearing', bearing)
            #print('EP_XY', EP_XY)
            print('--------------\n')
            
            # 좌표를 리스트에 추가
            O_XY_list.append(O_XY)
            BC_XY_list.append(BC_XY)
            EC_XY_list.append(EC_XY)
            IP_XY_list.append(IP_XY)
            bearing_list.append(strate_bearing)
        
    return O_XY_list, BC_XY_list, EC_XY_list, EP_XY,IP_XY_list

def find_direction(d10,v10,v11):
    '''
    # Example usage
    d10 = R
    v10 = H1
    v11 = H2
    '''
    
    if d10 == 0:
        result = 0
    elif math.sin((v11 - v10) * math.pi / 180) >= 0:
        result = 1
    else:
        result = -1
    return result


def calculate_IA(r7, v10, v11):
    '''
    # Example usage
    r7 = "RIGHT CURVE"
    v10 = H1
    v11 = H2
    '''
    
    if r7 == 1:
        if v11 > v10:
            result = v11 - v10
        else:
            result = (360 - v10) + v11
    else:
        if v10 > v11:
            result = v10 - v11
        else:
            result = (360 - v11) + v10
    return result

def calculate_distance(x1, y1, x2, y2):
    # Calculate the distance between two points in Cartesian coordinates
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    distance_x = abs(x2 - x1)
    distance_y = abs(y2 - y1)
    return distance

def calculate_coord_25_XY(stations,BP_XY,BC_XY,EC_XY,O_XY, IP_XY,EP_XY,radius):
    BP_STA = stations[0] #초기 시점STA
    EP_STA = stations[-1]#초기 종점STA
    BC_STA_LIST = []
    EC_STA_LIST = []
    
    coord_list = []
    R= []
    for r in radius:
         R.append(r)
    while 0 in R:
        R.remove(0)
    R = [abs(x) for x in R]
    
    current_station_list = []
    
    for i in range(len(IP_XY)):#IP만큼 반복
        
        bearing1 = calculate_bearingN(BC_XY[i][0],BC_XY[i][1],IP_XY[i][0],IP_XY[i][1])#방위각1
        bearing2 = calculate_bearingN(IP_XY[i][0],IP_XY[i][1],EC_XY[i][0],EC_XY[i][1])#방위각2

        h1 = calculate_bearing(BC_XY[i][0],BC_XY[i][1],IP_XY[i][0],IP_XY[i][1])#각1
        h2 = calculate_bearing(IP_XY[i][0],IP_XY[i][1],EC_XY[i][0],EC_XY[i][1])#각2
        
        BC_O_bearing = calculate_bearing(BC_XY[i][0],BC_XY[i][1],O_XY[i][0],O_XY[i][1])#BC>O방위각
        O_BC_bearing = calculate_bearing(O_XY[i][0],O_XY[i][1],BC_XY[i][0],BC_XY[i][1])#O>BC방위각
        
        
        if i ==0:#시작 IP
            Lb0 = calculate_distance(BP_XY[0], BP_XY[1], IP_XY[i][0], IP_XY[i][1]) #BP-IP거리
            Lb1 = calculate_distance(IP_XY[i][0], IP_XY[i][1], IP_XY[i+1][0], IP_XY[i+1][1]) #IP-EP거리
            IP_STA = BP_STA + Lb0 #IP정측점
            
        elif i == len(IP_XY)-1:#마지막 IP
            Lb0 = calculate_distance(EC_XY[i-1][0], EC_XY[i-1][1], IP_XY[i][0], IP_XY[i][1]) #BC-IP거리
            Lb1 = calculate_distance(IP_XY[i][0], IP_XY[i][1], EP_XY[0], EP_XY[1]) #IP-EP거리
            BP_STA = EC_STA_LIST[i-1]
            IP_STA = BP_STA + Lb0 #IP정측점
            
        else:#나머지 IP
            
            Lb0 = calculate_distance(EC_XY[i-1][0], EC_XY[i-1][1], IP_XY[i][0], IP_XY[i][1]) #BC-IP거리
            Lb1 = calculate_distance(IP_XY[i][0], IP_XY[i][1], EC_XY[i][0], EC_XY[i][1]) #IP-EC거리
            BP_STA = EC_STA_LIST[i-1]
            IP_STA = BP_STA + Lb0 #IP정측점

        

        direction = find_direction(R,bearing1,bearing2)#방향
        IA = calculate_IA(direction, bearing1, bearing2)#교각
        IA_rad = math.radians(IA)
        
        TL = R[i] * math.tan(IA_rad/2)
        CL = R[i] * IA_rad

        
        
        BC_STA = IP_STA - TL
        EC_STA = BC_STA + CL
        
        if i == 0:
            station_list = list(range(int(stations[0]), int(EC_STA)+25, 25))
        elif i == len(IP_XY)-1:
            station_list = list(range(int(BP_STA), int(stations[-1])+25, 25))
        else:
            station_list = list(range(int(BP_STA), int(EC_STA)+25, 25))

        
        '''
        print('BC_O_bearing',BC_O_bearing)
        print('O_BC_bearing',O_BC_bearing)
        print('방위각1= ', degrees_to_dms(bearing1))
        print('방위각2= ', degrees_to_dms(bearing2))
        
        print(Lb0)
        print(Lb1)
        print('IA= ', degrees_to_dms(IA))
        print('TL =',f'{TL:.2f}')
        print('CL =',f'{CL:.2f}')
        
        print('IP정측점 = ',format_distance(IP_STA))
        print('BC측점 = ',format_distance(BC_STA))
        print('EC측점 = ',format_distance(EC_STA))
        
        
        if direction == -1:
            print('좌향곡선')
        else:
            print('우향곡선')
        '''
        BC_STA_LIST.append(BC_STA)
        EC_STA_LIST.append(EC_STA)
        
        for j in range(len(station_list)):
            current_station = station_list[0] + j * 25
            
            if current_station <= BC_STA:#직선구간
                if i ==0 :#초기구간
                    coord = calculate_coordinates(BP_XY[0], BP_XY[1], h1, j*25)
                else:
                    coord = calculate_coordinates(EC_XY[i-1][0], EC_XY[i-1][1], h1, j*25)

            elif current_station > BC_STA and current_station < EC_STA:#단곡선구간
                
                k = (current_station - BC_STA) / 25  # k 계산
                
                delta_angle_rad = k * 25 / R[i]
                delta_angle = math.degrees(delta_angle_rad)

                if direction == 1:
                    delta_bearing = O_BC_bearing - delta_angle
                else:
                    delta_bearing = O_BC_bearing + delta_angle
                        
                    
                
                coord = calculate_coordinates(O_XY[i][0], O_XY[i][1], delta_bearing, R[i])
            elif current_station >= EC_STA and current_station <= stations[-1]:
                if i ==len(IP_XY)-1:
                    l = (current_station - int(EC_STA)) / 25
                    coord = calculate_coordinates(EC_XY[i][0], EC_XY[i][1], h2, l*25)
                    
            else:
                continue

            current_station_list.append(current_station)
            coord_list.append(coord)


    station_list2 = list(range(int(stations[0]), int(stations[-1])+25, 25))

    curve_type5 = []

    BC_STA_LIST = [int(round(x, 2)) for x in BC_STA_LIST]
    EC_STA_LIST = [int(round(x, 2)) for x in EC_STA_LIST]
    
    for current_station in current_station_list:
        if current_station in BC_STA_LIST:
            curve_type5.append('BC')
        elif current_station in EC_STA_LIST:
            curve_type5.append('EC')
        else:
            curve_type5.append(' ')
    curve_type5[0] = 'BP'
    curve_type5[-1] = 'EP'

    return curve_type5, current_station_list, coord_list

def create_csv(curve_type,station_list,coord_list):
    # write the extracted data to CSV
    output_file = r'c:\temp\bve_route_coords.csv'
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        for curve_type, station, coord in zip(curve_type, station_list, coord_list):
            # Convert station to string
            station_str = str(station)
            
            # Convert coord list to a string
            coord_str = ','.join(map(str, coord))
            
            # Write row to CSV file
            writer.writerow([curve_type, station] + list(coord))
        
def toggle_aspect_ratio():
    if aspect_var.get() == 1:
        ax.set_aspect('equal', adjustable='box')
    else:
        ax.set_aspect('auto', adjustable='box')
    canvas.draw()
    

def exit_program():
    print("프로그램을 종료합니다.")
    root.destroy()

def reset_draw():
    print("다시그리기.")
    update_plot()

def reset_values():
    print("초기화.")
    BP_X_entry.delete(0, tk.END)
    BP_X_entry.insert(0, "545358.594887")
    BP_Y_entry.delete(0, tk.END)
    BP_Y_entry.insert(0, "194636.629914")
    BP_azimuth_entry.delete(0, tk.END)
    BP_azimuth_entry.insert(0, '23')
    update_plot()

#25간격으로 표고 계산함수
def calculate_profile_elevation(fl,pitch_station,pitch):

    # 25 간격으로 표고값 계산
    elevations = []
    current_station_list = []

    # Store the ending elevation of the previous segment
    prev_end_elevation = fl
    for i in range(len(pitch_station)-1):
        current_grade = pitch[i]
        start_station = pitch_station[i]
        end_station = pitch_station[i+1]
        station_list = list(range(int(start_station), int(end_station) + 25, 25))

        for j in range(len(station_list)):
            current_station = start_station + j * 25
            if current_station <= end_station:
                length = 25
                height = current_grade / 1000 * length
                if current_station == start_station:  # Check if it's the first station of the segment
                    fl = prev_end_elevation  # Set initial elevation as the ending elevation of the previous segment
                else:
                    fl += height  # Accumulate height to initial elevation fl
                elevations.append(round(fl, 3))  # Round elevation to 6 decimal places
                current_station_list.append(current_station)
        
        # Store the ending elevation of the current segment
        prev_end_elevation = fl
    return current_station_list , elevations

#리스트의 인덱스를 반환
def get_value_from_index(A_LIST,B_LIST,C_LIST):
    indices = []
    values = []
    #A리스트 값에 해당하는 인덱스를 B리스트에서 추출 
    for number in A_LIST:
        try:
            index = B_LIST.index(number)
            indices.append(index)
        except ValueError:
            print(f"index error:Station number {number} not found in list.")
            
            # 오류가 발생하면 건너뜁니다.
            pass
    #B리스트의 인덱스로 C리스트에서 값을 추출
    for index in indices:
        try:
            value = C_LIST[index]
            values.append(value)
        except ValueError:
            print(f"value error:Station number {number} not found in list.")
            # 오류가 발생하면 건너뜁니다.
            pass
    #결과 반환(리스트)
    return values

def remove_duplicates_and_store_indexes(lst):
    unique_list = []
    duplicate_indexes = {}
    
    for i, item in enumerate(lst):
        if item not in unique_list:
            unique_list.append(item)
        else:
            if item not in duplicate_indexes:
                duplicate_indexes[item] = [unique_list.index(item)]
            duplicate_indexes[item].append(i)
    
    # 중복된 요소의 인덱스를 사전 대신에 리스트로 변경
    for key in duplicate_indexes:
        duplicate_indexes[key] = list(set(duplicate_indexes[key]))
    
    return unique_list, duplicate_indexes

def remove_elements_by_indexes(lst, indexes):
    """
    리스트에서 주어진 인덱스의 요소를 제거하는 함수
    :param lst: 요소를 제거할 리스트
    :param indexes: 제거할 요소의 인덱스 리스트
    :return: 없음 (리스트는 직접 수정됨)
    """
    # 인덱스 리스트를 정렬하여 뒤에서부터 제거해야 한 인덱스들이 올바르게 동작함
    
    for index in indexes:
        if index < 0 or index >= len(lst):
            print(f"인덱스 {index}가 유효하지 않습니다.")
        else:
            lst.pop(index)
    return lst

#종단그리기
def draw_profile(values,pitch_station,sta,sta_station):
    # 새로운 subplot을 생성하는 예제

    #지반고
    ground = [0,0]
    bp = (pitch_station[0],0)
    ep = (pitch_station[-1],0)

    #fl 종선
    fl_line = (values,0)
    #종단 스케일 적용400/1000
    factor = 1
    multiplied_list = [element * factor for element in values]

    #종단 계획선
    ax2.scatter(pitch_station,multiplied_list, color='red', marker='',zorder=10)
    ax2.plot(pitch_station,multiplied_list, linestyle='-', color='red')

    #지반고    
    ax2.plot(*zip(*[bp, ep]), linestyle='-', color='BLACK')

    #종단 계획선과 지반고 해칭
    ax2.fill_between(pitch_station, multiplied_list,0, color='#d2b48c', alpha=1, hatch='')

    # 각 계획선의 중심에 기울기 표시
    for i in range(len(pitch_station) - 1):
        x1, y1 = pitch_station[i], multiplied_list[i]
        x2, y2 = pitch_station[i + 1], multiplied_list[i + 1]
        gradient = (y2 - y1) / (x2 - x1) * 1000 # 기울기 계산
        length = pitch_station[i+1] - pitch_station[i]
        if gradient == 0:
            gradient_text = 'L'  # 기울기가 0인 경우 'L'로 설정
        else:
            gradient_text = f'{gradient:.2f}'.rstrip('0').rstrip('.')

        
        midpoint = (x1 + x2) / 2, 40  # 두 점 사이의 중심
        midpoint2 = (x1 + x2) / 2, 25  # 두 점 사이의 중심에서 이격거리
        
        # 기울기를 표시하는 마커 추가
        #midpoint를 지반고y의 중간점으로 
        ax2.text(midpoint[0], midpoint[1], gradient_text, fontsize=15, color='red', ha='center', va='center')

        # 각 계획선의 정점에 y값 표시
        ax2.text(x1, 60, f'{y1:.2f}', fontsize=12, color='red', ha='center', va='center',rotation=90, bbox=dict(facecolor='white', edgecolor='red', boxstyle='square,pad=0.1'))

        # 각 계획선의 중심에 수평연장 표시
        ax2.text(midpoint2[0], midpoint2[1], format_distance(length), fontsize=12, color='red', ha='center', va='center')

        
    # 각 계획선의 정점에서 수직으로 y=0까지 선 추가
    for x, y in zip(pitch_station, multiplied_list):
        ax2.plot([x, x], [y, 0], linestyle='-', color='red')

    #역에 해당하는 표고 찾기
    sta_elev = interpolate_coordinates(pitch_station, multiplied_list, sta_station)
    
    # 종단뷰에 역명 추가
    for i in range(len(sta_station)):
        if sta_elev[i] is not None:
            ax2.text(sta_station[i], sta_elev[i] + 200, sta[i], fontsize=10, color='black', ha='center', va='center',
                     rotation=90, bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.2'))
            #역명에서 계획선까지 수직선 추가
            ax2.plot([sta_station[i], sta_station[i]], [sta_elev[i] + 200, sta_elev[i]], linestyle='-', color='black')

            
def interpolate_coordinates(x, y, target_x):
    # target_x가 리스트인 경우 각 요소에 대해 보간 함수를 적용하고 결과를 리스트에 저장
    if isinstance(target_x, list):
        interpolated_values = []
        for tx in target_x:
            # 보간할 x 좌표가 기존 x 범위를 벗어나면 보간을 수행하지 않음
            if tx < x[0] or tx > x[-1]:
                interpolated_values.append(None)
            else:
                # 보간 함수 계산
                interp_func = np.interp(tx, x, y)
                interpolated_values.append(interp_func)
        return interpolated_values
    # target_x가 단일 값인 경우
    else:
        # 보간할 x 좌표가 기존 x 범위를 벗어나면 보간을 수행하지 않음
        if target_x < x[0] or target_x > x[-1]:
            return None
        else:
            # 보간 함수 계산
            interp_func = np.interp(target_x, x, y)
            return interp_func

def find_station_coordinates(current_station_list, coord_list,values):
    # 콤보 박스 생성 및 옵션 설정
    combobox = ttk.Combobox(root)
    combobox.config(height=5)           # 높이 설정
    combobox.config(values=current_station_list)           # 나타낼 항목 리스트 설정
    combobox.config(state="normal")   # 콤보 박스에 사용자가 직접 입력 불가
    combobox.current(0)                 # 초기 선택값 설정 (첫 번째 항목)
    combobox.grid(row=3, column=2)
    
    # scatter 객체를 추적하기 위한 변수
    global scatter4, scatter5, scatter6
    scatter4 = None #평면 x
    scatter5 = None #종단 x
    scatter6 = None #종단 x선

    def update_text():
               
        # 콤보 상자에서 현재 선택된 측정치 가져오기
        current_station = combobox.get()
        global scatter4, scatter5, scatter6

        try:
            # 현재 선택된 측정치의 인덱스 찾기
            index = current_station_list.index(int(current_station))
            
            current_station = int(current_station)
            
            # 텍스트 레이블 업데이트
            text_station = "현재 측점 = " + format_distance(current_station)
            text_label_station.config(text=text_station)

            # 좌표를 소수점 4자리까지 표시
            coord_str = "(" + ", ".join(["{:.4f}".format(coord) for coord in coord_list[index]]) + ")"
            text_coord = "현재 좌표= " + coord_str
            text_label_coord.config(text=text_coord)

            #표고  업데이트
            text_elevation = "현재 표고 = " + str(values[index])
            text_label_elevation.config(text=text_elevation)
            
            #현재 좌표에 점 생성
            # scatter 객체 제거
            if scatter4:
                scatter4.remove()
            if scatter5:
                scatter5.remove()
            if scatter6:
                scatter6.remove()

            # 수직선의 y 좌표 범위 (무한대로 설정)
            y_min = -np.inf
            y_max = np.inf
            scatter4 = ax.scatter(coord_list[index][0],coord_list[index][1],color='red',marker='x',s=50,zorder=10)
            scatter5 = ax2.scatter(current_station,values[index],color='red',marker='x',s=50,zorder=10)
            scatter6 = ax2.axvline(x=current_station, color='gray', linestyle='--')
            canvas.draw()  # Redraw the plot
            
        except ValueError:
            print("Error: Selected station not found in the list.")

    # 텍스트 레이블 생성
    text_label_station = tk.Label(root, bg=root.cget('bg'), fg="black")
    text_label_station.place(x=800, y=150)

    text_label_coord = tk.Label(root, bg=root.cget('bg'), fg="black")
    text_label_coord.place(x=800, y=170)

    text_label_elevation = tk.Label(root, bg=root.cget('bg'), fg="black")
    text_label_elevation.place(x=800, y=190)
    
    # 초기화 및 갱신 버튼 생성
    update_button = tk.Button(root, text="Update", command=update_text)
    update_button.place(x=650, y=80)

# 마우스 더블 클릭 이벤트 핸들러 함수 정의
def on_double_click(event):
    if event.dblclick:
        # 더블 클릭된 위치
        x = event.xdata
        y = event.ydata
        
        # 화면 확대를 위해 새로운 축 범위 설정
        ax.set_xlim(x - 5, x + 5)  # x 좌표를 중심으로 5의 범위 확대
        ax.set_ylim(y - 5, y + 5)  # y 좌표를 중심으로 5의 범위 확대
        
        # 그래프 다시 그리기
        canvas.draw()
        
#메인함수
def update_plot(event=None):
    
    global lines
    

    
    
    ax.clear()
    
    BP_XY = (float(BP_Y_entry.get()),float(BP_X_entry.get()))
    BP_bearing = float(BP_azimuth_entry.get())

    fl = float(fl_entry.get())
    
    
   
    
    
    
    
    
    stations, radius, sta_station,sta,pitch_station,pitch = parse_track(lines)

    direction = define_dirction(radius)
    
    
    curve_type = calculate_curve_type(stations,radius)
    interval_distance = calculate_interval_distance(stations,radius)
    O_XY, BC_XY, EC_XY, EP_XY,IP_XY = calculate_coord(BP_XY, BP_bearing, stations, radius, curve_type, interval_distance)

    x_arcs = {}  # 변수를 저장할 딕셔너리 생성
    y_arcs = {}
    acr1 = []
    acr2 = []

    # 그래프에 호를 그림
    for i in range(len(BC_XY)):
        
        key = f'x_arc{i+1}'  # 변수명 생성
        x_arcs[key],y_arcs[key] = draw_arc(direction[i],BC_XY[i], EC_XY[i], O_XY[i])  # 변수에 할당
        ax.plot(x_arcs[key], y_arcs[key], label='선형', color='RED')
        acr1.append(x_arcs[key])
        acr2.append(y_arcs[key])
        
        
        if i < len(BC_XY) - 1:  # EC_XY의 마지막 요소가 BC_XY의 마지막 요소보다 하나 적으므로 이를 고려
            ax.plot(*zip(*[BC_XY[i+1],EC_XY[i]]), linestyle='-', color='blue')

        


                
        #복심곡선이 아닌 노선
        if not 'PCC' in curve_type:
            ax.text(*BC_XY[i], 'BC= '+ format_distance(stations[2 * i + 1]), fontsize=12, ha='left',color='red')
            ax.text(*EC_XY[i], 'EC= '+ format_distance(stations[2 * i + 2]), fontsize=12, ha='left',color='red')
            ax.scatter(*zip(*[BC_XY[i], EC_XY[i]]), color='red', marker='',zorder=10)

    #복심곡선 노선
    if 'PCC' in curve_type:
        print('복심곡선 존재')
        stations2 = stations.copy() #원본 복사
        curve_type2 = curve_type.copy() #원본 복사
        curve_type3 = [] #수정본 저장 리스트
    
        del stations2[0]
        del stations2[-1]
    
        del curve_type2[0]
        del curve_type2[-1]
    
        for a in curve_type2:
            if a == 'PCC':
                curve_type3.append('EC')
                curve_type3.append('BC')
            else:
                curve_type3.append(a)
        
        for i, j in enumerate(curve_type2):
            if j == 'PCC':
                stations2.insert(i+1, stations2[i])  # 현재 인덱스 다음에 현재 인덱스의 값을 추가
            else:
                pass
        
        poly_XY = [item for pair in zip(BC_XY, EC_XY) for item in pair]
        
        for i in range(len(stations2)):
            if curve_type3[i] == 'BC':
                ax.text(*poly_XY[i], f'BC= {format_distance(stations2[i])}', fontsize=12, ha='left', color='red')
            elif curve_type3[i] == 'EC':
                ax.text(*poly_XY[i], f'EC= {format_distance(stations2[i])}', fontsize=12, ha='right', color='red')
            else:
                pass
            ax.scatter(*poly_XY[i], color='red', marker='',zorder=10)    
    

   
    #리스트 단일화
    acr1 = [item for sublist in acr1 for item in sublist]
    acr2 = [item for sublist in acr2 for item in sublist]
    
    
    #시작과 끝
    ax.plot(*zip(*[BP_XY,BC_XY[0]]), linestyle='-', color='BLACK')
    ax.plot(*zip(*[EC_XY[-1],EP_XY]), linestyle='-', color='BLACK')
    
    ax.text(*BP_XY, 'BP= '+ format_distance(stations[0]), fontsize=12, ha='left',color='BLACK')
    ax.text(*EP_XY, 'EP= '+ format_distance(stations[-1]), fontsize=12, ha='left',color='BLACK')

    
    # 폰트 설정
    custom_font = ("굴림체", 12)  # 폰트 및 크기 지정
    
    # 텍스트 레이블 생성 윈도우창
    text = "BP STA = "+ format_distance(stations[0])# Change "Other Text" to whatever you want for direction not equal to 1
    text_label = tk.Label(root, text=text, bg=root.cget('bg'), fg="black", font=custom_font)
    text_label.place(x=650, y=40)

    # 텍스트 레이블 생성 윈도우창
    text = "EP STA = "+ format_distance(stations[-1])# Change "Other Text" to whatever you want for direction not equal to 1
    text_label = tk.Label(root, text=text, bg=root.cget('bg'), fg="black", font=custom_font)
    text_label.place(x=800, y=40)

    
    
    
    #초기화버튼 생성
    reset_button = tk.Button(root, text="초기화", command=reset_values)
    reset_button.grid(row=2, column=2, pady=10)

    # 다시그리기 버튼 생성
    redraw_button = tk.Button(root, text="다시그리기", command=reset_draw)
    redraw_button.grid(row=2, column=1, pady=10)
    
    # 종료 버튼 생성
    exit_button = tk.Button(root, text="종료", command=exit_program)
    exit_button.grid(row=2, column=0, pady=10)

    #초기 버튼 생성
    reread_button = tk.Button(root, text="다른 파일 열기", command=read_other_file)
    reread_button.grid(row=2, column=3, pady=10)

    canvas.draw()  # Redraw the plot

    #좌표출력함수
    curve_type5, current_station_list, coord_list = calculate_coord_25_XY(stations,BP_XY,BC_XY,EC_XY,O_XY, IP_XY,EP_XY,radius)

    
    #정거장 구현
    n_station_list = list(range(int(stations[0]), int(stations[-1])+25, 25))
    
    station_coordinates = get_value_from_index(sta_station,n_station_list,coord_list)

    for i in range(len(station_coordinates)):
        ax.scatter(*station_coordinates[i], color='blue', marker='o',zorder=10)
        ax.text(*station_coordinates[i], sta[i], fontsize=12, ha='left', color='blue')
    #csv 저장함수
    create_csv(curve_type5,current_station_list,coord_list)

    #dxf 저장함수
    create_dxf("example_polyline.dxf", coord_list, current_station_list,curve_type5)
    #KML저장용
    
    if 'PCC' in curve_type:#복심곡선용
        stations3 = stations2.copy()
        stations3.insert(0,stations[0])
        stations3.append(stations[-1])
        curve_type4 = curve_type3.copy()
        curve_type4.insert(0,curve_type[0])
        curve_type4.append('EP')
        poly_XY2 = poly_XY.copy()
        poly_XY2.insert(0,BP_XY)
        poly_XY2.append(EP_XY)
        Create_KML2(acr1,acr2,poly_XY2,stations3,curve_type4)
        
    else:#일반용
        Create_KML(BP_XY,EP_XY,acr1,acr2,BC_XY,EC_XY,stations)

    #종단뷰 생성
    
    
    
    v_station_list , elevations = calculate_profile_elevation(fl, pitch_station,pitch)
    vip_elev_list = get_value_from_index(pitch_station,v_station_list,elevations)
    draw_profile(vip_elev_list,pitch_station,sta,sta_station)
        
    #좌표 찾기
    unique_values,duplicate_indexes = remove_duplicates_and_store_indexes(v_station_list)
    duplicate_indexes = list(duplicate_indexes.values())
    duplicate_indexes = [sublist[0] for sublist in duplicate_indexes]
    modifed_lst = remove_elements_by_indexes(elevations, duplicate_indexes)

    find_station_coordinates(unique_values, coord_list,modifed_lst)
    
    # 툴바 추가
    # NavigationToolbar2Tk를 사용하여 그래프 위젯에 툴바 추가
    # Create a frame to contain both the canvas and the toolbar
    toolbar_frame = tk.Frame(root)
    toolbar_frame.grid(row=5, columnspan=2)

    toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
    toolbar.update()
    toolbar.grid(row=0, column=0, sticky="we") 

    # Run the GUI
    root.geometry("1024x800")

    root.mainloop()

root = tk.Tk()
root.title("openbve 선형뷰어")

# Initialize the plot
fig = plt.figure(figsize=(8,6))  # 가로 800픽셀, 세로 600픽셀 크기의 도표 생성

ax = fig.add_subplot(2,1,1)
ax2 = fig.add_subplot(2,1,2)
ax2.set_aspect(aspect=2.5)

ax2.set_xlim(0, 1000)
ax2.set_ylim(-50, 100)

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=6, columnspan=2)

fig.canvas.mpl_connect('button_press_event', on_double_click)

ax.set_title('선형개요도')
ax.set_xlabel('X-axis')
ax.set_ylabel('Y-axis')
ax.grid(True)


tk.Label(root, text="BP X:").grid(row=0, column=0, sticky="e")
BP_X_entry = tk.Entry(root)
BP_X_entry.grid(row=0, column=1)
BP_X_entry.insert(0, "545358.594887")
BP_X_entry.bind('<KeyRelease>', update_plot)

tk.Label(root, text="BP Y:").grid(row=0, column=1, sticky="e")
BP_Y_entry = tk.Entry(root)
BP_Y_entry.grid(row=0, column=2)
BP_Y_entry.insert(0, "194636.629914")
BP_Y_entry.bind('<KeyRelease>', update_plot)

tk.Label(root, text="BP 방위각:").grid(row=1, column=0, sticky="e")
BP_azimuth_entry = tk.Entry(root)
BP_azimuth_entry.grid(row=1, column=1)
BP_azimuth_entry.insert(0, '90')
BP_azimuth_entry.bind('<KeyRelease>', update_plot)

tk.Label(root, text="계획고:").grid(row=3, column=0, sticky="e")
fl_entry = tk.Entry(root)
fl_entry.grid(row=3, column=1)
fl_entry.insert(0, "100")
fl_entry.bind('<KeyRelease>', update_plot)

aspect_var = tk.IntVar(value=0)
# Create the checkbox
aspect_checkbox = tk.Checkbutton(root, text="비율 동일하게", variable=aspect_var, command=toggle_aspect_ratio)
aspect_checkbox.grid(row=0, column=3, columnspan=2, pady=10)
    
def main():
    print("프로그램 시작")
    
    global lines
    lines = read_file()
    lines = preprocess_line(lines)
    
    update_plot()
    
if __name__ == '__main__':
    main()
