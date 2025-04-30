import random
from dataclasses import dataclass
import win32pipe, win32file
import matplotlib.pyplot as plt
import re
import os

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


class Vector3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

class Vector2:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

class Subway:
    def __init__(self, name, color, alignment, stations):
        self.name = name
        self.color = color
        self.alignment = alignment
        self.stations = stations


class Alignment:
    def __init__(self, coords):
        self.points = [AlignmentPoint(sta, Vector3(x, y, z)) for sta, x, y, z in coords]

class Station:
    def __init__(self, name, sta, coord):
        self.name = name
        self.sta = sta
        self.coord = coord

class Color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    @staticmethod
    def from_hex(hexcolor: str):
        hexcolor = hexcolor.lstrip('#')
        if len(hexcolor) != 6:
            raise ValueError("HEX 색상은 6자리여야 합니다.")
        r = int(hexcolor[0:2], 16)
        g = int(hexcolor[2:4], 16)
        b = int(hexcolor[4:6], 16)
        return Color(r, g, b)

    @staticmethod
    def get_random_color():
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        return Color(r, g, b)

@dataclass
class AlignmentPoint:
    station: int
    coord: Vector3

class SubwayColorMap:
    subway_color_map = {
        '1호선': '0052A4',
        '2호선': '00A84D',
        '3호선': 'EF7C1C',
        '4호선': '00A4E3',
        '5호선': '996CAC',
        '6호선': 'CD7C2F',
        '7호선': '747F00',
        '8호선': 'E6186C',
        '9호선': 'BDB092',
        '인천1호선': '759CCE',
        '인천2호선': 'F5A251',
        '경의중앙선': '77C4A3',
        '공항철도': '0090D2',
        '서해선': '8FC31F',
        '수인분당선': 'FABE00',
        '김포골드라인': 'AD8605',
        'GTX-A': '9A6292'
    }

    @classmethod
    def get_color(cls, name):
        hexcolor = cls.subway_color_map.get(name)
        if hexcolor:
            return Color.from_hex(hexcolor)
        else:
            return Color(r=128, g=128, b=128)  # 기본 회색

def read_polyline(file_path):
    points = []
    i = 0
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            try:
                parts = list(map(float, line.strip().split(',')))
                if len(parts) == 2:
                    x, y = parts
                    z = 0.0
                elif len(parts) == 3:
                    x, y, z = parts
                else:
                    continue  # 2개 또는 3개가 아니면 무시

                sta = i * 20
                points.append((sta, x, y, z))

            except ValueError:
                pass  # 잘못된 줄 무시

            i += 1
    return points

def read_station(file_path):
    points = []
    i = 0
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            try:
                if i != 0:
                    parts = line.strip().split(',')
                    if len(parts) == 4:
                        name = parts[0]
                        sta = float(parts[1])
                        x = float(parts[2])
                        y = float(parts[3])
                        points.append((name, sta, x, y))
            except ValueError:
                pass
            i += 1
    return points



# 폴더 설정
path = r'c:\temp\지하철'
station_path = path + r'\역'

# 폴더 내 모든 txt 파일 수집
collect_file = [os.path.join(path, file) for file in os.listdir(path) if file.endswith('.txt')]
# 파일 이름만 추출 + 확장자 제거
collect_file_names = [os.path.splitext(os.path.basename(file))[0] for file in collect_file]

#자선 선택
rail0 = '한국쾌속철도'

#클래스 인스턴스 생성
subways = []
for filename, file in zip(collect_file_names, collect_file):
    coords = read_polyline(file)
    alignment = Alignment(coords)
    color = SubwayColorMap.get_color(filename) if not filename == rail0 else Color(255, 0, 0)
    # 해당 노선의 역 파일 경로
    station_file = os.path.join(station_path, filename + ".txt")
    # 역 파일이 존재하면 읽기
    if os.path.exists(station_file):
        stations_data = read_station(station_file)
        stations = [Station(name=name, sta=sta, coord=Vector3(x=x, y=y, z=0)) for name, sta, x, y in stations_data]
    else:
        stations = []

    subway = Subway(name=filename, color=color, alignment=alignment, stations=stations)
    subways.append(subway)

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
# 플롯에 모든 노선 추가
for subway in subways:
    x_poly, y_poly = zip(*[(p.coord.x, p.coord.y) for p in subway.alignment.points])
    color = (subway.color.r/255, subway.color.g/255, subway.color.b/255)
    ax.plot(x_poly, y_poly, color=color, label=subway.name)

    if subway.stations:
        x_sta, y_sta = zip(*[(p.coord.x, p.coord.y) for p in subway.stations])
        ax.scatter(x_sta, y_sta, marker='o', s=25, c='r')
        for station in subway.stations:
            ax.text(station.coord.x, station.coord.y, station.name, fontsize=24, color=color)
# 차량 점 (scatter) 생성 - 최초엔 임의 값
vehicle_point, = ax.plot([], [], 'ro', markersize=8, label="Vehicle Path")

ax.set_xlabel('X 좌표')
ax.set_ylabel('Y 좌표')
ax.set_title('Vehicle Path (X, Y)')
ax.legend()
ax.set_aspect('equal')
plt.show()

# 차량 중심으로 보여줄 범위 설정 (ex: 100m x 100m)
view_range = 500  # 차량 중심에서 좌우로 50m, 총 100m

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
