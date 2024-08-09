import random
from shapely.geometry import Point, LineString
import matplotlib.pyplot as plt
from math import cos, sin, atan2, degrees, radians, pi
import math
from tkinter import filedialog
import tkinter as tk
import simplekml
import pyproj
import os
import numpy as np
from geopy.geocoders import Nominatim

plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False

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



#메인코드

# 유효한 시작 지점과 종료 지점 좌표를 입력받기
start_coordinates,start_name = get_valid_coordinates("BP 장소 입력: ")
end_coordinates,end_name= get_valid_coordinates("EP 장소 입력: ")

# 시작과 종료 좌표가 모두 유효하므로 이제 코드를 계속 실행할 수 있습니다.
print(f"시작 좌표:{start_name} : {start_coordinates}")
print(f"종료 좌표:{end_name} : {end_coordinates}")

start_point = Point(calc_pl2xy((start_coordinates[1],start_coordinates[0])))

end_point = Point(calc_pl2xy((end_coordinates[1],end_coordinates[0])))

max_points = 100 # At least 3 points to form a linestring
min_distance = 3000
max_distance = 5000
min_radius = 3100
max_radius = 20000
min_arc_to_arc_distance = 1300 #직선 최소길이
min_arc_length = 1300 #곡선 최소길이

ispasspoint = True

#초기선형 생성
random_linestring = generate_random_linestring_within_radius(start_point, end_point, max_points, min_distance, max_distance)


# 교각 계산
angles = calculate_angles_and_plot(random_linestring)

#초기선형 수정
adjusted_linestring = adjust_linestring(random_linestring, angles)

#수정된 선형 교각계산
new_angles = calculate_angles_and_plot(adjusted_linestring)

#경유지 존재지 경유지 포함
if ispasspoint:
    passpoint_coordinates = []
    passpoint_name_list = []
    i= 0
    while True:
        passpoint_coordinate,passpoint_name = get_valid_coordinates("경유지 입력: ")
        print(f"경유지: {passpoint_name} = {passpoint_coordinate}")
        pass_point = Point(calc_pl2xy((passpoint_coordinate[1],passpoint_coordinate[0])))
        passpoint_coordinates.append(pass_point) # Example passpoint
        passpoint_name_list.append(passpoint_name)
        
        i += 1
        a = int(input("계속해서 입력하려면 1을 입력하세요. 경유지 입력 종료는 0 입력: "))
        if a == 0:
            print(f'경유지 입력이 종료되었습니다. 입력 갯수 {i}')
            break
        
    # 입력된 경유지를 포함하여 선형 조정
    for pass_point in passpoint_coordinates:
        adjusted_linestring = adjust_linestring_for_passpoint(adjusted_linestring,pass_point)

    #다시한번 수정
    #수정된 선형 교각계산
    new_angles = calculate_angles_and_plot(adjusted_linestring)
    
#초기 랜덤 반경 생성
radius_list = []
for i in range(len(new_angles)):
    IA = new_angles[i]
    radius = adjust_radius_by_angle(IA, min_radius, max_radius)
    radius_list.append(radius)

#linestring에 원곡선 추가
#BC_XY,EC_XY,O_XY,direction,BC_STA_LIST,EC_STA_LIST = calculate_simple_curve(adjusted_linestring,radius_list,new_angles)    

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
        print(f'IP-EP 방위각 = {last_IP_EP_bearing}')
        print(f'EC-EP 방위각 = {EC_EP_bearing}')
        return False
    else:
        radius_list[-1] = adjust_radius(radius_list, -1)
        print(f'마지막 반경: {radius_list[-1]}')
        return True
    
