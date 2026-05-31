from shapely.geometry import LineString, Point
from shapely.ops import nearest_points
import numpy as np
import matplotlib.pyplot as plt
from tkinter import Tk
from tkinter.filedialog import askopenfilename,asksaveasfilename

# Tkinter root 창을 생성합니다.
root = Tk()
root.withdraw()

  
def get_segments(polyline):
    return list(zip(polyline[:-1], polyline[1:]))


def get_segment_direction(segment):
    dx = segment[1][0] - segment[0][0]
    dy = segment[1][1] - segment[0][1]
    return np.arctan2(dy, dx)

def calculate_distances(polyline1, polyline2):
    polyline1_segments = get_segments(polyline1)
    polyline2 = LineString(polyline2)
    distances = []
    intersections = []

    for i, segment in enumerate(polyline1_segments):
        direction = get_segment_direction(segment)
        segment_start = Point(segment[0])
        xline_start_point = Point(segment_start.x + np.cos(direction - np.pi/2) * -999999, segment_start.y + np.sin(direction - np.pi/2) * -999999)
        xline_end_point = Point(segment_start.x + np.cos(direction - np.pi/2) * 999999, segment_start.y + np.sin(direction - np.pi/2) * 999999)
        xline = LineString([xline_start_point, xline_end_point])

        intersection = xline.intersection(polyline2)
        if intersection.is_empty:
            distances.append('INFINITY')
            
        else:
            nearest_point_on_intersection = nearest_points(segment_start, intersection)[1]
            distances.append(segment_start.distance(nearest_point_on_intersection))
            intersections.append(nearest_point_on_intersection.coords[0])
            
        if i == len(polyline1_segments) - 1:
            segment_end = Point(segment[1])
            xline_start_point = Point(segment_end.x + np.cos(direction + np.pi/2) * -999999, segment_end.y + np.sin(direction + np.pi/2) * -999999)
            xline_end_point = Point(segment_end.x + np.cos(direction + np.pi/2) * 999999, segment_end.y + np.sin(direction + np.pi/2) * 999999)
            xline = LineString([xline_start_point, xline_end_point])

            intersection = xline.intersection(polyline2)
            
            if intersection.is_empty:
                distances.append('INFINITY')
            else:
                nearest_point_on_intersection = nearest_points(segment_end, intersection)[1]
                distances.append(segment_end.distance(nearest_point_on_intersection))
                intersections.append(nearest_point_on_intersection.coords[0])
                
    return distances ,intersections

# 폴리라인 좌표를 입력합니다.
# 파일 대화 상자를 통해 폴리라인 좌표 파일을 선택합니다.
input_file = askopenfilename(filetypes=[("텍스트 파일", "*.txt")])

if input_file:
    # 선택한 파일에서 폴리라인 좌표를 읽어옵니다.
    with open(input_file, "r") as file:
        lines = file.readlines()
    
    # 폴리라인 좌표와 측점 정보를 파싱하여 리스트로 저장합니다.
    polyline1 = []
    polyline1sta = []
    for line in lines:
        data = line.strip().split(",")
        x = float(data[1])
        y = float(data[2])
        point = (x, y)
        polyline1.append(point)
        polyline1sta.append(float(data[0]))

polyline2 = [(-215.9805,-118.7471), (48.7108, 365.7672)]
# 측점 간의 수직 거리를 계산합니다.
distances,intersections = calculate_distances(polyline1, polyline2)

# 거리값과 추가 정보를 저장할 텍스트 파일 경로를 대화식으로 선택합니다.
output_file = asksaveasfilename(defaultextension=".txt", filetypes=[("텍스트 파일", "*.txt")])

if output_file:
    # 거리값과 추가 정보를 텍스트 파일에 저장합니다.
    with open(output_file, "w") as file:
        for i, distance in enumerate(distances):
            if i == len(distances) - 1:
                file.write(f"{polyline1sta[i]},.railend 1;{distance};0;\n")
            else:
                file.write(f"{polyline1sta[i]},.rail 1;{distance};0;\n")
    
    print("거리값과 추가 정보가 성공적으로 텍스트 파일로 저장되었습니다.")
else:
    print("파일 선택이 취소되었습니다.")
    
# 폴리라인과 폴리라인2를 시각화합니다.
fig, ax = plt.subplots()
ax.plot(*zip(*polyline1), marker='o', color='red', label='Polyline 1')
ax.plot(*zip(*polyline2), marker='o', color='blue', label='Polyline 2')

#plot 시각화
# Plotting distances
'''
for i, j in enumerate(polyline1):
    ax.text(polyline1[i][0], polyline1[i][1], str(distances[i]), ha='center', va='center')
'''

# Create individual xline segments using polyline1 and intersections
xline_segments = []
for i, intersection in enumerate(intersections):
    if intersection is not None:
        segment = [polyline1[i], intersection]
        xline_segments.append(segment)

# Plot xline segments
for segment in xline_segments:
    segment_coords = list(zip(*segment))
    ax.plot(segment_coords[0], segment_coords[1], linestyle='--',marker='x', color='green')

# 폴리라인 좌표를 기반으로축 범위를 설정합니다.
min_x = min(min(x for x, _ in polyline1), min(x for x, _ in polyline2))
max_x = max(max(x for x, _ in polyline1), max(x for x, _ in polyline2))
min_y = min(min(y for _, y in polyline1), min(y for _, y in polyline2))
max_y = max(max(y for _, y in polyline1), max(y for _, y in polyline2))
ax.set_xlim(min_x - 100, max_x + 100)
ax.set_ylim(min_y - 100, max_y + 100)

# xy 스케일을 1:1로 설정
ax.axis('equal')

ax.legend()
plt.show()

