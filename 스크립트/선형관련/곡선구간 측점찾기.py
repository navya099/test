import numpy as np
import math
import matplotlib.pyplot as plt
from tkinter import *

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

def update_plot():
    global sta3
    global ax
    
    find_sta = float(entry.get())
     # 입력값의 범위를 확인하여 sta1과 sta3 사이에 있는지 검사
    if not (sta1 <= find_sta <= sta3):
        print("입력값이 범위를 벗어납니다.")
        return
    
    # 세 점을 사용하여 원의 중심점과 반지름을 찾음
    center, radius = find_circle_parameters(point1, point2, point3)
    start_angle = find_start_angle(center, point3)
    start_angle_degree = math.degrees(start_angle)

    # 주어진 길이만큼 회전한 각도 계산 (단위: 라디안)
    given_length = (sta3 - find_sta)
    angle = given_length / radius

    # 호의 중심점에서 주어진 길이만큼 회전한 각도에 해당하는 호 위의 점을 찾음
    point_on_arc = find_point_on_arc(center, radius, start_angle, angle)

    # 결과 출력
    print("호의 중심점:", center)
    print("반지름:", radius)
    print("시작각도:", start_angle_degree)
    print("주어진 길이만큼 회전한 후의 호 위의 점:", point_on_arc)

    # 측점과 호 위의 점의 좌표
    find_sta_coord = point_on_arc

    # 그래프 업데이트
    ax.clear()
    ax.scatter(*zip(*[point1,point2,point3]), marker='o', label='Stations')
    ax.scatter(*zip(*[point_on_arc]), marker='x', label='dest')

    ax.text(*point1,sta1,ha='left',color='red')
    ax.text(*point2,sta2,ha='left',color='red')
    ax.text(*point3,sta3,ha='left',color='red')

    ax.text(*point_on_arc,str(find_sta),ha='left',color='blue')

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Stations and Points on Arc')
    ax.legend()
    ax.grid(True)
    ax.axis('equal')
    plt.draw()
    plt.pause(0.01)


# 예시 데이터
point1 = (192315.867143228, 555061.364099226) # 10150
point2 = (192962.307552105, 556214.466436408) # 11550
point3 = (193243.230742163, 556317.492582416) # 11850

sta1 = 10150
sta2 = 11550
sta3 = 11850

# 세 점을 사용하여 원의 중심점과 반지름을 찾음
center, radius = find_circle_parameters(point1, point2, point3)
start_angle = find_start_angle(center, point3)

# 그래프 초기화
fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(*zip(*[point1,point2,point3]), marker='o', label='Stations')

# 측점 입력 창
root = Tk()
root.title("Arc Calculator")
label = Label(root, text="측점 입력:")
label.pack()

entry = Entry(root)
entry.pack()

# 버튼 추가
button = Button(root, text="계산 및 플로팅", command=update_plot)
button.pack()

root.mainloop()
