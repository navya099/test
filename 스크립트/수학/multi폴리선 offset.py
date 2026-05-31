from matplotlib import pyplot as plt
from shapely.geometry import LineString
from descartes import PolygonPatch
import mplcursors

# 파일 경로
file_path = 'coords.txt'
export_path = 'export.txt'

# 좌표를 저장할 리스트
coords = []

# 파일에서 좌표 읽기
with open(file_path, 'r') as file:
    for line in file:
        x, y = line.strip().split(',')
        coords.append((float(x.strip()), float(y.strip())))

# LineString 생성
line = LineString(coords)

# 각 구간에 대한 offset 값을 리스트로 정의
offset_values = [float(val) for val in input("각 구간별 오프셋 값을 입력하세요 (구간 사이에 공백으로 구분): ").split()]

# 각 구간에 대한 LineString 객체와 offset을 적용하여 결과를 저장할 리스트
offset_lines = []

# 구간별로 offset을 적용한 LineString 생성
for i in range(len(coords) - 1):
    segment = LineString(coords[i:i+2])
    offset = offset_values[i]
    direction = 'right' if offset >= 0 else 'left'
    offset_line = segment.parallel_offset(abs(offset), direction, join_style=2)
    offset_lines.append(offset_line)

# 맨 처음 구간의 시작점과 마지막 구간의 끝점만 남기고 모두 제거
offset_lines = [offset_lines[0], offset_lines[-1]]

# 각 구간별로 선을 fillet 후 결합된 좌표 추출
fillet_coords = []

for i in range(len(offset_lines) - 1):
    line1 = offset_lines[i]
    line2 = offset_lines[i + 1]

    # Calculate intersection using algebraic approach
    line1_coords = line1.coords
    x1, y1 = line1_coords[0]
    x2, y2 = line1_coords[1]
    m1 = (y2 - y1) / (x2 - x1)
    b1 = y1 - m1 * x1

    line2_coords = line2.coords
    x1, y1 = line2_coords[0]
    x2, y2 = line2_coords[1]
    m2 = (y2 - y1) / (x2 - x1)
    b2 = y1 - m2 * x1

    x = (b2 - b1) / (m1 - m2)
    y = m1 * x + b1

    fillet_coords.append((x, y))

# 새로운 LineString 생성
new_line = LineString([offset_lines[0].coords[0]] + fillet_coords + [offset_lines[-1].coords[-1]])

# 좌표를 문자열로 변환하여 파일에 저장
with open(export_path, 'w') as export_file:
    for coord in new_line.coords:
        x, y = coord
        export_file.write(f"{x}, {y}\n")

# Plot original line
plt.plot(*line.xy, color='blue', linewidth=1, label='Original Line')

# Plot offset lines for each segment
for offset_line in offset_lines:
    plt.plot(*offset_line.xy, linewidth=1)

# Plot fillet points
fillet_x = [coord[0] for coord in fillet_coords]
fillet_y = [coord[1] for coord in fillet_coords]
plt.scatter(fillet_x, fillet_y, color='red', label='Fillet Points')

# Plot new line
plt.plot(*new_line.xy, color='green', linewidth=1, label='New Line')

# Add legend
plt.legend()

# Show plot
plt.show()
