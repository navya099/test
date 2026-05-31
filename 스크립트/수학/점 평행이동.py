import csv
import math
import os
from tkinter import Tk
from tkinter.filedialog import askopenfilename

def translate_polyline(points_list, dx, dy):
    translated_points = []
    for point in points_list:
        if len(point) >= 3:  # 유효한 좌표인지 확인
            x, y = point[1], point[2]  # 두 번째 열이 X 좌표, 세 번째 열이 Y 좌표
            translated_x = x + dx
            translated_y = y + dy
            translated_points.append((point[0], translated_x, translated_y))
    return translated_points

def rotate_point(x, y, center_x, center_y, angle):
    # 기준점을 중심으로 점을 회전시키는 함수
    angle_rad = math.radians(angle)
    translated_x = x - center_x
    translated_y = y - center_y
    rotated_x = translated_x * math.cos(angle_rad) - translated_y * math.sin(angle_rad)
    rotated_y = translated_x * math.sin(angle_rad) + translated_y * math.cos(angle_rad)
    new_x = rotated_x + center_x
    new_y = rotated_y + center_y
    return new_x, new_y

def mirror_points_x_axis(points_list):
    mirrored_points = []
    for point in points_list:
        if len(point) >= 3:  # 유효한 좌표인지 확인
            x, y = point[1], point[2]  # 두 번째 열이 X 좌표, 세 번째 열이 Y 좌표
            mirrored_y = -y  # y좌표를 반전시킴
            mirrored_points.append((point[0], x, mirrored_y))
    return mirrored_points

# CSV 파일 선택
Tk().withdraw()
csv_file = askopenfilename(filetypes=[("CSV Files", "*.csv")])

points_list = []
with open(csv_file, 'r') as file:
    csv_reader = csv.reader(file)
    for row in csv_reader:
        try:
            x, y = map(float, row[1:3])  # 두 번째 열이 X 좌표, 세 번째 열이 Y 좌표
            points_list.append((row[0], x, y))
        except ValueError:
            print("Invalid coordinate found. Skipping the row.")

# 이동 변위 입력 받기
dx = float(input("Enter translation along x-axis: "))
dy = float(input("Enter translation along y-axis: "))

# 회전 각도 입력 받기
rotation_angle = float(input("Enter rotation angle (in degrees): "))

# x축 대칭 수행
mirrored_polyline = mirror_points_x_axis(points_list)

# 폴리선 평행 이동 수행
translated_polyline = translate_polyline(mirrored_polyline, dx, dy)

# 회전 변환 수행
rotated_polyline = []
center_x = dx  # 회전 중심 X 좌표
center_y = dy  # 회전 중심 Y 좌표
for point in translated_polyline:
    x, y = point[1], point[2]
    rotated_x, rotated_y = rotate_point(x, y, center_x, center_y, rotation_angle)
    rotated_polyline.append((point[0], rotated_x, rotated_y))

# coord_convert_export.txt 파일의 저장 경로 생성
output_file = os.path.join(os.path.dirname(csv_file), "coord_convert_export.txt")

# 결과를 coord_convert_export.txt 파일로 내보내기
with open(output_file, 'w') as file:
    for point in rotated_polyline:
        file.write(f"{point[0]},{point[1]},{point[2]}\n")

print(f"Results exported to {output_file}")
