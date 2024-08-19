import random
from shapely.geometry import Point, LineString
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk  # 추가
import numpy as np
from math import cos, sin, atan2, degrees, radians, pi
import math
from tkinter import filedialog, Tk, StringVar, ttk
import tkinter as tk
import simplekml
import pyproj
import os
import numpy as np
from geopy.geocoders import Nominatim
import ezdxf
import time
from matplotlib.figure import Figure
from random import randint

plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False

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

def ensure_layer(doc, layer_name, color_index):
    """Ensure that a layer exists with a specific color."""
    layers = doc.layers
    if layer_name not in layers:
        layers.add(name=layer_name, color=color_index)

def add_arc(msp, center, radius, start_angle, end_angle, layer, color_index):
    """Add an arc to the modelspace."""
    if start_angle > end_angle:
        start_angle, end_angle = end_angle, start_angle
        end_angle += 360
    else:
        end_angle += 360 if end_angle < start_angle else 0
    
    msp.add_arc(
        center=center,
        radius=radius,
        start_angle=start_angle,
        end_angle=end_angle,
        dxfattribs={'color': color_index, 'layer': layer}
    )
    
def create_dxf(filename, linestring,BC,EC,O,R,DR):
    doc = ezdxf.new()
    msp = doc.modelspace()

    # Create a polyline entity
    coordinates = list(linestring.coords)
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
    ##IP라인 코드##
    # Set polyline properties if needed
    layers = doc.layers
    
    polyline.dxf.layer = 'IP라인'

    if 'FL' not in layers:
        layers.add(name='FL', color=1)  # 레이어 'Layer1' 생성, 색상은 Cyan (3)
    if 'IP문자' not in layers:
        layers.add(name='IP문자', color=9)  # 레이어 'Layer1' 생성, 색상은 Cyan (3)
        
    # Set the color of the polyline to red
    red_color_index = 7  # Get color index for 'red'
    polyline.dxf.color = red_color_index
    
    text_color_index = 7
    text_height = 3

    # Add labels for each point
    for i, point in enumerate(coordinates):
        if i == 0:
            label = 'BP'
            msp.add_text(label, dxfattribs={'insert': point, 'height': text_height, 'color': 7,'layer': 'IP문자'})
        elif i == len(coordinates) - 1:
            label = 'EP'
            msp.add_text(label, dxfattribs={'insert': point, 'height': text_height, 'color': 7,'layer': 'IP문자'})
        else:
            label = f'IP.NO{i}'
            msp.add_text(label, dxfattribs={'insert': point, 'height': text_height, 'color': 7,'layer': 'IP문자'})

    ##선형 코드##      
    #호 그리기
    for BC_XY,EC_XY,O_XY,R,direction in zip(BC,EC,O,R,DR):
        # Calculate start and end angles
        center_point = O_XY
        start_point = BC_XY
        end_point = EC_XY
        radius = R
        start_angle = angle_from_center(center_point, start_point)
        end_angle = angle_from_center(center_point, end_point)
        
        # Adjust angles to be in [0, 360) range
        start_angle = start_angle if start_angle >= 0 else start_angle + 360
        end_angle = end_angle if end_angle >= 0 else end_angle + 360

        
        # 호 생성하기
        if direction == 1:  # 시계 방향
            if end_angle > start_angle:
                end_angle -= 360
        elif direction == -1:  # 반시계 방향
            start_angle, end_angle = end_angle, start_angle  # 각도를 반대로
            if end_angle > start_angle:
                end_angle -= 360
            start_angle -= 360  # 반시계 방향으로 회전하기 위해 추가 조정

        # Add the arc to the DXF document
        msp.add_arc(
            center=center_point,
            radius=radius,
            start_angle=end_angle,
            end_angle=start_angle,
            dxfattribs={'color': 1 ,'layer': 'FL'}
            )

    #호 사이 직선
    for i in range(len(BC) - 1):
        try:
            # Debug print to check types and values
            

            start_point = BC[i+1]
            end_point = EC[i]
            
            # Add the line to the modelspace
            msp.add_line(start=start_point, end=end_point, dxfattribs={'color': 1,'layer': 'FL'})

        except Exception as e:
            print(f"Error drawing line from {start_point} to {end_point}: {e}")    # Save the DXF document to a file
    #시작,끝 직선
    fs = coordinates[0]
    fe = BC[0]
    es = EC[-1]
    ee = coordinates[-1]
    msp.add_line(start=fs, end=fe, dxfattribs={'color': 1,'layer': 'FL'})#시작선
    msp.add_line(start=es, end=ee, dxfattribs={'color': 1,'layer': 'FL'})#끝선
    
    file_dir = 'C:/TEMP/랜덤선형성과/도면/' + filename
    
    save_with_retry(doc, file_dir)
    
def save_with_retry(doc, filename, max_retries=100, delay=1):
    # Ensure the directory exists
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Try saving the file, retrying if there's a PermissionError
    for attempt in range(max_retries):
        try:
            doc.saveas(filename)
            print(f"File saved successfully: {filename}")
            break
        except PermissionError:
            print(f"Attempt {attempt + 1}: Permission denied while saving {filename}. Retrying in {delay} seconds...")
            time.sleep(delay)
    else:
        print(f"Failed to save the file after {max_retries} attempts.")
        
def angle_from_center(center, point):
    cx, cy = center
    px, py = point
    return math.degrees(math.atan2(py - cy, px - cx))

def arc_length(radius, start_angle, end_angle):
    # Normalize angles to be within 0-360 degrees
    delta_angle = (end_angle - start_angle) % 360
    if delta_angle > 180:
        delta_angle -= 360
    return abs(delta_angle) / 360 * 2 * math.pi * radius


def calculate_O_PC_angle(v10, x10, direction):
    '''
    # Example usage
    v10 = 방위각1
    x10 = PC점의 점선각
    w13 = R
    '''
    if direction > 0:
        if v10 + x10 - 90 < 0:
            result = v10 + x10 - 90 + 360
        else:
            result = v10 + x10 - 90
    else:
        if v10 - x10 + 90 > 360:
            result = v10 - x10 + 90 - 360
        else:
            result = v10 - x10 + 90
    return result


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

