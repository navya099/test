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
    
def create_dxf(coordinates,BC,EC,O,R,DR):
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
    
    filename = 'C:/TEMP/randomalinement.dxf'
    save_with_retry(doc, filename)
    
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

def create_kml(point_list):  # kml작성함수
    kml = simplekml.Kml()

    # Convert coordinates to latitude and longitude
    point_list_latlong = calc_pl2xy_array(point_list)

    # Create a single linestring to connect all points
    linestring = kml.newlinestring(name="Sample Polyline", coords=point_list_latlong)
    linestring.style.linestyle.color = simplekml.Color.red
    linestring.style.linestyle.width = 4

    # Save the KML file
    kml_file = "sample.kml"
    kml.save(kml_file)

    # Open the saved KML file
    os.system(f'start {kml_file}')  # This command works on Windows

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

def adjust_linestring_for_passpoint(linestring,passpoint):
    #인수:coordinates as LineString,passpoint as Point

    # LineString의 좌표 가져오기
    coordinates = list(linestring.coords)
    
    # 가장 가까운 선분 찾기
    min_distance = float('inf')
    closest_segment_index = None
    for i in range(len(coordinates) - 1):
        segment = LineString([coordinates[i], coordinates[i + 1]])
        distance = segment.distance(passpoint)
        if distance < min_distance:
            min_distance = distance
            closest_segment_index = i
            
    # 선택된 선분의 두 끝점
    start_point = Point(coordinates[closest_segment_index])
    end_point = Point(coordinates[closest_segment_index + 1])

    #선분의 방향 벡터
    direction_vector = np.array(end_point.coords[0]) - np.array(start_point.coords[0])

    # 경유지를 선분 위로 이동시키기 위해 필요한 이동 벡터
    move_vector = np.array(passpoint.coords[0]) - (np.array(start_point.coords[0]) + np.dot(np.array(passpoint.coords[0]) - np.array(start_point.coords[0]), direction_vector) / np.dot(direction_vector, direction_vector) * direction_vector)

    # 평행 이동된 새로운 점들
    new_start_point = np.array(start_point.coords[0]) + move_vector
    new_end_point = np.array(end_point.coords[0]) + move_vector
    
    # 새로운 좌표 리스트 생성
    new_coords = coordinates[:closest_segment_index] + [(new_start_point[0], new_start_point[1]), (new_end_point[0], new_end_point[1])] + coordinates[closest_segment_index + 2:]

    # 새로운 LineString 생성
    return LineString(new_coords)

## Define start and end points
# 테스트할 지명 입력
def get_valid_coordinates(prompt):
    while True:
        location_name = str(input(prompt))
        coordinates = get_coordinates(location_name)
        
        if coordinates is None:
            print("유효한 지명을 입력해주세요.")
        else:
            return coordinates,location_name





#경유지 로직
def input_passpoints():
    passpoint_coordinates = []
    passpoint_name_list = []
    i = 0
    ispasspoint = None
    
    while True:
        a = int(input('경유지 유무 1: 있음 0: 없음: '))
        
        if a == 0:  # 사용자에게 경유지 입력을 중단할 옵션 제공
            print('경유지를 생략합니다.')
            ispasspoint = False
            return ispasspoint, passpoint_coordinates, passpoint_name_list
        else:
            passpoint_coordinate, passpoint_name = get_valid_coordinates("경유지 입력: ")
            ispasspoint = True
            print(f"경유지: {passpoint_name} = {passpoint_coordinate}")
            pass_point = Point(calc_pl2xy((passpoint_coordinate[1], passpoint_coordinate[0])))
            passpoint_coordinates.append(pass_point)
            passpoint_name_list.append(passpoint_name)
            
            i += 1
            continue_input = int(input("계속해서 입력하려면 1을 입력하세요. 경유지 입력 종료는 0 입력: "))

            if continue_input == 0:
                print(f'경유지 입력이 종료되었습니다. 입력 갯수: {i}')
                return ispasspoint, passpoint_coordinates, passpoint_name_list

def adjust_linestring_with_passpoints(adjusted_linestring, passpoint_coordinates):
    for pass_point in passpoint_coordinates:
        adjusted_linestring = adjust_linestring_for_passpoint(adjusted_linestring, pass_point)
    return adjusted_linestring


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
        print('경고: 마지막 곡선과 종점 겹침')
        print(f'마지막 반경: {radius_list[-1]}')
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
            print('루프 {j}회차 종료. 곡선반경 조정 실패')
            break
        
        j += 1
        #print('---------------------------------------------------')

    return BC_XY, EC_XY, O_XY, direction, BC_STA_LIST, EC_STA_LIST, EP_STA