def main_loop(adjusted_linestring, radius_list, new_angles):
    j = 0

    while True:
        print(f'루프 {j}회차')
        BC_XY, EC_XY, O_XY, direction, BC_STA_LIST, EC_STA_LIST = calculate_simple_curve(adjusted_linestring, radius_list, new_angles)
        CL_LIST = [ec - bc for ec, bc in zip(EC_STA_LIST, BC_STA_LIST)]
        
        isCurveOverlap_list = []
        
        for i in range(len(BC_STA_LIST) - 1):
            print(f'현재IP{i+1}')
            max_R = max(radius_list[i - 1], radius_list[i], radius_list[i + 1])
            bc_to_ec_dist = BC_STA_LIST[i + 1] - EC_STA_LIST[i]
            print(f'BC = {BC_STA_LIST[i]}, EC = {EC_STA_LIST[i]}, R = {radius_list[i]}')
            
            if bc_to_ec_dist > 0:#겹치지 않은경우
                if bc_to_ec_dist < min_arc_to_arc_distance:#최소곡선길이보다 작으면
                    print(f'경고: IP{i + 2}번의 시작점과 IP{i + 1}번의 종점 간의 거리 {bc_to_ec_dist:.2f}m는 {min_arc_to_arc_distance} 미만입니다.')
                    radius_list[i - 1 if max_R == radius_list[i - 1] else i + 1 if max_R == radius_list[i + 1] else i] = adjust_radius(radius_list, i)
                    isCurveOverlap_list.append(True)
                else:
                    isCurveOverlap_list.append(False)
            else:
                print(f'IP{i + 1}번과 IP{i + 2}번 곡선 겹침 L= {bc_to_ec_dist}')
                
                radius_list[i - 1 if max_R == radius_list[i - 1] else i + 1 if max_R == radius_list[i + 1] else i] = adjust_radius(radius_list, i)
                isCurveOverlap_list.append(True)
        islastoverlap = check_last_ip_ep(adjusted_linestring, EC_XY, radius_list)
        
        if all(not overlap for overlap in isCurveOverlap_list) and not islastoverlap:
            print(f'루프 {j}회차 종료')
            break
        
        j += 1
        print('---------------------------------------------------')

    return  BC_XY, EC_XY, O_XY, direction, BC_STA_LIST, EC_STA_LIST
# 실행 부분
BC_XY, EC_XY, O_XY, direction, BC_STA_LIST, EC_STA_LIST =main_loop(adjusted_linestring, radius_list, new_angles)

total_IP_count = len(adjusted_linestring.coords) - 2
print('IP좌표출력')
print(f'IP 갯수 : {total_IP_count}')

# Plot the random linestring

#IP라인 출력
x, y = adjusted_linestring.xy
plt.plot(x, y, color='gray',linestyle='--')

#첫번째와 마지막 line plot
# Extract x and y coordinates for plotting
x_values = [adjusted_linestring.coords[0][0], BC_XY[0][0]]
y_values = [adjusted_linestring.coords[0][1], BC_XY[0][1]]
x_values2 = [adjusted_linestring.coords[-1][0], EC_XY[-1][0]]
y_values2 = [adjusted_linestring.coords[-1][1], EC_XY[-1][1]]
# Create the plot
plt.plot(x_values, y_values, color='r')  
plt.plot(x_values2, y_values2, color='r')

x_arcs = {}  # 변수를 저장할 딕셔너리 생성
y_arcs = {}
acr1 = []
acr2 = []

i = 0
# 그래프에 호를 그림
for i in range(len(BC_XY)):

    key = f'x_arc{i+1}'  # 변수명 생성
    x_arcs[key],y_arcs[key] = draw_arc(direction[i],BC_XY[i], EC_XY[i], O_XY[i])  # 변수에 할당
    plt.plot(x_arcs[key], y_arcs[key], label='선형', color='RED')
    acr1.append(x_arcs[key])
    acr2.append(y_arcs[key])

    

    
    if i < len(BC_XY) - 1:  # EC_XY의 마지막 요소가 BC_XY의 마지막 요소보다 하나 적으므로 이를 고려
        plt.plot(*zip(*[BC_XY[i+1],EC_XY[i]]), linestyle='-', color='r')
    
    
#리스트 단일화
acr1 = [item for sublist in acr1 for item in sublist]
acr2 = [item for sublist in acr2 for item in sublist]

# 곡선 좌표 리스트 (x, y 튜플의 리스트)
curve_coords = list(zip(acr1, acr2))  # (x, y) 튜플 리스트로 변환

# 새 좌표 리스트 생성
combined_coords = [adjusted_linestring.coords[0]] + curve_coords + [adjusted_linestring.coords[-1]]

