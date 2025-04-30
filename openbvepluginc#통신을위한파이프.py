import random
import sys
from dataclasses import dataclass
import win32pipe, win32file
import re
import os


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



from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

# 클래스 정의 생략 (Vector3, AlignmentPoint, Station, Subway 등 기존 그대로 유지)

class VehiclePlotter(QtWidgets.QMainWindow):
    def __init__(self, subways):
        super().__init__()
        self.setWindowTitle("실시간 차량 위치")
        self.setGeometry(100, 100, 1200, 800)

        self.plot_widget = pg.PlotWidget()
        self.setCentralWidget(self.plot_widget)
        self.plot_widget.setAspectLocked(True)

        self.vehicle_plot = self.plot_widget.plot([], [], pen=None, symbol='o', symbolBrush='r', symbolSize=10)

        # 모든 노선 한 번만 그림
        for subway in subways:
            x_poly = [p.coord.x for p in subway.alignment.points]
            y_poly = [p.coord.y for p in subway.alignment.points]
            color = (subway.color.r, subway.color.g, subway.color.b)
            self.plot_widget.plot(x_poly, y_poly, pen=pg.mkPen(color=color, width=2))

            if subway.stations:
                x_sta = [s.coord.x for s in subway.stations]
                y_sta = [s.coord.y for s in subway.stations]
                self.plot_widget.plot(x_sta, y_sta, pen=None, symbol='o', symbolBrush='r', symbolSize=6)
                for s in subway.stations:
                    text = pg.TextItem(s.name, color=(subway.color.r, subway.color.g, subway.color.b))
                    text.setPos(s.coord.x, s.coord.y)
                    self.plot_widget.addItem(text)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_vehicle)
        self.timer.start(10)  # 100 FPS도 가능

        self.pipe = win32file.CreateFile(
            r'\\.\pipe\VehicleDataPipe',
            win32file.GENERIC_READ,
            0, None,
            win32file.OPEN_EXISTING,
            0, None
        )

    def update_vehicle(self):
        try:
            result, data = win32file.ReadFile(self.pipe, 4096)
            received_data = data.decode("utf-8").strip()

            match = re.search(r'X=([\-+]?\d*\.\d+|\d+),\s*Y=([\-+]?\d*\.\d+|\d+)', received_data)
            if match:
                x = float(match.group(1))
                y = float(match.group(2))
                self.vehicle_plot.setData([x], [y])
                self.plot_widget.setXRange(x - 250, x + 250)
                self.plot_widget.setYRange(y - 250, y + 250)

        except Exception as e:
            print("오류 발생:", e)


if __name__ == "__main__":
    # 지하철 데이터 로드 (read_polyline, read_station 등 기존 함수 사용)
    path = r'c:\temp\지하철'
    station_path = path + r'\역'
    rail0 = '한국쾌속철도'

    collect_file = [os.path.join(path, file) for file in os.listdir(path) if file.endswith('.txt')]
    collect_file_names = [os.path.splitext(os.path.basename(file))[0] for file in collect_file]

    subways = []
    for filename, file in zip(collect_file_names, collect_file):
        coords = read_polyline(file)
        alignment = Alignment(coords)
        color = SubwayColorMap.get_color(filename) if not filename == rail0 else Color(255, 0, 0)

        station_file = os.path.join(station_path, filename + ".txt")
        if os.path.exists(station_file):
            stations_data = read_station(station_file)
            stations = [Station(name=name, sta=sta, coord=Vector3(x=x, y=y, z=0)) for name, sta, x, y in stations_data]
        else:
            stations = []

        subway = Subway(name=filename, color=color, alignment=alignment, stations=stations)
        subways.append(subway)

    app = QtWidgets.QApplication(sys.argv)
    viewer = VehiclePlotter(subways)
    viewer.show()
    sys.exit(app.exec_())