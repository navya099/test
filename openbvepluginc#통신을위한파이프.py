import win32pipe, win32file
import matplotlib.pyplot as plt
import re

#선형 좌표 리스트
def read_polyline(file_path):
    points = []
    with open(file_path, 'r') as file:
        for line in file:
            # 쉼표로 구분된 값을 읽어서 float로 변환
            x, y, z = map(float, line.strip().split(','))
            points.append((x, y, z))
    return points

def load_coordinates():
    """BVE 좌표 데이터를 텍스트 파일에서 불러오는 함수"""
    coord_filepath = 'c:/temp/bve_coordinates.txt'
    return read_polyline(coord_filepath)

polyline = load_coordinates()
# 폴리선 좌표 분리
x_poly, y_poly = zip(*[(-p[1], p[0]) for p in polyline])
        
        
        
        
print("파이프 연결 시도 중...")
pipe = win32file.CreateFile(
    r'\\.\pipe\VehicleDataPipe',
    win32file.GENERIC_READ,
    0, None,
    win32file.OPEN_EXISTING,
    0, None)

print("파이프 연결 성공, 데이터 수신 시작...")

x_coords = []  # X 좌표 리스트
y_coords = []  # Y 좌표 리스트


try:
    while True:
        result, data = win32file.ReadFile(pipe, 4096)
        received_data = data.decode("utf-8").strip()
        
        print(f"수신된 데이터: {received_data}")

        # 위치와 좌표를 추출하는 정규 표현식
        match = re.search(r'X=([\-+]?\d*\.\d+|\d+), Y=([\-+]?\d*\.\d+|\d+)', received_data)
        if match:
            x = float(match.group(1))
            y = float(match.group(2))

            #x_coords.append(x)

            #y_coords.append(y)

            # 데이터 시각화
            plt.clf()  # 이전 플롯을 지우고
            plt.plot(x_poly, y_poly, 'b-', label="폴리선")
            plt.scatter(x, y, marker='o', color='b', label="Vehicle Path")
            plt.xlabel('X 좌표')
            plt.ylabel('Y 좌표')
            plt.title('Vehicle Path (X, Y)')
            plt.legend(loc='best')
            plt.pause(0.1)  # 데이터 수신 시마다 잠시 기다리며 업데이트

except Exception as e:
    print("❌ 파이프 연결 종료:", e)
finally:
    plt.show()  # 프로그램 종료 시 플롯을 보여줌
