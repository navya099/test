import win32pipe, win32file
import matplotlib.pyplot as plt
import re
import os


# 선형 좌표 리스트 읽기
def read_polyline(file_path):
    points = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            try:
                x, y, z = map(float, line.strip().split(','))
                points.append((x, y, z))
            except ValueError:
                pass  # 잘못된 줄 무시
    return points


# 폴더 설정
path = r'c:\temp\지하철'

# 폴더 내 모든 txt 파일 수집
collect_file = [os.path.join(path, file) for file in os.listdir(path) if file.endswith('.txt')]
collect_list = []
for file in collect_file:
    polyline = read_polyline(file)
    collect_list.append(polyline)

# 파이프 연결
print("파이프 연결 시도 중...")
pipe = win32file.CreateFile(
    r'\\.\pipe\VehicleDataPipe',
    win32file.GENERIC_READ,
    0, None,
    win32file.OPEN_EXISTING,
    0, None
)

print("파이프 연결 성공, 데이터 수신 시작...")

# 플롯 초기화
plt.ion()
fig, ax = plt.subplots()

# 폴리선은 한번만 그린다
for polyline in collect_list:
    x_poly, y_poly = zip(*[(p[0], p[1]) for p in polyline])
    ax.plot(x_poly, y_poly, 'b-', label="폴리선")

# 차량 점 (scatter) 생성 - 최초엔 임의 값
vehicle_point, = ax.plot([], [], 'ro', markersize=8, label="Vehicle Path")

ax.set_xlabel('X 좌표')
ax.set_ylabel('Y 좌표')
ax.set_title('Vehicle Path (X, Y)')
ax.legend()
ax.set_aspect('equal')
plt.show()

# 차량 중심으로 보여줄 범위 설정 (ex: 100m x 100m)
view_range = 50  # 차량 중심에서 좌우로 50m, 총 100m

try:
    while True:
        result, data = win32file.ReadFile(pipe, 4096)
        received_data = data.decode("utf-8").strip()

        print(f"수신된 데이터: {received_data}")

        # 위치와 좌표를 추출하는 정규표현식
        match = re.search(r'X=([\-+]?\d*\.\d+|\d+),\s*Y=([\-+]?\d*\.\d+|\d+)', received_data)
        if match:
            x = float(match.group(1))
            y = float(match.group(2))

            # 기존 점을 갱신
            vehicle_point.set_data(x, y)

            # 화면 업데이트
            # 차량 좌표를 중심으로 화면 범위 재설정
            ax.set_xlim(x - view_range, x + view_range)
            ax.set_ylim(y - view_range, y + view_range)
            
            fig.canvas.draw()
            fig.canvas.flush_events()
            plt.pause(0.01)

except KeyboardInterrupt:
    print("\n⛔ 수동 종료 (Ctrl+C)")
except Exception as e:
    print("❌ 에러 발생:", e)
finally:
    plt.ioff()
    plt.show()