def process_coordinates():
    # 유효한 시작 지점과 종료 지점 좌표를 입력받기
    start_coordinates, start_name = get_valid_coordinates("BP 장소 입력: ")
    end_coordinates, end_name = get_valid_coordinates("EP 장소 입력: ")

    print(f"시작 좌표: {start_name} : {start_coordinates}")
    print(f"종료 좌표: {end_name} : {end_coordinates}")

    start_point = Point(calc_pl2xy((start_coordinates[1], start_coordinates[0])))
    end_point = Point(calc_pl2xy((end_coordinates[1], end_coordinates[0])))
    return start_point, end_point

def initialize_parameters():
    max_points = 100
    min_distance = 3000
    max_distance = 5000
    min_radius = 3100
    max_radius = 20000
    min_arc_to_arc_distance = 1000
    min_arc_length = 1300
    return max_points, min_distance, max_distance, min_radius, max_radius, min_arc_to_arc_distance, min_arc_length
    
def save_files(adjusted_linestring, radius_list, BC_STA_LIST, EC_STA_LIST, EP_STA, direction):
    # Hide the root window

    alignment_file_path = 'c:/temp/alignment_file.txt'
    if alignment_file_path:
        with open(alignment_file_path, "w") as file:
            for i, point in enumerate(adjusted_linestring.coords):
                x, y = point
                if i == 0 or i == len(adjusted_linestring.coords) - 1:
                    file.write(f'{x:.4f},{y:.4f}\n')
                else:
                    radius = radius_list[i - 1]
                    file.write(f'{x:.4f},{y:.4f},{radius}\n')

    BVE_file_path = 'c:/temp/bve.txt'

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

    try:
        create_kml(adjusted_linestring.coords)
        print('kml 저장성공\n')
    except ValueError as e:
        print(f'kml 저장 중 에러 발생: {e}')

def calculate_score(length, min_radius, num_curves, cost):
    """
    점수 계산 함수
    - length: 노선 길이 (km)
    - min_radius: 최소 곡선 반경 (m)
    - num_curves: 곡선의 개수
    
    점수는 임의로 설정한 가중치와 수식으로 계산됩니다.
    """
    # 각 평가 요소의 가중치 설정
    length_weight = 0.25
    cost_weight = 0.3
    min_radius_weight = 0.25
    num_curves_weight  = 0.25
    score = length * length_weight  + min_radius * min_radius_weight + num_curves * num_curves_weight + cost * cost_weight
    
    return score

def generate_and_score_lines(num_iterations):
    best_score = -float('inf')
    best_linestring = None
    best_params = None

    scores_and_lines = []
    
    start_point, end_point = process_coordinates()
    max_points, min_distance, max_distance, min_radius, max_radius, min_arc_to_arc_distance, min_arc_length = initialize_parameters()
    ispasspoint, passpoint_coordinates, passpoint_name_list = input_passpoints()
    
    for i in range(num_iterations):
        print(f"Iteration {i+1}/{num_iterations}")
        
        # 랜덤 선형 생성
        random_linestring = generate_random_linestring_within_radius(start_point, end_point, max_points, min_distance, max_distance)
        angles = calculate_angles_and_plot(random_linestring)
        adjusted_linestring = adjust_linestring(random_linestring, angles)
        new_angles = calculate_angles_and_plot(adjusted_linestring)

        
        
        if ispasspoint:
            adjusted_linestring = adjust_linestring_with_passpoints(adjusted_linestring, passpoint_coordinates)
            new_angles = calculate_angles_and_plot(adjusted_linestring)

        radius_list = [adjust_radius_by_angle(angle, min_radius, max_radius) for angle in new_angles]
        BC_XY, EC_XY, O_XY, direction, BC_STA_LIST, EC_STA_LIST, EP_STA = main_loop(adjusted_linestring, radius_list, new_angles, min_arc_to_arc_distance)

        
        new_linestring = create_joined_linestirng(adjusted_linestring,BC_XY,EC_XY,O_XY,direction)
        
        # 점수요소계산
        length_km = new_linestring.length / 1000
        min_radius_for_alignment = min(radius_list)
        num_ip = len(BC_XY)
        cost_per_km = 211
        
        total_cost = length_km * cost_per_km
        formatted_cost = format_cost(total_cost)

        console_print_line_info(BC_XY,new_linestring,radius_list)
        
        score = calculate_score(length_km, min_radius_for_alignment, num_ip, total_cost)
        print(f"Score: {score}")

        # 점수와 선형 정보를 저장
        scores_and_lines.append((score, adjusted_linestring, BC_XY, EC_XY, O_XY, radius_list, direction, BC_STA_LIST, EC_STA_LIST, EP_STA, passpoint_coordinates, passpoint_name_list))


        # 최고 점수를 가진 선형 저장
        if score > best_score:
            best_score = score
            best_linestring = adjusted_linestring
            best_params = (BC_XY, EC_XY, O_XY, radius_list, direction, BC_STA_LIST, EC_STA_LIST, EP_STA)
            plot_params = (BC_XY, EC_XY, O_XY, radius_list, direction, passpoint_coordinates, passpoint_name_list)
            save_params = (radius_list, BC_STA_LIST, EC_STA_LIST, EP_STA, direction)
            dxf_params =  (BC_XY,EC_XY,O_XY,radius_list,direction)

            
    print(f"Best Score: {best_score}")
    
    #파일저장
    export_best_line(best_linestring, save_params, dxf_params)
    
    # 점수 상위 10개의 선형 선택
    top_10_lines = sorted(scores_and_lines, key=lambda x: x[0], reverse=True)[:10]

    return top_10_lines

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