def calculate_north_bearing(x1, y1, x2, y2):
    # Calculate the bearing (direction) between two points in Cartesian coordinates
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.degrees(math.atan2(dx, dy))
    if bearing < 0:
        bearing = bearing + 360
    else:
        bearing
    return bearing

def calculate_distance(x1, y1, x2, y2):
    # Calculate the distance between two points in Cartesian coordinates
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    distance_x = abs(x2 - x1)
    distance_y = abs(y2 - y1)
    return distance

def calculate_simple_curve(linestring,radius_list,angles):

    O_XY_list = []
    BC_XY_list = []
    EC_XY_list = []
    BC_STA_LIST = []
    EC_STA_LIST = []
    TL_list = []
    
    direction_list = []
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
            IP_STA = BP_STA + Lb0 #ip정측점
        else:
            X16 =  TL_list[i-1]
            BP_STA = EC_STA_LIST[i-1]
            IP_STA = BP_STA + Lb0 - X16
        
        
        BC_XY = calculate_destination_coordinates(IP_XY[0], IP_XY[1], BP_IP_BEARING, -TL)

        direction = find_direction(radius_list[i], h1, h2)
        O_PC_ANGLE = calculate_O_PC_angle(h1, math.degrees(0), direction)

        CURVE_CENTER_XY = (math.sin((O_PC_ANGLE + 180) * math.pi / 180) * radius_list[i] + BC_XY[0],
                           math.cos((O_PC_ANGLE + 180) * math.pi / 180) * radius_list[i] + BC_XY[1])

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

        
        #테스트코드
        #print(f'IP{i+1} BC:{BC_STA},EC:{EC_STA}')
        #print(f'IP_STA:{IP_STA}')

     
    return BC_XY_list, EC_XY_list, O_XY_list,direction_list,BC_STA_LIST,EC_STA_LIST


# TM좌표를 경위도 좌표로 변환함수(좌표배열)
def calc_pl2xy_array(coords_array):
    transformed_coords = []

    # Define CRS
    p1_type = pyproj.CRS.from_epsg(5186)  # TM
    p2_type = pyproj.CRS.from_epsg(4326)  # 위도

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

def calculate_angle(p1, p2):
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    return atan2(dy, dx)

def calculate_inner_angle(v1, v2):
    angle1 = atan2(v1[1], v1[0])
    angle2 = atan2(v2[1], v2[0])
    angle_diff = abs(angle2 - angle1)
    if angle_diff > pi:
        angle_diff = 2 * pi - angle_diff
    return degrees(angle_diff)

def generate_random_point_near(point, end, min_distance, max_distance):
    angle_to_end = calculate_angle(point, end)
    while True:
        angle = random.uniform(angle_to_end - radians(90), angle_to_end + radians(90))
        distance = random.uniform(min_distance, max_distance)
        x = point.x + distance * cos(angle)
        y = point.y + distance * sin(angle)
        new_point = Point(x, y)

        # Check if the new point is in the direction of the end point
        if new_point.distance(end) < point.distance(end):
            return new_point

def generate_random_linestring_within_radius(start, end, max_points, min_distance, max_distance, min_end_distance=2000):
    points = [start]
    while True:
        if len(points) >= max_points:
            break

        new_point = generate_random_point_near(points[-1], end, min_distance, max_distance)

        if new_point.distance(points[-1]) <= max_distance:
            points.append(new_point)

        if new_point.distance(end) <= min_end_distance:
            break

    points.append(end)
    return LineString(points)

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

def adjust_linestring(line_string, angles):
    new_points = [line_string.coords[0]]  # Start with the first point
    for i in range(1, len(line_string.coords) - 1):
        if angles[i - 1] <= 60:
            new_points.append(line_string.coords[i])
    new_points.append(line_string.coords[-1])  # End with the last point
    return LineString(new_points)

def get_random_color():
    R =randint(0,255)
    G = randint(0,255)
    B = randint(0,255)
    A = 255
    
    return f"{A:02x}{B:02x}{G:02x}{R:02x}"

def create_kml(filename, point_list):  # kml작성함수
    kml = simplekml.Kml()

    # Convert coordinates to latitude and longitude
    point_list_latlong = calc_pl2xy_array(point_list)

    # Get a random color in ABGR format
    kmlcolor = get_random_color()
    
    # Create a single linestring to connect all points
    linestring = kml.newlinestring(name="Sample Polyline", coords=point_list_latlong)
    linestring.style.linestyle.color = kmlcolor
    linestring.style.linestyle.width = 4

    # Save the KML file
    # 디렉토리가 없는 경우 생성
    workdiretory = 'C:/TEMP/랜덤평면선형성과/KMZ/'
    
    if not os.path.exists(workdiretory):
        os.makedirs(workdiretory)
        
    kml_file = workdiretory + filename
    kml.save(kml_file)

    # Open the saved KML file
    #os.system(f'start {kml_file}')  # This command works on Windows

