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

# 오프셋 값 입력 받기
offset = float(input("오프셋 값을 입력하세요: "))

# 오프셋 방향 설정
if offset >= 0:
    direction = 'right'
else:
    direction = 'left'

# 오프셋 적용
offset_line = line.parallel_offset(abs(offset), direction, join_style=2)

# 좌표를 문자열로 변환하여 파일에 저장
with open(export_path, 'w') as export_file:
    for point in offset_line.coords:
        x, y = point
        export_file.write(f"{x}, {y}\n")

# Plot original line
plt.plot(*line.xy, color='blue', linewidth=1, label='Original Line')

# Plot offset line
plt.plot(*offset_line.xy, color='red', linewidth=1, label='Offset Line')

# Add legend
plt.legend()

# Get the x and y coordinates of the line and offset line
x_coords = [coord[0] for coord in line.xy]
y_coords = [coord[1] for coord in line.xy]
offset_x_coords = [coord[0] for coord in offset_line.xy]
offset_y_coords = [coord[1] for coord in offset_line.xy]

# 마우스 커서를 사용하여 점 좌표 스냅
cursor = mplcursors.cursor(hover=True)
cursor.connect(
    "add",
    lambda sel: sel.annotation.set_text(f"{sel.target[0]:.2f}, {sel.target[1]:.2f}")
)

# Show the plot
plt.show()
