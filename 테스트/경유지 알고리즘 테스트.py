import random
from shapely.geometry import Point, LineString
import matplotlib.pyplot as plt
from math import cos, sin, atan2, radians, pi, degrees
import numpy as np

plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False

def calculate_angle(start, end):
    """
    두 점 사이의 각도를 계산합니다.
    """
    return atan2(end.y - start.y, end.x - start.x)

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
    return points

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

def calculate_inner_angle(v1, v2):
    angle1 = atan2(v1[1], v1[0])
    angle2 = atan2(v2[1], v2[0])
    angle_diff = abs(angle2 - angle1)
    if angle_diff > pi:
        angle_diff = 2 * pi - angle_diff
    return degrees(angle_diff)

def generate_random_line(point, min_distance, max_distance):
    """
    주어진 점을 중심으로 대칭적으로 랜덤한 두 점을 생성합니다.
    
    인수:
    - point: 중심이 될 점 (Point 객체)
    - min_distance: 점들 사이의 최소 거리
    - max_distance: 점들 사이의 최대 거리
    
    반환:
    - 새로 생성된 두 점 (Point 객체들)
    """
    while True:
        # 랜덤 각도와 거리를 선택하여 첫 번째 점을 생성합니다.
        angle = random.uniform(0, 2 * pi)
        distance = random.uniform(min_distance, max_distance)
        x1 = point.x + distance * cos(angle)
        y1 = point.y + distance * sin(angle)
        new_point1 = Point(x1, y1)

        
        
        
        # 새 점1의 각도를 기준으로 대칭되는 점을 생성합니다.
        new_point1_to_point_angle = calculate_angle(new_point1, point)
        x2 = new_point1.x + distance * 2 * cos(new_point1_to_point_angle)
        y2 = new_point1.y + distance * 2 * sin(new_point1_to_point_angle)
        new_point2 = Point(x2, y2)

        #진행방향 방위각
        bearing = calculate_angle(point , new_point1)
        print(f'P1 : ({x1, y1}), d= {distance} thet = {degrees(bearing)}도')
        print(f'P2 : {x2, y2}, d= {distance} thet = {angle}도')
        
        # 새로 생성된 두 점이 유효한지를 검사합니다.
        # 이 조건을 추가하여 두 점이 올바르게 생성되었는지 확인할 수 있습니다.
        if new_point1.distance(point) >= min_distance and new_point2.distance(point) >= min_distance:
            return new_point1, new_point2

def adjust_linestring_with_passpoints(adjusted_linestring, passpoint_coordinates):
    for pass_point in passpoint_coordinates:
        adjusted_linestring = adjust_linestring_for_passpoint(adjusted_linestring, pass_point)
    return adjusted_linestring

def calculate_angle_difference(angle1, angle2):
    """두 각도 간의 차이를 계산합니다."""
    angle_diff = abs(angle1 - angle2)
    # 각도 차이를 360도 이하로 조정
    if angle_diff > 180:
        angle_diff = 360 - angle_diff
    return angle_diff

def are_directions_similar(angle1, angle2, threshold=10):
    """두 각도의 방향이 비슷한지 확인합니다."""
    angle_diff = calculate_angle_difference(angle1, angle2)
    return angle_diff <= threshold

def generate_random_linestring_for_passpoint(start, end, passpoints, max_points, min_distance, max_distance):
    lines = []
    points = [start]
    
    # Process each passpoint
    for i in range(len(passpoints) -1):
        p1, p2 = generate_random_line(passpoints[i], min_distance, max_distance)
        p3, p4 = generate_random_line(passpoints[i+1], min_distance, max_distance)
        
        lines.append(p1)
        lines.append(p2)

        #linrs = generate_random_linestring_within_radius(p2, p3, max_points, min_distance, max_distance, min_end_distance=2000)

    # Create final line
    combined_line = []
    
    # Ensure the start and end points are included
    combined_line = [start.coords[0]] + lines + [end.coords[0]]
    
    return LineString(combined_line)

# 테스트 데이터
start = Point(197420.4322, 550432.6777)  # 서울역
end = Point(263099.771, 587456.6810)     # 춘천역
passpoints = [
    Point(204230.3944, 553388.0212),
    Point(221501.014084, 561525.650902),
    Point(237592.184773, 570749.661709)
    ]

initialize_parameters()

# 선형 시각화
fig, ax = plt.subplots(figsize=(8, 6))

# 랜덤 선형 생성
# Generate random linestring
line = generate_random_linestring_for_passpoint(start, end, passpoints, max_points, min_distance, max_distance)

#경유지 선 시각화
for i in range(len(passpoints)):
    p1,p2 = generate_random_line(passpoints[i], min_distance, max_distance)
    NL = LineString([p1,p2])
    x2, y2 = NL.xy
    ax.plot(x2, y2, color='k')
    # Plot start point of the line
    ax.plot(NL.coords[0][0], NL.coords[0][1], 'go')

    # Plot end point of the line
    ax.plot(NL.coords[1][0], NL.coords[1][1], 'ro')







# 원본 선형 그리기
x, y = line.xy
ax.plot(x, y, color='blue', label='Generated LineString')




# 시작점, 종료점 및 경유점 표시
ax.plot(start.x, start.y, 'go', label='Start Point')
ax.plot(end.x, end.y, 'ro', label='End Point')
ax.plot(*zip(*[(p.x, p.y) for p in passpoints]), 'mo')

# 경유점에 "s" 텍스트 추가
ax.text(start.x, start.y, '서울역', fontsize=12, ha='right')
ax.text(start.x, start.y, f'{x[0],y[0]}', fontsize=12, ha='left')
ax.text(passpoints[0].x, passpoints[0].y, '청량리역', fontsize=12, ha='right')
ax.text(passpoints[1].x, passpoints[1].y, '평내호평역', fontsize=12, ha='right')
ax.text(passpoints[2].x, passpoints[2].y, '가평역', fontsize=12, ha='right')
ax.text(end.x, end.y, '춘천역', fontsize=12, ha='right')
ax.text(end.x, end.y, f'{x[-1],y[-1]}', fontsize=12, ha='left')

# 그래프 레이아웃 설정
ax.set_xlabel('X Coordinate')
ax.set_ylabel('Y Coordinate')
ax.set_title('Generated LineString with Pass Points')
ax.legend()
ax.grid(True)

plt.show()
