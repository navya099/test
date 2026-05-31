import matplotlib.pyplot as plt
from shapely.geometry import LineString
from tkinter import Tk, ttk, filedialog, StringVar, END

plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False

# txt 파일에서 데이터 읽기
def read_data_from_txt():
    points = []
    filename = filedialog.askopenfilename() # Open file dialog
    if filename:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                parts = line.strip().split(',')
                curvetype = parts[0]
                cumulative_distance = float(parts[1])
                x = float(parts[2])
                y = float(parts[3])
                points.append((curvetype,cumulative_distance, x, y))
    return points

# 메인 계산 함수
def calcluate_xy(points,cumulative_distance):
    # 곡선 시작 및 종점 인덱스 찾기
    curve_start_index = None
    curve_end_index = None
    for i, (curvetype, sta, x, y) in enumerate(points):
        if curvetype == 'bc':  # 곡선 시작
            curve_start_index = i
        elif curvetype == 'ec':  # 곡선 종점
            curve_end_index = i
    
    # 누적거리 계산을 위한 이전 지점의 누적거리
    prev_cumulative_distance = None
    
    # 곡선 구간
    if curve_start_index is not None and curve_end_index is not None:
        # 곡선 구간 계산
        # 세 점을 사용하여 원의 중심점과 반지름을 찾음
        point1 = (points[curve_start_index][2], points[curve_start_index][3]) # 10150
        point2 = (points[curve_start_index + 1][2], points[curve_start_index + 1][3]) # 11550
        point3 = (points[curve_end_index][2], points[curve_end_index][3]) # 11850
        center, radius = find_circle_parameters(point1, point2, point3)

        start_angle = find_start_angle(center, point3)
        start_angle_degree = math.degrees(start_angle)

        sta1 = points[curve_start_index][1]
        sta3 = points[curve_end_index][1]
        # 주어진 길이만큼 회전한 각도 계산 (단위: 라디안)
        given_length = (sta3 - find_sta)
        angle = given_length / radius

        # 호의 중심점에서 주어진 길이만큼 회전한 각도에 해당하는 호 위의 점을 찾음
        x, y = find_point_on_arc(center, radius, start_angle, angle)
        
        return (x, y)

    # 직선 구간
    else:
        for i in range(1, len(points)):
            curvetype, sta, x, y = points[i]
            if curvetype in ['bc', 'ec']:
                continue
            
            if prev_cumulative_distance is None:
                prev_cumulative_distance = points[i - 1][1]
            
            if sta >= cumulative_distance:
                x1, y1 = points[i - 1][2], points[i - 1][3]
                x2, y2 = points[i][2], points[i][3]
                distance_ratio = (cumulative_distance - prev_cumulative_distance) / (sta - prev_cumulative_distance)
                x = x1 + (x2 - x1) * distance_ratio
                y = y1 + (y2 - y1) * distance_ratio
                return (x, y)
        
            prev_cumulative_distance = sta
        
        return None

# 누적 거리까지의 좌표 출력
def print_coordinates(cumulative_distance, coordinates):
    if coordinates:
        coordinate_str = ','.join(map(str, coordinates))
        print(f"누적 거리 {cumulative_distance}까지의 좌표: {coordinate_str}")
    else:
        print("누적 거리가 파일에 있는 데이터 범위를 벗어납니다.")
# linestring 그리기
def draw_linestring(points):
    line = LineString([(x, y) for a, _, x, y in points])
    x, y = line.xy
    plt.plot(x, y, 'b-', label='Linestring')  # 파란색 실선으로 linestring 그리기

# 세 점을 사용하여 원의 중심점과 반지름을 찾는 함수
def find_circle_parameters(point1, point2, point3):
    x1, y1 = point1
    x2, y2 = point2
    x3, y3 = point3
    A = np.array([[x3 - x1, y3 - y1], [x3 - x2, y3 - y2]])
    B = np.array([[(x3 ** 2 - x1 ** 2) + (y3 ** 2 - y1 ** 2)], [(x3 ** 2 - x2 ** 2) + (y3 ** 2 - y2 ** 2)]]) / 2
    try:
        center_x, center_y = np.linalg.solve(A, B)
    except np.linalg.LinAlgError:
        center_x, center_y = None, None
    radius = np.sqrt((x1 - center_x) ** 2 + (y1 - center_y) ** 2)
    return (center_x, center_y), radius

# 호의 중심점과 시작점으로 호의 시작 각도를 찾는 함수
def find_start_angle(center, start_point):
    center_x, center_y = center
    start_x, start_y = start_point
    return np.arctan2(start_y - center_y, start_x - center_x)

# 호의 중심점과 반지름을 기반으로 호 위의 점을 찾는 함수
def find_point_on_arc(center, radius, start_angle, angle):
    x = center[0] + radius * np.cos(angle + start_angle)
    y = center[1] + radius * np.sin(angle + start_angle)
    return x, y

# 입력 필드가 변경될 때마다 그래프 업데이트
def update_plot(event):
    cumulative_distance = float(entry.get())
    coordinates = None
    if points and points[0][1] <= cumulative_distance <= points[-1][1]:
        # 누적 거리가 파일에 있는 범위 내에 있는 경우 해당 좌표 반환
        coordinates = calcluate_xy(points, cumulative_distance)
    elif points and cumulative_distance > points[-1][1]:
        # 누적 거리가 파일에 있는 데이터 범위를 벗어나는 경우
        print('범위 에러')
    print_coordinates(cumulative_distance, coordinates)
    
    if coordinates:
        # 그래프 업데이트
        plt.cla()  # 기존 그래프 지우기
        draw_linestring(points)  # linestring 그리기
        plt.plot(*coordinates, 'ro', label='Point')  # 빨간색 점으로 좌표 표시

        # 누적 거리 텍스트 표시
        plt.text(coordinates[0], coordinates[1], f'측점: {cumulative_distance}', color='green')
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.title('Coordinates at Cumulative Distance')
        plt.grid(True)
        plt.legend()  # 범례 추가
        plt.draw()  # 그래프 다시 그리기

# 메인 함수
def main():
    global entry, points
    points = read_data_from_txt()  # 파일에서 데이터 읽기

    root = Tk()
    root.title("누적 거리 입력 및 그래프")

    # 입력 필드 추가
    label = ttk.Label(root, text="측점 입력:")
    label.pack()
    entry_var = StringVar()
    entry = ttk.Entry(root, textvariable=entry_var, width=20)
    entry.pack()
    entry.bind("<Return>", update_plot)  # 엔터 키로 업데이트

    # 초기 그래프 그리기
    draw_linestring(points)  # linestring 그리기
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Coordinates at Cumulative Distance')
    plt.grid(True)
    plt.legend()  # 범례 추가
    plt.show()

    root.mainloop()

if __name__ == "__main__":
    main()