def get_random_radius(min_radius, max_radius):
    # min_radius와 max_radius 사이의 가장 작은 1000의 배수 구하기
    start = (min_radius + 1000) // 1000 * 1000
    end = (max_radius // 1000) * 1000

    if start > end:
        raise ValueError("min_radius와 max_radius 사이에 유효한 1000의 배수가 없습니다.")
    
    # start와 end 사이의 1000의 배수 목록 생성
    multiples_of_1000 = list(range(start, end + 1000, 1000))
    
    # 랜덤하게 선택
    return random.choice(multiples_of_1000)

def adjust_radius_by_angle(IA, min_radius, max_radius):
    # 교각이 작을수록 반경을 크게, 교각이 클수록 반경을 작게 설정
    while 1:
        if IA < 3:
            new_radius = get_random_radius(min_radius * 2, max_radius) # 교각이 1도일 때 반경을 크게
        else:
            new_radius = get_random_radius(min_radius, int(max_radius/2)) # 교각이 30도 이상일 때 반경을 작게

        if new_radius>0:
            break
        
    return new_radius

def format_cost(cost):
    """
    Format the cost into 'X조Y억원' format.
    """
    trillion = cost // 10000 # 조 단위 계산
    billion = (cost % 10000) # 억 단위 계산
    
    if trillion > 0:
        if billion > 0:
            return f'{trillion:.0f}조{billion:.0f}억원'
        else:
            return f'{trillion:.0f}조'
    else:
        return f'{billion:.0f}억원'

def get_coordinates(location_name):
    # Nominatim 인스턴스 생성
    geolocator = Nominatim(user_agent = 'South Korea')
    
    # 주소 검색
    location = geolocator.geocode(location_name)
    
    if location:
        return (location.latitude, location.longitude)
    else:
        return None
    
#경위도를 TM좌표로 변환함수(좌표)
    #arg 튜플(x,y)
def calc_pl2xy(longlat):
    (long,lat) = longlat
    p1_type = pyproj.CRS.from_epsg(4326)
    p2_type = pyproj.CRS.from_epsg(5186)
    transformer = pyproj.Transformer.from_crs(p1_type, p2_type, always_xy=True)
    x, y = transformer.transform(long, lat)
    
    return x, y  # [m]

def point_on_line(P, Q, T):
    # P, Q, T는 각각 (x, y) 형태의 튜플로 가정
    px, py = P
    qx, qy = Q
    tx, ty = T

    # 외적을 사용하여 점 T가 직선 PQ 위에 있는지 확인
    if abs((qy - py) * (tx - px) - (ty - py) * (qx - px)) >= max(abs(qx - px), abs(qy - py)):
        return 0

    # 점 T가 선분 PQ의 연장선 위에 있지만 선분의 양 끝 점 사이에 있는 경우
    if (qx < px and px < tx) or (qy < py and py < ty):
        return 1
    if (tx < px and px < qx) or (ty < py and py < qy):
        return 1
    if (px < qx and qx < tx) or (py < qy and qy < ty):
        return 3
    if (tx < qx and qx < px) or (ty < qy and qy < py):
        return 3

    # 점 T가 직선 PQ 위에 있는 경우
    return True

## Define start and end points
# 테스트할 지명 입력
def get_valid_coordinates(prompt):
    while True:
        location_name = prompt
        coordinates = get_coordinates(location_name)
        
        if coordinates is None:
            print("유효한 지명을 입력해주세요.")
        else:
            return coordinates,location_name





#경유지 로직
def input_passpoints(ispasspoint):
    passpoint_coordinates = []
    passpoint_name_list = []
    i = 0
    
    while True:
        
        if ispasspoint == 0:  # 사용자에게 경유지 입력을 중단할 옵션 제공
            print('경유지를 생략합니다.')
            return passpoint_coordinates, passpoint_name_list
        else:
            passpoint_coordinate, passpoint_name = get_valid_coordinates(str(input("경유지 입력: ")))
            print(f"경유지: {passpoint_name} = {passpoint_coordinate}")
            pass_point = Point(calc_pl2xy((passpoint_coordinate[1], passpoint_coordinate[0])))
            passpoint_coordinates.append(pass_point)
            passpoint_name_list.append(passpoint_name)
            
            i += 1
            continue_input = int(input("계속해서 입력하려면 1을 입력하세요. 경유지 입력 종료는 0 입력: "))

            if continue_input == 0:
                print(f'경유지 입력이 종료되었습니다. 입력 갯수: {i}')
                return passpoint_coordinates, passpoint_name_list


def is_approximately_equal(a, b, tolerance=1e-5):
    return abs(a - b) < tolerance

def adjust_radius(radius_list, index, decrement=500):
    new_radius = radius_list[index] - decrement
    return max(new_radius, 600)  # 반경이 600 이하로 내려가지 않도록 제한

def check_last_ip_ep(adjusted_linestring, EC_XY, radius_list):
    last_IP = adjusted_linestring.coords[-2]
    EP = adjusted_linestring.coords[-1]
    last_IP_EP_bearing = calculate_bearing(last_IP[0], last_IP[1], EP[0], EP[1])
    EC_EP_bearing = calculate_bearing(EC_XY[-1][0], EC_XY[-1][1], EP[0], EP[1])

    if is_approximately_equal(last_IP_EP_bearing, EC_EP_bearing):
        #print(f'IP-EP 방위각 = {last_IP_EP_bearing}')
        #print(f'EC-EP 방위각 = {EC_EP_bearing}')
        return False
    else:
        radius_list[-1] = adjust_radius(radius_list, -1)
        #print('경고: 마지막 곡선과 종점 겹침')
        #print(f'마지막 반경: {radius_list[-1]}')
        return True
    
def cal_EP_STA(adjusted_linestring,EC_XY,EC_STA_LIST):
    LAST_EC_XY = EC_XY[-1]
    EP = adjusted_linestring.coords[-1]
    EC_EP_dist = calculate_distance(LAST_EC_XY[0],LAST_EC_XY[1],EP[0],EP[1])
    EC_STA = EC_STA_LIST[-1]
    EP_STA = EC_STA + EC_EP_dist
    return EP_STA
    

def main_loop(adjusted_linestring, radius_list, new_angles,min_arc_to_arc_distance):
    j = 0

    while True:
        #print(f'루프 {j}회차')
        BC_XY, EC_XY, O_XY, direction, BC_STA_LIST, EC_STA_LIST = calculate_simple_curve(adjusted_linestring, radius_list, new_angles)
        CL_LIST = [ec - bc for ec, bc in zip(EC_STA_LIST, BC_STA_LIST)]
        EP_STA = cal_EP_STA(adjusted_linestring, EC_XY, EC_STA_LIST)
        isCurveOverlap_list = []
        
        #print(f'BP  = 0km000.00\n')
        
        for i in range(len(BC_STA_LIST)):
            
            #print(f'현재 IP{i+1}')
            
            if i == len(BC_STA_LIST) - 1:  # 마지막 인덱스 처리
                max_R = max(radius_list[i - 1], radius_list[i])
                bc_to_ec_dist = EP_STA - EC_STA_LIST[i]
            else:  # 그 외의 경우
                max_R = max(radius_list[i - 1], radius_list[i], radius_list[i + 1])
                bc_to_ec_dist = BC_STA_LIST[i + 1] - EC_STA_LIST[i]
           
            #print(f'BC = {format_distance(BC_STA_LIST[i])}, EC = {format_distance(EC_STA_LIST[i])}, R = {radius_list[i]}')

            
            #첫번째 곡선 겹침체크
            if BC_STA_LIST[0] < 0:
                #print(f'BP와 IP1번 곡선 겹침 L= {BC_STA_LIST[0]}m')
                radius_list[0] = adjust_radius(radius_list, 0)
                
            if BC_STA_LIST[0] < min_arc_to_arc_distance:
                #print(f'경고: BP와 IP1번간의 거리 {BC_STA_LIST[0]}m는 {min_arc_to_arc_distance}m 미만입니다.')
                
                radius_list[0] = adjust_radius(radius_list, 0)
            
            if bc_to_ec_dist > 0:  # 겹치지 않은 경우
                if bc_to_ec_dist < min_arc_to_arc_distance:  # 최소 곡선 거리보다 작은 경우

                    #EP체크
                    if i == len(BC_STA_LIST) - 1:
                        pass#print(f'경고: IP{i + 1}번과 EP간의 거리 {bc_to_ec_dist:.2f}m는 {min_arc_to_arc_distance}m 미만입니다.')
                    else:
                        pass#print(f'경고: IP{i + 2}번과 IP{i + 1}번간의 거리 {bc_to_ec_dist:.2f}m는 {min_arc_to_arc_distance}m 미만입니다.')
                        
                    if max_R == radius_list[i - 1]:
                        radius_list[i - 1] = adjust_radius(radius_list, i - 1)
                    elif max_R == radius_list[i]:
                        radius_list[i] = adjust_radius(radius_list, i)
                    elif i != len(BC_STA_LIST) - 1 and max_R == radius_list[i + 1]:
                        radius_list[i + 1] = adjust_radius(radius_list, i + 1)
                    else:
                        print('error')
                    isCurveOverlap_list.append(True)
                else:
                    isCurveOverlap_list.append(False)
            else:
                #print(f'IP{i + 1}번과 IP{i + 2}번 곡선 겹침 L= {bc_to_ec_dist}')
                
                if max_R == radius_list[i - 1]:
                    radius_list[i - 1] = adjust_radius(radius_list, i - 1)
                elif max_R == radius_list[i]:
                    radius_list[i] = adjust_radius(radius_list, i)
                elif i != len(BC_STA_LIST) - 1 and max_R == radius_list[i + 1]:
                    radius_list[i + 1] = adjust_radius(radius_list, i + 1)
                else:
                    print('error')
                isCurveOverlap_list.append(True)

        #print(f'EP  = {format_distance(EP_STA)}\n')
        islastoverlap = check_last_ip_ep(adjusted_linestring, EC_XY, radius_list)
        
        if all(not overlap for overlap in isCurveOverlap_list) and not islastoverlap:
            print(f'루프 {j}회차 종료\n')
            break
        
        if j >200:
            print(f'루프 {j}회차 종료. 곡선반경 조정 실패')
            break
        
        j += 1
        #print('---------------------------------------------------')

    return BC_XY, EC_XY, O_XY, direction, BC_STA_LIST, EC_STA_LIST, EP_STA

def is_number(s):
    """Check if the string s represents a number."""
    try:
        float(s)
        return True
    except ValueError:
        return False

    
def process_coordinates(start_station, end_station):
    """Process start and end coordinates and return Points."""
    # Initialize variables
    start_coordinates, start_name = None, None
    end_coordinates, end_name = None, None

    # Check if start_station and end_station are numbers
    if is_number(start_station):
        start_coordinates = start_station # Adjust this if needed
        start_name = f'BP'
    else: 
        start_coordinates, start_name = get_valid_coordinates(start_station)
    
    if is_number(end_station):
        end_coordinates = end_station # Adjust this if needed
        end_name = f'EP'
        
    else:
        end_coordinates, end_name = get_valid_coordinates(end_station)

    if start_coordinates is None or end_coordinates is None:
        raise ValueError("Failed to determine valid coordinates for start or end points.")

    print(f"시작 좌표: {start_name} : {start_coordinates}")
    print(f"종료 좌표: {end_name} : {end_coordinates}")

    # Convert coordinates to Points
    start_point = Point(calc_pl2xy((start_coordinates[1], start_coordinates[0])))
    end_point = Point(calc_pl2xy((end_coordinates[1], end_coordinates[0])))
    
    return start_point, end_point

def initialize_parameters():
    global max_points, min_distance, max_distance, min_radius, max_radius, min_arc_to_arc_distance, min_arc_length
    max_points = 100
    min_distance = 3000
    max_distance = 5000
    min_radius = 3100
    max_radius = 20000
    min_arc_to_arc_distance = 1000
    min_arc_length = 1300
    return max_points, min_distance, max_distance, min_radius, max_radius, min_arc_to_arc_distance, min_arc_length
    
def create_txt(filename, adjusted_linestring, radius_list, BC_STA_LIST, EC_STA_LIST, EP_STA, direction):
    # Hide the root window
    # 디렉토리가 없는 경우 생성

    workdiretory = 'c:/temp/랜덤선형성과/좌표/'
    # 디렉토리가 없는 경우 생성
    if not os.path.exists(workdiretory):
        os.makedirs(workdiretory)
    
    alignment_file_path = workdiretory + filename + '_alignment_file.txt'
    if alignment_file_path:
        with open(alignment_file_path, "w") as file:
            for i, point in enumerate(adjusted_linestring.coords):
                x, y = point
                if i == 0 or i == len(adjusted_linestring.coords) - 1:
                    file.write(f'{x:.4f},{y:.4f}\n')
                else:
                    radius = radius_list[i - 1]
                    file.write(f'{x:.4f},{y:.4f},{radius}\n')

    BVE_file_path = workdiretory + filename + '_bve.txt'

    if BVE_file_path:
        with open(BVE_file_path, "w") as file:
            file.write(f',;BP\n0,.curve 0;\n')
            for i in range(len(BC_STA_LIST)):
                BC = BC_STA_LIST[i]
                EC = EC_STA_LIST[i]
                minus = direction[i]
                radius = radius_list[i]
                curve_str = f'{BC:.2f},.curve {radius};\n' if minus == 1 else f'{BC:.2f},.curve -{radius};\n'
                file.write(f',;IP{i+1}\n{curve_str}{EC:.2f},.curve 0;\n')
            file.write(f',;EP\n{EP_STA:.2f},.curve 0;\n')

def export_kml(filename, adjusted_linestring):
    try:
        create_kml(filename, adjusted_linestring.coords)
        print('kml 저장성공\n')
    except ValueError as e:
        print(f'kml 저장 중 에러 발생: {e}')
        
def export_dxf(filename, params):
    # DXF 저장
    dxf_params = (params[0],params[1],params[2],params[3],params[4],params[5])
    try:
        create_dxf(filename, *dxf_params)
        print('도면 저장성공\n')
    except ValueError as e:
        print(f'도면 저장 중 에러 발생: {e}')

def export_txt(filename, params):
    # DXF 저장
    txt_params = (params[0],params[4],params[6],params[7],params[8],params[5])
    try:
        create_txt(filename, *txt_params)
        print('txt 저장성공\n')
    except ValueError as e:
        print(f'txt 저장 중 에러 발생: {e}')
        
def calculate_score(length, min_radius, num_curves, cost):
    """
    점수 계산 함수
    - length: 노선 길이 (km)
    - min_radius: 최소 곡선 반경 (m)
    - num_curves: 곡선의 개수
    - cost: 공사비 (원)
    
    점수는 길이와 공사비가 작을수록 높은 점수를 부여하도록 가중치와 수식을 조정합니다.
    """
    # 각 평가 요소의 가중치 설정
    length_weight = 0.2
    cost_weight = 0.3
    min_radius_weight = 0.25
    num_curves_weight = 0.25
    
    # 역수 형태로 가중치를 반영하여 점수 계산
    # 길이와 공사비는 작을수록 점수가 높아짐
    normalized_length = 1 / (1 + length)
    normalized_cost = 1 / (1 + cost)
    
    score = (normalized_length * length_weight +
             min_radius * min_radius_weight +
             num_curves * num_curves_weight +
             normalized_cost * cost_weight)
    
    return score


def create_joined_linestirng(linestring,BC_XY,EC_XY,O_XY,direction):#선과 호를 이어서 새로운 linestring생성
    
    #호 리스트 생성
    acr1, acr2 = [], []
    for i in range(len(BC_XY)):
        x_arc, y_arc = draw_arc(direction[i], BC_XY[i], EC_XY[i], O_XY[i])
        acr1.append(x_arc)
        acr2.append(y_arc)

    acr1 = [item for sublist in acr1 for item in sublist]
    acr2 = [item for sublist in acr2 for item in sublist]
    curve_coords = list(zip(acr1, acr2))
    combined_coords = [linestring.coords[0]] + curve_coords + [linestring.coords[-1]]
    new_linestring = LineString(combined_coords)
    
    return new_linestring

def generate_and_score_lines(num_iterations):
    global P1_list, P2_list
    get_passpoint()
    
    best_score = -float('inf')
    best_linestring = None
    best_params = None
    scores_and_lines = []

    for i in range(num_iterations):
        print(f"Iteration {i+1}/{num_iterations}")

        if ispasspoint:
            P1_list =[]
            P2_list = []
            
            random_linestring, P1_list, P2_list = generate_random_linestring_for_passpoint(start_point, end_point, passpoint_coordinates, max_points, min_distance, max_distance)

        else:
            random_linestring = generate_random_linestring_within_radius(start_point, end_point, max_points, min_distance, max_distance)

        adjusted_linestring, new_angles = process_linestring(random_linestring)

        score, new_linestring, params, formatted_cost = evaluate_linestring(adjusted_linestring, new_angles)
        scores_and_lines.append((score, *params))

        print(f"Score: {score}")

        if score > best_score:
            best_score = score
            best_linestring = new_linestring
            best_params = params

        save_output_files(f'대안{i}', new_linestring, *params)

    print(f"Best Score: {best_score}")
    
    top_10_lines = get_top_n_lines(scores_and_lines, 10)

    for i, line in enumerate(top_10_lines):
        file_name = f'최종{i}'
        joined_linestirng = create_joined_linestirng(line[1], line[2], line[3], line[4], line[6])
        save_out_params = (line[1], line[2], line[3], line[4], line[5], line[6], line[7], line[8], line[9])
        save_output_files(file_name, joined_linestirng, *save_out_params)

    return top_10_lines

def adjust_linestring_with_passpoint(line_string, p1_points, p2_points, angle_threshold=30):
    coords = list(line_string.coords)
    
    adjusted_points = [coords[0]]  # Start with the first point
    
    for i in range(1, len(coords) - 1):
        current_point = coords[i]
        
        # p1, p2, [1] 및 [-2] 점이 예외로 처리됨
        if current_point in [(p.x, p.y) for p in p1_points] or \
           current_point in [(p.x, p.y) for p in p2_points] or \
           current_point == coords[1] or \
           current_point == coords[-2]:
            adjusted_points.append(current_point)
            continue
        
        # 이전 점과 다음 점의 벡터를 계산하여 각도를 구함
        prev_vector = (coords[i][0] - coords[i - 1][0],
                       coords[i][1] - coords[i - 1][1])
        next_vector = (coords[i + 1][0] - coords[i][0],
                       coords[i + 1][1] - coords[i][1])
        inner_angle = calculate_inner_angle(prev_vector, next_vector)
        
        # 각도가 임계값보다 작은 경우만 점을 추가
        if inner_angle < angle_threshold:#교각보다 작은경우
            adjusted_points.append(current_point)
    
    # Add the last point if it's not the same as the second last one
    if adjusted_points[-1] != coords[-1]:
        adjusted_points.append(coords[-1])
    
    return LineString(adjusted_points)

def process_linestring(linestring):
    angles = calculate_angles_and_plot(linestring)

    if ispasspoint:
        adjusted_linestring = adjust_linestring_with_passpoint(linestring, P1_list, P2_list, angle_threshold=40)
        new_angles = calculate_angles_and_plot(adjusted_linestring)
    else:
        adjusted_linestring = adjust_linestring(linestring, angles)
        new_angles = calculate_angles_and_plot(adjusted_linestring)
        
    if isstaticbearing:
        adjusted_linestring = static_beating(adjusted_linestring, start_bearing, end_bearing)
        new_angles = calculate_angles_and_plot(adjusted_linestring)

    return adjusted_linestring, new_angles

def evaluate_linestring(linestring, angles):
    radius_list = [adjust_radius_by_angle(angle, min_radius, max_radius) for angle in angles]
    BC_XY, EC_XY, O_XY, direction, BC_STA_LIST, EC_STA_LIST, EP_STA = main_loop(linestring, radius_list, angles, min_arc_to_arc_distance)

    new_linestring = create_joined_linestirng(linestring, BC_XY, EC_XY, O_XY, direction)
    length_km = new_linestring.length / 1000
    min_radius_for_alignment = min(radius_list)
    num_ip = len(BC_XY)
    cost_per_km = 211
    total_cost = length_km * cost_per_km
    formatted_cost = format_cost(total_cost)

    score = calculate_score(length_km, min_radius_for_alignment, num_ip, total_cost)
    params = (linestring, BC_XY, EC_XY, O_XY, radius_list, direction, BC_STA_LIST, EC_STA_LIST, EP_STA)

    console_print_line_info(BC_XY, new_linestring, radius_list)

    return score, new_linestring, params, formatted_cost

def save_output_files(base_filename, linestring, *params):
    dxf_filename = base_filename + '.dxf'
    txt_filename = base_filename + '.txt'
    kml_filename = base_filename + '.kml'

    export_dxf(dxf_filename, params)
    export_txt(txt_filename, params)
    export_kml(kml_filename, linestring)

def get_top_n_lines(scores_and_lines, n):
    return sorted(scores_and_lines, key=lambda x: x[0], reverse=True)[:n]

def get_passpoint():
    global passpoint_coordinates, passpoint_name_list
    passpoint_coordinates, passpoint_name_list = input_passpoints(ispasspoint)


def plot_line(ax, linestring, BC_XY, EC_XY, O_XY, radius_list, direction):
    """
    선형을 플로팅하는 함수
    """
    ax.clear()  # 이전 플롯을 지움
    x, y = linestring.xy
    ax.plot(x, y, color='gray', linestyle='--')

    # 첫번째와 마지막 line plot
    ax.plot([linestring.coords[0][0], BC_XY[0][0]], [linestring.coords[0][1], BC_XY[0][1]], color='r')
    ax.plot([linestring.coords[-1][0], EC_XY[-1][0]], [linestring.coords[-1][1], EC_XY[-1][1]], color='r')

    # 각 곡선을 플로팅
    for i in range(len(BC_XY)):
        x_arc, y_arc = draw_arc(direction[i], BC_XY[i], EC_XY[i], O_XY[i])
        ax.plot(x_arc, y_arc, label='선형', color='RED')

        #곡선 사이 직선 플로팅
        if i < len(BC_XY) - 1:  # EC_XY의 마지막 요소가 BC_XY의 마지막 요소보다 하나 적으므로 이를 고려
            ax.plot(*zip(*[BC_XY[i+1], EC_XY[i]]), linestyle='-', color='r')

    #곡선반경과 IP넘버 텍스트
    for i, point in enumerate(linestring.coords):
        x, y = point
        label = 'BP' if i == 0 else 'EP' if i == len(linestring.coords) - 1 else f'IP {i}'
        ax.text(x, y, label, fontsize=12, ha='right', color='r')
        if i != 0 and i != len(linestring.coords) - 1:
            ax.text(x, y, f'R={radius_list[i - 1]}', fontsize=12, ha='left', color='b')

    if passpoint_coordinates:
        for pass_point, name in zip(passpoint_coordinates, passpoint_name_list):
            x, y = pass_point.x, pass_point.y
            ax.scatter(x, y, color='r', marker='o', zorder=10)
            ax.text(x, y, name, fontsize=12, ha='left', color='r')
            

    ax.set_title('Selected LineString')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.grid(True)
    ax.set_aspect('equal', adjustable='box')
    plt.draw()  # 플롯 업데이트

def exit_program():
    print("프로그램을 종료합니다.")
    root.destroy()

def redraw():
    main_cal_logic()

        
def onselect(event):#콤보박스 선택시
    selected_index = combobox.current()  # 콤보박스에서 선택한 인덱스
    selected_line = top_10_lines[selected_index]
    plot_line(ax, selected_line[1], selected_line[2], selected_line[3], selected_line[4], selected_line[5], selected_line[6])
    # top10 = (BC_XY, EC_XY, O_XY, radius_list, direction, BC_STA_LIST, EC_STA_LIST, EP_STA)
              #1, 2      3     4        5           6             7               8      9
    #save_params(radius_list, BC_STA_LIST, EC_STA_LIST, EP_STA, direction)
    console_print_line_info(selected_line[2],selected_line[1],selected_line[5])
    console_print_IP_info(selected_line[1],selected_line[5])

    
def console_print_line_info(bc,linestring,radius_list):
    num_ip = len(bc)
    length_km = linestring.length / 1000
    cost_per_km = 211
    min_radius_for_alignment = min(radius_list)   
    total_cost = length_km * cost_per_km
    formatted_cost = format_cost(total_cost)
    print('-------------------------------------------\n')
    print('노선정보출력')
    print(f'IP 갯수 : {num_ip}')
    print(f'노선연장 : {length_km:.2f} km')
    print(f'공사비 : {formatted_cost}')
    print(f'최소곡선반경 R= {min_radius_for_alignment}')
    print('-------------------------------------------\n')
    
def console_print_IP_info(linestring, radius_list):
    print('IP제원출력\n')
    
    TL, CL = cal_TL_CL(linestring, radius_list)
    IA = calculate_angles_and_plot(linestring)
    
    for i in range(len(radius_list)):
        print(f'IPNO.{i + 1}')
        print(f'IA : {degrees_to_dms(IA[i])}')
        print(f'R : {radius_list[i]}')
        print(f'TL : {TL[i]:.2f}')
        print(f'CL : {CL[i]:.2f}')
        print(f'X : {linestring.coords[i+1][0]:.4f}')  # IP의 X 좌표 (linestring에서 i+1번째 점)
        print(f'Y : {linestring.coords[i+1][1]:.4f}\n')  # IP의 Y 좌표 (linestring에서 i+1번째 점)


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
    
def cal_TL_CL(linestring, radius_list):
    TL = []
    CL = []
    IA = calculate_angles_and_plot(linestring)
    
    for i in range(len(radius_list)):
        tl = radius_list[i] * math.tan(math.radians(IA[i]) / 2)  # TL 계산
        cl = radius_list[i] * math.radians(IA[i])  # CL 계산
        TL.append(tl)
        CL.append(cl)
    
    return TL, CL

#메인코드
def rotate_point(origin, point, angle):
    """Rotate a point counterclockwise around a given origin."""
    angle_rad = math.radians(angle)
    ox, oy = origin
    px, py = point
    qx = ox + math.cos(angle_rad) * (px - ox) - math.sin(angle_rad) * (py - oy)
    qy = oy + math.sin(angle_rad) * (px - ox) + math.cos(angle_rad) * (py - oy)
    return (qx, qy)


def static_beating(linestring, start_bearing, end_bearing):
    """Adjust the linestring based on the start and end bearings."""
    
    if not isstaticbearing:
        
        return linestring

    coords = list(linestring.coords)
    
    if len(coords) < 4:
        raise ValueError("Linestring must have at least 4 points for static bearing adjustment.")
    
    BP = coords[0]
    IP1 = coords[1]
    IP_last = coords[-2]
    EP = coords[-1]

    # Calculate bearings
    # Calculate bearings
    bearing_start = calculate_bearing(BP[0], BP[1], IP1[0], IP1[1])
    
    bearing_end = calculate_bearing(IP_last[0], IP_last[1], EP[0], EP[1])
    
    
    # Compute the needed rotations
    rotate_start = bearing_start - start_bearing
    
    rotate_end = bearing_end - end_bearing
    
    # Apply rotations
    IP1_rotated = rotate_point(BP, IP1, -rotate_start)
    lastIP_rotated = rotate_point(EP, IP_last, -rotate_end)
    
    # Create the new linestring
    new_coords = [BP, IP1_rotated] + coords[2:-2] + [lastIP_rotated, EP]
    new_linestring = LineString(new_coords)

    return new_linestring

#경유지로직
def generate_random_linestring_for_passpoint(start, end, passpoints, max_points, min_distance, max_distance):
    combined_points = []
    
    P1_list = []
    P2_list = []

    # Generate random points around each pass point
    for i in range(len(passpoints)):
        p1, p2 = generate_random_line(passpoints[i], end,  min_distance, max_distance)
        P1_list.append(p1)
        P2_list.append(p2)

    # Connect the first passpoint to the start point
    first_segment = generate_random_linestring_within_radius(start, P1_list[0], max_points, min_distance, max_distance, min_end_distance=2000)

    #라인스트링객체를 분해
    first_segment = list(first_segment.coords)
    combined_points.extend(first_segment)

    # Generate segments between the generated points
    for i in range(len(passpoints) - 1):
        segment = generate_random_linestring_within_radius(P2_list[i], P1_list[i + 1], max_points, min_distance, max_distance, min_end_distance=2000)

        #라인스트링객체를 분해
        segment = list(segment.coords)
        combined_points.extend(segment)

    # Connect the last passpoint to the end point
    final_segment = generate_random_linestring_within_radius(P2_list[-1], end, max_points, min_distance, max_distance, min_end_distance=2000)

    #라인스트링객체를 분해
    final_segment = list(final_segment.coords)
    
    combined_points.extend(final_segment)

    # Add the end point to the list
    combined_points.append((end.x, end.y))

    return LineString(combined_points), P1_list, P2_list

def generate_random_line(point, end, min_distance, max_distance):
    """
    주어진 점을 중심으로 end 방향으로 대칭적으로 랜덤한 두 점을 생성합니다.
    
    인수:
    - point: 중심이 될 점 (Point 객체)
    - end: 최종 목적지 (Point 객체)
    - min_distance: 점들 사이의 최소 거리
    - max_distance: 점들 사이의 최대 거리
    
    반환:
    - 새로 생성된 두 점 (Point 객체들)
    """
    angle_to_end = calculate_angle(point, end)  # start에서 end로 향하는 방향의 각도 계산
    opposite_angle_to_end = get_opposite_angle(angle_to_end) #시작점은 반대방향에 존재해야함.
    while True:
        # end로 향하는 방향을 중심으로 약간의 랜덤 각도를 더해 점을 생성
        angle = random.uniform(opposite_angle_to_end - pi/4, opposite_angle_to_end + pi/4)  # -45도에서 +45도 사이의 각도
        distance = random.uniform(min_distance, max_distance)
        x1 = point.x + distance * cos(angle)
        y1 = point.y + distance * sin(angle)
        new_point1 = Point(x1, y1)

        # 첫 번째 점의 각도를 기준으로 대칭되는 점을 생성
        new_point1_to_point_angle = calculate_angle(new_point1, point)
        x2 = new_point1.x + distance * 2 * cos(new_point1_to_point_angle)
        y2 = new_point1.y + distance * 2 * sin(new_point1_to_point_angle)
        new_point2 = Point(x2, y2)

        # 새로 생성된 두 점이 유효한지를 검사
        if new_point1.distance(point) >= min_distance and new_point2.distance(point) >= min_distance:
            return new_point1, new_point2

def get_opposite_angle(angle):
    opposite_angle = angle + 180
    if opposite_angle >= 360:
        opposite_angle -= 360
    return opposite_angle

def toggle_ispasspoint():
    global ispasspoint
    ispasspoint = ispasspoint_var.get() == 1

def toggle_isstaticbearing():
    global isstaticbearing
    isstaticbearing = isstaticbearing_var.get() == 1
    
def initial_GUI():
    global root, ax, start_waypoint, end_waypoint, ispasspoint_var, ispasspoint, isstaticbearing, isstaticbearing_var
    global start_bearing, start_bearing_var, end_bearing, end_bearing_var
    global combobox
    global count_iterations_var
    
    # Tkinter 초기화
    root = Tk()
    root.title("랜덤 선형뽑기")
    root.geometry("900x900")

    # 콤보박스에 사용할 라벨 생성
    combo_labels = [f'Line {i+1}' for i in range(10)]
    
    # 콤보박스 프레임 생성
    COMBO_frame = tk.Frame(root)
    COMBO_frame.pack(side=tk.TOP, pady=5)

    # 콤보박스 생성
    combobox_var = StringVar(value=combo_labels[0])
    combobox = ttk.Combobox(COMBO_frame, textvariable=combobox_var, values=combo_labels)
    combobox.pack(side=tk.LEFT, pady=5)
    combobox.bind("<<ComboboxSelected>>", onselect)


    # 플롯 생성
    # Initialize the plot
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot()
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Create a frame for the toolbar
    toolbar_frame = tk.Frame(root)
    toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)

    # Add the navigation toolbar
    toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
    toolbar.update()

    # Create a frame to contain buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=5)

    # Create a frame to contain buttons
    CHEACK_frame = tk.Frame(root)
    CHEACK_frame.pack(pady=5)
    
    # 다시그리기 버튼 생성
    redraw_button = tk.Button(button_frame, text="다시그리기", command=redraw)
    redraw_button.pack(side=tk.LEFT, pady=5, padx=10)

    # 종료 버튼 생성
    exit_button = tk.Button(button_frame, text="종료", command=exit_program)
    exit_button.pack(side=tk.LEFT, pady=5, padx=10)

    ispasspoint_var = tk.IntVar(value=0)
    
    # Create the checkbox
    ispasspoint_checkbox = tk.Checkbutton(CHEACK_frame, text="경유지 있음", variable=ispasspoint_var, command=toggle_ispasspoint)
    ispasspoint_checkbox.pack(side=tk.LEFT, pady=5, padx=10)

    isstaticbearing_var = tk.IntVar(value=0)
    # Create the checkbox
    isstaticbearing_checkbox = tk.Checkbutton(CHEACK_frame, text="방위각 고정", variable=isstaticbearing_var, command=toggle_isstaticbearing)
    isstaticbearing_checkbox.pack(side=tk.LEFT, pady=5, padx=10)

    # Create a frame to contain buttons
    TEXT_frame = tk.Frame(root)
    TEXT_frame.pack(pady=1)
    
    # Create a frame to contain buttons
    BOX_frame = tk.Frame(root)
    BOX_frame.pack(pady=1)
    
    tk.Label(TEXT_frame, text="시작점:").pack(side=tk.LEFT, padx=70, pady=1)
    start_waypoint = tk.Entry(BOX_frame)
    start_waypoint.pack(side=tk.LEFT, pady=1, padx=10)
    start_waypoint.insert(0, "함열역")

    
    tk.Label(TEXT_frame, text="끝점:").pack(side=tk.LEFT,padx=70, pady=1)
    end_waypoint = tk.Entry(BOX_frame)
    end_waypoint.pack(side=tk.LEFT, pady=1, padx=10)
    end_waypoint.insert(0, "소정리역")

    tk.Label(TEXT_frame, text="시작 방위각(도):").pack(side=tk.LEFT,padx=70, pady=1)
    start_bearing_var = tk.Entry(BOX_frame)
    start_bearing_var.pack(side=tk.LEFT, pady=1, padx=10)
    start_bearing_var.insert(0, "24")

    tk.Label(TEXT_frame, text="종점 방위각(도):").pack(side=tk.LEFT,padx=10, pady=1)
    end_bearing_var = tk.Entry(BOX_frame)
    end_bearing_var.pack(side=tk.LEFT, pady=1, padx=10)
    end_bearing_var.insert(0, "34")

    tk.Label(TEXT_frame, text="반복횟수:").pack(side=tk.LEFT, padx=20, pady=1)
    count_iterations_var = tk.Entry(BOX_frame)
    count_iterations_var.pack(side=tk.LEFT, pady=1, padx=3)
    count_iterations_var.insert(0, "10")

    
def initial_input_parameters():
    global start_station,end_station, start_bearing,  end_bearing, ispasspoint, isstaticbearing, start_point, end_point
    global num_iterations
    
    start_station = start_waypoint.get()
    end_station = end_waypoint.get()

    start_bearing = int(start_bearing_var.get())
    end_bearing = int(end_bearing_var.get())
    
    ispasspoint = ispasspoint_var.get()
    isstaticbearing = isstaticbearing_var.get()

    start_point, end_point = process_coordinates(start_station, end_station)

    num_iterations = int(count_iterations_var.get())
    
    
def main_cal_logic():
    global top_10_lines
    initial_input_parameters()
    top_10_lines = generate_and_score_lines(num_iterations)
    
def main():
    initial_GUI()
    
    initialize_parameters()
    
    root.mainloop()
    
if __name__ == "__main__":
    main()