def plot_line(ax, linestring, BC_XY, EC_XY, O_XY, radius_list, direction, passpoint_coordinates, passpoint_name_list):
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

def export_best_line(best_linestring, save_params, dxf_params):
    if best_linestring:
        save_files(best_linestring, *save_params)
        
        # DXF 저장
        try:
            create_dxf(best_linestring.coords, *dxf_params)
            print('도면 저장성공\n')
        except ValueError as e:
            print(f'도면 저장 중 에러 발생: {e}')   



    
def onselect(event):#콤보박스 선택시
    selected_index = combobox.current()  # 콤보박스에서 선택한 인덱스
    selected_line = top_10_lines[selected_index]
    plot_line(ax, selected_line[1], selected_line[2], selected_line[3], selected_line[4], selected_line[5], selected_line[6], selected_line[10], selected_line[11])
    # top10 = (BC_XY, EC_XY, O_XY, radius_list, direction, BC_STA_LIST, EC_STA_LIST, EP_STA)
              #1, 2      3     4        5           6             7               8      9
    #save_params(radius_list, BC_STA_LIST, EC_STA_LIST, EP_STA, direction)
    save_params = (selected_line[5], selected_line[7], selected_line[8], selected_line[9], selected_line[6])
    dxf_params = (selected_line[2], selected_line[3], selected_line[4], selected_line[5], selected_line[6])
    export_best_line(selected_line[1], save_params, dxf_params)
    console_print_line_info(selected_line[2],selected_line[1],selected_line[5])
    
def console_print_line_info(bc,linestring,radius_list):
    num_ip = len(bc)
    length_km = linestring.length / 1000
    cost_per_km = 211
    min_radius_for_alignment = min(radius_list)   
    total_cost = length_km * cost_per_km
    formatted_cost = format_cost(total_cost)
        
    print('노선정보출력')
    print(f'IP 갯수 : {num_ip}')
    print(f'노선연장 : {length_km:.2f} km')
    print(f'공사비 : {formatted_cost}')
    print(f'최소곡선반경 R= {min_radius_for_alignment}')
    
#메인코드

def main():
    global combobox, top_10_lines, ax
    
    num_iterations = 50  # 반복 횟수 설정

    top_10_lines = generate_and_score_lines(num_iterations)

    # Tkinter 초기화
    root = Tk()
    root.title("선형 선택")
    root.geometry("900x800")

    # 콤보박스에 사용할 라벨 생성
    combo_labels = [f'Line {i+1}: Score {top_10_lines[i][0]:.2f}' for i in range(len(top_10_lines))]
    
    # 콤보박스 생성
    combobox_var = StringVar(value=combo_labels[0])
    combobox = ttk.Combobox(root, textvariable=combobox_var, values=combo_labels)
    combobox.pack(pady=20)
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

    
    plot_line(ax, top_10_lines[0][1], top_10_lines[0][2], top_10_lines[0][3], top_10_lines[0][4], top_10_lines[0][5], top_10_lines[0][6], top_10_lines[0][10], top_10_lines[0][11])  # 처음에 첫 번째 선형을 플로팅  # 처음에 첫 번째 선형을 플로팅

    root.mainloop()
    
if __name__ == "__main__":
    main()