# 새 LineString 생성
new_linestring = LineString(combined_coords)

# 노선 연장 길이 출력 (단위: km)
print(f'노선연장 : {new_linestring.length / 1000:.2f} km')

# 공사비를 km당 211억원으로 계산
# new_linestring.length는 길이 (m 단위)라고 가정
cost_per_km = 211  # 211억원 per km
length_km = new_linestring.length / 1000  # 길이를 km 단위로 변환

# 전체 공사비 계산
total_cost = length_km * cost_per_km  # 총 공사비 (원 단위로 계산)

# 포맷된 공사비 출력
formatted_cost = format_cost(total_cost)
print(f'공사비 : {formatted_cost}')

#최소곡선반경 출력
min_radius_for_alignment = min(radius_list)
print(f'최소곡선반경 R= {min_radius_for_alignment}')

# Add labels for each point
for i, point in enumerate(adjusted_linestring.coords):
    x, y = point
    if i == 0:
        plt.text(x, y, 'BP', fontsize=12, ha='right', color='r')
        print(f'BP,{x},{y}')
    elif i == len(adjusted_linestring.coords) - 1:
        plt.text(x, y, 'EP', fontsize=12, ha='right', color='r')
        print(f'EP,{x},{y}')
    else:
        radius = radius_list[i - 1]  # radius_list length is one less than adjusted_linestring.coords
        plt.text(x, y, f'IP {i}', fontsize=12, ha='right', color='r')
        plt.text(x, y, f'R={radius}', fontsize=12, ha='left', color='b')
        print(f'IP{i},{x},{y},R={radius}')

# 경유지 좌표 출력
if ispasspoint:
    for pass_point, name in zip(passpoint_coordinates, passpoint_name_list):
        x, y = pass_point.x, pass_point.y
         
        plt.scatter(x,y, color='r', marker='o',zorder=10)
        plt.text(x,y, name, fontsize=12, ha='left', color='r')
        print(f'경유지: {name}, 좌표: ({pass_point.x}, {pass_point.y})')

# Create Tkinter root window
root = tk.Tk()
root.withdraw()  # Hide the root window

file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])

if file_path:
    with open(file_path, "w") as file:
        for i, point in enumerate(adjusted_linestring.coords):
            x, y = point
            if i == 0 or i == len(adjusted_linestring.coords) - 1:
                file.write(f'{x:.4f},{y:.4f}\n')
            else:
                radius = radius_list[i - 1]
                file.write(f'{x:.4f},{y:.4f},{radius}\n')

BVE_file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])

EP_XY = adjusted_linestring.coords[-1]
FINAL_EC_XY = EC_XY[-1]
EC_EP_distnace = calculate_distance(FINAL_EC_XY[0],FINAL_EC_XY[1], EP_XY[0],EP_XY[1])
EP_STA = EC_STA_LIST[-1] + EC_EP_distnace

if BVE_file_path:
    with open(BVE_file_path, "w") as file:
        file.write(f',;BP\n0,.curve 0;\n')
        
        for i in range(len(BC_STA_LIST)):
            
            BC = BC_STA_LIST[i]
            EC = EC_STA_LIST[i]
            minus = direction[i]
            radius = radius_list[i]
            
            if minus == 1:#양수
                file.write(f',;IP{i+1}\n')
                file.write(f'{BC:.2f},.curve {radius};\n')
                file.write(f'{EC:.2f},.curve 0;\n')
            else:
                file.write(f',;IP{i+1}\n')
                file.write(f'{BC:.2f},.curve -{radius};\n')
                file.write(f'{EC:.2f},.curve 0;\n')
        file.write(f',;EP\n{EP_STA:.2f},.curve 0;\n')        
try:
    create_kml(adjusted_linestring.coords)
    print('kml 저장성공')
except ValueError as e:
    print(f'kml 저장 중 에러 발생: {e}')



plt.title('Random LineString with Point Numbers and Inner Angles')
plt.xlabel('X')
plt.ylabel('Y')
plt.gca().set_aspect('equal', adjustable='box')
plt.show()
