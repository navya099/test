import random
import sys
from dataclasses import dataclass
import win32pipe, win32file
import re
import os
import time

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
            return Color.get_random_color() # 기본 회색

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



from PyQt5 import QtWidgets, QtCore, QtGui  # QtGui 추가
import pyqtgraph as pg

# 클래스 정의 생략 (Vector3, AlignmentPoint, Station, Subway 등 기존 그대로 유지)
class PipeReader(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str)

    def __init__(self, pipe_name, parent=None):
        super().__init__(parent)
        self.pipe_name = pipe_name
        self._running = True

    def run(self):
        try:
            pipe = win32file.CreateFile(
                self.pipe_name,
                win32file.GENERIC_READ,
                0, None,
                win32file.OPEN_EXISTING,
                0, None
            )
            while self._running:
                result, data = win32file.ReadFile(pipe, 4096)
                decoded = data.decode("utf-8").strip()
                self.data_received.emit(decoded)
        except Exception as e:
            print("파이프 오류:", e)

    def stop(self):
        self._running = False
        self.quit()
        self.wait()

class VehiclePlotter(QtWidgets.QMainWindow):
    def __init__(self, subways):
        super().__init__()
        self.setWindowTitle("실시간 차량 위치")
        self.setGeometry(100, 100, 1200, 800)

        # 중앙 위젯 생성
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        # 수직 레이아웃
        layout = QtWidgets.QVBoxLayout(central_widget)

        # 버튼 추가
        button_layout = QtWidgets.QHBoxLayout()
        zoom_in_btn = QtWidgets.QPushButton("Zoom In")
        zoom_out_btn = QtWidgets.QPushButton("Zoom Out")
        reset_btn = QtWidgets.QPushButton("Reset View")
        button_layout.addWidget(zoom_in_btn)
        button_layout.addWidget(zoom_out_btn)
        button_layout.addWidget(reset_btn)
        layout.addLayout(button_layout)

        # 그래프 위젯 추가
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)
        self.plot_widget.setAspectLocked(True)

        # 버튼 추가 (기존 코드에서 아래 부분에 추가)
        self.follow_checkbox = QtWidgets.QCheckBox("차량 따라가기")
        self.follow_checkbox.setChecked(True)  # 기본으로 따라감
        button_layout.addWidget(self.follow_checkbox)

        # 상태 표시줄 (좌표, 속도, FPS)
        self.status_layout = QtWidgets.QHBoxLayout()
        self.coord_label = QtWidgets.QLabel("X: -, Y: -")
        self.speed_label = QtWidgets.QLabel("속도: - km/h")
        self.fps_label = QtWidgets.QLabel("FPS: -")
        self.pos_label = QtWidgets.QLabel('위치')

        # 폰트 설정 코드 정리
        font = QtGui.QFont()
        font.setPointSize(10)
        for label in [self.coord_label, self.speed_label, self.fps_label, self.pos_label]:
            label.setFont(font)
            self.status_layout.addWidget(label)

        layout.addLayout(self.status_layout)

        # 노선 데이터 그리기
        self.subways = subways
        self.draw_static_lines()

        # 차량 점 초기화
        self.vehicle_plot = self.plot_widget.plot([], [], pen=None, symbol='o', symbolBrush='r', symbolSize=10)

        # 기본 보기 범위 저장
        self.default_x_range = self.plot_widget.viewRange()[0]
        self.default_y_range = self.plot_widget.viewRange()[1]

        # 줌 버튼 연결
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_out_btn.clicked.connect(self.zoom_out)
        reset_btn.clicked.connect(self.reset_view)

        self.pipe_reader = PipeReader(r'\\.\pipe\VehicleDataPipe')
        self.pipe_reader.data_received.connect(self.handle_pipe_data)
        self.pipe_reader.start()

        self.last_time = time.time()

    def closeEvent(self, event):
        # 창 종료 시 스레드 정리
        self.pipe_reader.stop()
        super().closeEvent(event)

    def handle_pipe_data(self, received_data):
        try:
            parts = received_data.split(',')
            if len(parts) != 5:
                return
            location = float(parts[0])
            speed = float(parts[1])
            x = float(parts[2])
            y = float(parts[3])
            z = float(parts[4])

            now = time.time()
            dt = now - self.last_time
            self.last_time = now
            fps = 1.0 / dt if dt > 0 else 0

            self.vehicle_plot.setData([x], [y])
            self.coord_label.setText(f"X={x:.4f}, Y={y:.4f}, Z={z:.2f}")
            self.speed_label.setText(f"속도: {speed:.1f} km/h")
            self.fps_label.setText(f"FPS: {fps:.2f}")
            self.pos_label.setText(f'위치: {location:.2f}')

            if self.follow_checkbox.isChecked():
                vb = self.plot_widget.getViewBox()
                vb.setRange(xRange=(x - 250, x + 250), yRange=(y - 250, y + 250), padding=0)

        except Exception as e:
            print("데이터 처리 오류:", e)

    def draw_static_lines(self):
        for subway in self.subways:
            x_poly = [p.coord.x for p in subway.alignment.points]
            y_poly = [p.coord.y for p in subway.alignment.points]
            color = (subway.color.r, subway.color.g, subway.color.b)
            self.plot_widget.plot(x_poly, y_poly, pen=pg.mkPen(color=color, width=2))

            if subway.stations:
                x_sta = [s.coord.x for s in subway.stations]
                y_sta = [s.coord.y for s in subway.stations]
                self.plot_widget.plot(x_sta, y_sta, pen=None, symbol='o', symbolBrush='r', symbolSize=6)
                for s in subway.stations:
                    text = pg.TextItem(s.name, color=color)
                    text.setPos(s.coord.x, s.coord.y)
                    self.plot_widget.addItem(text)

    # 줌 및 뷰 컨트롤 함수들
    def zoom_in(self):
        vb = self.plot_widget.getViewBox()
        vb.scaleBy((0.8, 0.8))  # 축소 => 줌 인

    def zoom_out(self):
        vb = self.plot_widget.getViewBox()
        vb.scaleBy((1.25, 1.25))  # 확대 => 줌 아웃

    def reset_view(self):
        vb = self.plot_widget.getViewBox()
        vb.autoRange()

if __name__ == "__main__":
    # ===== 노선 데이터 불러오기 (read_polyline 등은 그대로 사용) =====
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