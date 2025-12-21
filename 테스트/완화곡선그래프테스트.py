import sys
import math
import numpy as np
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
from utils import format_distance
from data.alignment.geometry.spiral.params import TransitionCurveParams
from line import Line2d
from math_utils import degrees_to_dms
from point2d import Point2d
from curvedirection import CurveDirection

# --- 클로소이드 함수 ---
def clothoid(s, a):
    if s == 0 or a == 0:
        return 0, 0
    l = s / a
    r = 1 / l
    x = l * (1 - ((l**2)/(40*r**2)) + ((l**4)/(3456*r**4)) - ((l**6)/(599040*r**6)))
    y = (l**2)/(6*r) * (1 - ((l**2)/(56*r**2)) + ((l**4)/(7040*r**4)) - ((l**6)/(1612800*r**4)))
    return x * a, y * a

def global_xy_cls(s, a, origin, origin_az, isexit=False, dir=CurveDirection.LEFT):
    x, y = clothoid(s, a)
    if isexit:
        x = -x
    if dir == CurveDirection.RIGHT:
        y = -y
    ca = math.cos(origin_az)
    sa = math.sin(origin_az)
    gx = origin.x + x * ca - y * sa
    gy = origin.y + x * sa + y * ca
    return Point2d(gx, gy)

def cubic_local_xy(s: float ,R, L ,X1) -> tuple:
    """3차포물선 완화곡선 로컬좌표 (x, y) 계산"""

    x = s - (s**5) / (40 * R * R * (L**2))
    y = (x**3) / (6 * R * X1) if X1 != 0 else 0

    return x, y

#3차폼루선
def cubic_global_xy(s, R, L ,X1 ,dir, origin: Point2d, origin_az: float, isexit=False) -> Point2d:
    """로컬좌표(x,y)를 글로벌 좌표로 변환하여 실제 점 반환"""
    x, y = cubic_local_xy(s, R, L ,X1)
    if isexit:
        x = -x
    if dir == CurveDirection.RIGHT:
        y = -y

    ca = math.cos(origin_az)
    sa = math.sin(origin_az)

    gx = origin.x + x * ca - y * sa
    gy = origin.y + x * sa + y * ca

    return Point2d(gx, gy)

# --- 교점 계산 ---
def cal_intersect_point(line1: Line2d, line2: Line2d):
    """두 직선의 교점 계산"""
    x1, y1 = line1.start.x, line1.start.y
    x2, y2 = line1.end.x, line1.end.y
    x3, y3 = line2.start.x, line2.start.y
    x4, y4 = line2.end.x, line2.end.y

    denom = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
    if denom == 0:
        raise ValueError("두 직선이 평행하여 교점이 없습니다.")

    Px = ((x1*y2 - y1*x2)*(x3-x4) - (x1-x2)*(x3*y4 - y3*x4)) / denom
    Py = ((x1*y2 - y1*x2)*(y3-y4) - (y1-y2)*(x3*y4 - y3*x4)) / denom

    return Point2d(Px, Py)

#교각 계산
def cal_internal_angle(bp_coordinate, ip_coordinate, ep_coordinate):
    from math_utils import calculate_bearing
    v1 = calculate_bearing(bp_coordinate, ip_coordinate)
    v2 = calculate_bearing(ip_coordinate, ep_coordinate)
    # ±π 범위로 보정
    ia = v2 - v1
    if ia > math.pi:
        ia -= 2 * math.pi
    elif ia < -math.pi:
        ia += 2 * math.pi
    return abs(ia)

# --- 전체 좌표 계산 함수 ---
def calculate_curve(R, L1, L2, delta=0.1, h1: float = 0.0, BTC: Point2d = Point2d(0, 0), direction: CurveDirection = None, spiral_definination=''):
    """클로소이드+원곡선+ETC+IP 좌표 계산"""
    A1 = math.sqrt(R * L1)
    A2 = math.sqrt(R * L2)
    if spiral_definination == 'CLOTHOID':
        data = process_clothoid(R, L1, L2, A1, A2)

    elif spiral_definination == 'CUBIC':
        data = process_cubic(R, L1, L2)

    else:
        #data = process_sine(R, L1, L2, A1, A2)
        data = process_clothoid(R, L1, L2, A1, A2)
    # BCC 계산
    x1, y1 , x2, y2, t1, t2 = data
    BCC = BTC.moved(h1, x1)
    if direction == CurveDirection.LEFT:
        BCC.move(h1 + math.pi/2, y1)
    else:
        BCC.move(h1 - math.pi / 2, y1)
    # 원곡선 중심과 ECC 계산
    if direction == CurveDirection.LEFT:
        C = BCC.moved(t1 +  h1 + math.pi/2, R)
        ECC = C.moved(t1 + h1 - math.pi/2 + delta, R)
    else:
        C = BCC.moved(h1 - t1 - math.pi / 2, R)
        ECC = C.moved(h1 - t1 + math.pi / 2 - delta, R)

    # 원곡선 좌표
    theta_start = math.atan2(BCC.y - C.y, BCC.x - C.x)
    theta_end = math.atan2(ECC.y - C.y, ECC.x - C.x)
    theta_vals = np.linspace(theta_start, theta_end, 200)
    x_curve = C.x + R * np.cos(theta_vals)
    y_curve = C.y + R * np.sin(theta_vals)

    # ETC 계산
    if direction == CurveDirection.LEFT:
        tangent_angle = h1 + delta + t1 + t2
        ETC = ECC.moved(tangent_angle - math.pi /2 , y2)

    else:
        tangent_angle = h1 - delta - t1 - t2
        ETC = ECC.moved(tangent_angle + math.pi / 2, y2)

    ETC.move(tangent_angle, x2)

    # IP 계산
    h2 = tangent_angle + math.pi
    line1 = Line2d(BTC, BTC.moved(h1, 10000))
    line2 = Line2d(ETC, ETC.moved(h2, 10000))
    IP = cal_intersect_point(line1, line2)
    ia = cal_internal_angle(BTC,IP,ETC)

    # 시점부 좌표
    s_pos = np.linspace(0, L1, 500)
    x_in, y_in = [], []
    for s in s_pos:
        if spiral_definination == 'CLOTHOID':
            pt = global_xy_cls(s, A1, origin=BTC, dir=direction, isexit=False, origin_az=h1)
        elif spiral_definination == 'CUBIC':
            pt = cubic_global_xy(s,R,L1,x1,dir=direction, origin=BTC, origin_az=h1, isexit=False)
        else:
            pt = global_xy_cls(s, A1, origin=BTC, dir=direction, isexit=False, origin_az=h1)
        x_in.append(pt.x)
        y_in.append(pt.y)

    # 종점부 좌표
    s_pos2 = np.linspace(0, L2, 200)
    x_out, y_out = [], []
    for s in s_pos2:
        revs = L2 - s
        if spiral_definination == 'CLOTHOID':
            pt = global_xy_cls(revs, A2, origin=ETC, origin_az=tangent_angle, dir=direction, isexit=True)
        elif spiral_definination == 'CUBIC':
            pt = cubic_global_xy(revs, R, L2, x2, dir=direction, origin=ETC, origin_az=tangent_angle ,isexit=True)
        else:
            pt = global_xy_cls(revs, A2, origin=ETC, origin_az=tangent_angle, dir=direction, isexit=True)

        x_out.append(pt.x)
        y_out.append(pt.y)

    spec = cal_spec(R, L1, L2, delta, ia)

    # 점 이름 매핑
    POINT_KEYS = {
        'CLOTHOID': ['BTC', 'BCC', 'ECC', 'ETC'],
        'CUBIC': ['SP', 'PC', 'CP', 'PS'],
        'SINE': ['TS', 'SC', 'CS', 'ST']
    }

    keys = POINT_KEYS.get(spiral_definination, ['BTC', 'BCC', 'ECC', 'ETC'])
    point_values = [BTC, BCC, ECC, ETC]

    # 딕셔너리 생성
    data = {
        keys[0]: point_values[0],
        keys[1]: point_values[1],
        keys[2]: point_values[2],
        keys[3]: point_values[3],
        'IP': IP,
        'x_in': x_in, 'y_in': y_in,
        'x_curve': x_curve, 'y_curve': y_curve,
        'x_out': x_out, 'y_out': y_out,
        'L1': L1, 'L2': L2,
        'A1': A1, 'A2': A2,
        'R': R, 'spec': spec,
        'type': spiral_definination,
        'IA': ia,
        'H1': h1,
        'H2': h2,
        'direction': direction,
    }

    return data


def print_spec(specs: dict, spiral_definination: str):
    """
    cal_spec에서 반환된 딕셔너리를 한 줄씩 관련 값끼리 출력
    """
    print("\n----- 완화곡선 제원출력 -----")
    print(f"완화곡선 유형 : {spiral_definination}")
    print(f"L1, L2: {specs['L1']:.3f}, {specs['L2']:.3f}")
    print(f"A1, A2: {specs['A1']:.3f}, {specs['A2']:.3f}")
    print(f"x1, y1: {specs['x1']:.3f}, {specs['y1']:.3f}")
    print(f"x2, y2: {specs['x2']:.3f}, {specs['y2']:.3f}")
    print(f"t1, t2: {math.degrees(specs['t1']):.3f}, {math.degrees(specs['t2']):.3f}")
    print(f"xm1, xm2: {specs['xm1']:.3f}, {specs['xm2']:.3f}")
    print(f"dr1, dr2: {specs['dr1']:.3f}, {specs['dr2']:.3f}")
    print(f"w: {specs['w']:.3f}")
    print(f"z1, z2: {specs['z1']:.3f}, {specs['z2']:.3f}")
    print(f"d1, d2: {specs['d1']:.3f}, {specs['d2']:.3f}")
    print(f"lc: {specs['lc']:.3f}\n")



def print_coord(data):
    # 곡선 타입별 점 이름과 색상
    if data['type'] == 'CLOTHOID':
        points = [('BTC', data['BTC'], 'green'),
                  ('BCC', data['BCC'], 'orange'),
                  ('ECC', data['ECC'], 'purple'),
                  ('ETC', data['ETC'], 'brown')]

    elif data['type'] == 'CUBIC':
        points = [('SP', data['SP'], 'green'),
                  ('PC', data['PC'], 'orange'),
                  ('CP', data['CP'], 'purple'),
                  ('PS', data['PS'], 'brown')]
    else:
        points = [('TS', data['TS'], 'green'),
                  ('SC', data['SC'], 'orange'),
                  ('CS', data['CS'], 'purple'),
                  ('ST', data['ST'], 'brown')]

    print(f"\n{'-' * 4} 완화곡선 좌표출력 {'-' * 4}")
    for name, pt, color in points:
        print(f'{name}: X = {pt.x:.4f}, Y = {pt.y:.4f}')


def print_station(specs: dict, sp_type ,btc_sta = 0.0):

    bcc = btc_sta + specs['L1']
    ecc = bcc + specs['lc']
    etc = ecc + specs['L2']
    if sp_type == 'CLOTHOID':
        name = 'BTC', 'BCC', 'ECC', 'ETC'
    elif sp_type == 'CUBIC':
        name = 'SP', 'PC', 'CP', 'PS'
    else:
        name = 'TS', 'SC', 'CS', 'ST'
    print(f"\n{'-' * 4} 완화곡선 측점출력 {'-' * 4}")
    print(f"{name[0]}: {format_distance(btc_sta)}")
    print(f"{name[1]}: {format_distance(bcc)}")
    print(f"{name[2]}: {format_distance(ecc)}")

    print(f"{name[3]}: {format_distance(etc)}")

def print_ipinfo(data):
    print("\n----- IP 제원출력 -----")
    print(f"IP: X = {data['IP'].x:.4f}, Y = {data['IP'].y:.4f}")
    print(f"방위각 1: {degrees_to_dms(90 - math.degrees(data['H1']))}")
    print(f"방위각 2: {degrees_to_dms(270 - math.degrees(data['H2']))}")
    print(f"IA: {degrees_to_dms(math.degrees(data['IA']))}")
    print(f"{data['direction'].name} CURVE")

def cal_spec(R, L1, L2, delta ,ia):
    A1 = math.sqrt(R * L1)
    A2 = math.sqrt(R * L2)
    x1, y1 = clothoid(L1, A1)
    x2, y2 = clothoid(L2, A2)
    t1 = (L1) / (2 * R)
    t2 = (L2) / (2 * R)
    xm1 = x1 - (R * math.sin(t1))
    xm2 = x2 - (R * math.sin(t2))
    dr1 = y1 + (R * math.cos(t1)) - R
    dr2 = y2 + (R * math.cos(t2)) - R
    w = (R + dr1) * math.tan(ia / 2)
    z1 = (dr2 -dr1) * (1 / math.sin(ia))
    z2 = (dr2 -dr1) * (1 / math.tan(ia))
    d1 = xm1 + w + z1
    d2 = xm2 + w - z2
    lc = R * delta

    return {
        'L1': L1,
        'L2': L2,
        'A1': A1,
        'A2': A2,
        'x1': x1,
        'y1': y1,
        'x2': x2,
        'y2': y2,
        't1': t1,
        't2': t2,
        'xm1': xm1,
        'xm2': xm2,
        'dr1': dr1,
        'dr2': dr2,
        'w': w,
        'z1': z1,
        'z2': z2,
        'd1': d1,
        'd2': d2,
        'lc': lc
    }

def process_clothoid(R, L1, L2 ,A1, A2):
    x1, y1 = clothoid(L1, A1)
    x2, y2 = clothoid(L2, A2)
    t1 = (L1) / (2 * R)
    t2 = (L2) / (2 * R)

    return x1, y1, x2, y2, t1, t2
def process_cubic(R, L1, L2):
    x1 = TransitionCurveParams.solve_x1(L1, R)
    y1 = (x1 ** 2) / (6 * R)
    x2 = TransitionCurveParams.solve_x1(L2, R)
    y2 = (x2 ** 2) / (6 * R)
    t1 = math.atan(x1 / (2 * R))
    t2 = math.atan(x2 / (2 * R))

    return x1, y1, x2, y2, t1, t2

# --- PyQt5 GUI ---
class CurveApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.ip_line2 = None
        self.ip_line1 = None
        self.setWindowTitle("완화곡선 PyQtGraph 실시간 그래프")
        self.resize(1000, 600)

        layout = QtWidgets.QGridLayout(self)

        # 입력 위젯
        self.entries = {}
        labels = ["BTC X", "BTC Y", "L1", "L2", "R" , "DELTA", "H1" , "BTC STA"]
        defaults = [0, 0, 160, 320, 600, 0.1, 0 , 0]
        for i, (label, default) in enumerate(zip(labels, defaults)):
            layout.addWidget(QtWidgets.QLabel(label), i, 0)
            entry = QtWidgets.QLineEdit(str(default))
            self.entries[label] = entry
            layout.addWidget(entry, i, 1)
            entry.textChanged.connect(self.update_plot)

        # 곡선 방향
        layout.addWidget(QtWidgets.QLabel("Curve Direction"), 8, 0)
        self.direction_cb = QtWidgets.QComboBox()
        self.direction_cb.addItems(["L", "R"])
        layout.addWidget(self.direction_cb, 8, 1)
        self.direction_cb.currentIndexChanged.connect(self.update_plot)

        # 완화곡선 유형
        layout.addWidget(QtWidgets.QLabel("Spiral Type"), 9, 0)
        self.spiral_cb = QtWidgets.QComboBox()
        self.spiral_cb.addItems(["CLOTHOID", "CUBIC", "SINE"])
        layout.addWidget(self.spiral_cb, 9, 1)
        self.spiral_cb.currentIndexChanged.connect(self.update_plot)

        # PyQtGraph PlotWidget
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget, 0, 2, 20, 1)  # 오른쪽에 그래프 영역
        self.plot_widget.setAspectLocked(True)
        self.curve_in = self.plot_widget.plot(pen=pg.mkPen('b', width=2))
        self.circle = self.plot_widget.plot(pen=pg.mkPen('r', width=2))
        self.curve_out = self.plot_widget.plot(pen=pg.mkPen('b', width=2))
        self.scatter = pg.ScatterPlotItem(size=10, brush=pg.mkBrush(0, 255, 0))
        self.plot_widget.addItem(self.scatter)

        self.update_plot()

    def update_plot(self):
        try:
            BTCX = float(self.entries["BTC X"].text())
            BTCY = float(self.entries["BTC Y"].text())
            L1 = float(self.entries["L1"].text())
            L2 = float(self.entries["L2"].text())
            R = float(self.entries["R"].text())
            BTC = Point2d(BTCX, BTCY)
            h1 = float(self.entries["H1"].text())
            delta = float(self.entries["DELTA"].text())
            direction = CurveDirection.LEFT if self.direction_cb.currentText() == 'L' else CurveDirection.RIGHT
            spiral_definination = self.spiral_cb.currentText()
            btc_sta = float(self.entries["BTC STA"].text())
            data = calculate_curve(R=R, L1=L1, L2=L2, delta=delta, h1=h1, BTC=BTC ,direction=direction, spiral_definination=spiral_definination)

            print_ipinfo(data)
            print_spec(data['spec'], data['type'])
            print_station(data['spec'], data['type'] ,btc_sta)
            print_coord(data)

            self.plot_curve(data, btc_sta)
        except ValueError as e:
            print(f'에러 발생 {e}')  # 입력 중에 잘못된 값이 들어오면 무시

    def plot_curve(self, data ,btc_sta):
        #각 곡선 그래프
        self.curve_in.setData(data['x_in'], data['y_in'])
        self.circle.setData(data['x_curve'], data['y_curve'])
        self.curve_out.setData(data['x_out'], data['y_out'])

        btc = btc_sta
        bcc = btc + data['spec']['L1']
        ecc = bcc + data['spec']['lc']
        etc = ecc + data['spec']['L2']

        # 곡선 타입별 점 이름과 색상, 측점 값 매핑
        POINTS_MAP = {
            'CLOTHOID': [('BTC', 'green', btc), ('BCC', 'orange', bcc), ('ECC', 'purple', ecc), ('ETC', 'brown', etc)],
            'CUBIC': [('SP', 'green', btc), ('PC', 'orange', bcc), ('CP', 'purple', ecc), ('PS', 'brown', etc)],
            'SINE': [('TS', 'green', btc), ('SC', 'orange', bcc), ('CS', 'purple', ecc), ('ST', 'brown', etc)],
        }

        # 점 데이터 생성
        points = []
        for name, color, sta in POINTS_MAP.get(data['type'], []):
            pt = data.get(name)
            if pt is not None:
                # 이름에 시리얼 번호 추가
                name = f"{name} = {format_distance(sta)}"
                points.append((name, pt, color))

        # 공통적으로 IP는 항상 추가
        points.append(('IP', data['IP'], 'black'))

        # ScatterPlotItem 갱신
        self.scatter.setData(
            x=[pt.x for _, pt, _ in points],
            y=[pt.y for _, pt, _ in points],
            brush=[pg.mkBrush(color) for _, _, color in points],
            size=10
        )

        # 텍스트 처리
        if hasattr(self, 'text_items'):
            for item in self.text_items:
                self.plot_widget.removeItem(item)
        self.text_items = []
        for name, pt, color in points:
            text_item = pg.TextItem(text=name, color=color, anchor=(0, 0))
            text_item.setPos(pt.x, pt.y)
            self.plot_widget.addItem(text_item)
            self.text_items.append(text_item)

        # IP 라인 그리기
        # 기존 IP 라인 제거
        if hasattr(self, 'ip_line1'):
            self.plot_widget.removeItem(self.ip_line1)
        if hasattr(self, 'ip_line2'):
            self.plot_widget.removeItem(self.ip_line2)

        # 각 점 좌표 가져오기
        # 타입 가져오기
        curve_type = data['type']
        keys = POINTS_MAP.get(curve_type, ['BTC', 'BCC', 'ECC', 'ETC'])

        pt_start = data[keys[0][0]]  # BTC / SP / TS
        pt_middle1 = data[keys[1][0]]  # BCC / PC / SC
        pt_middle2 = data[keys[2][0]]  # ECC / CP / CS
        pt_end = data[keys[3][0]]  # ETC / PS / ST

        # IP 라인
        self.ip_line1 = pg.PlotDataItem([pt_start.x, data['IP'].x],
                                        [pt_start.y, data['IP'].y],
                                        pen=pg.mkPen('gray', width=1))

        self.ip_line2 = pg.PlotDataItem([data['IP'].x, pt_end.x],
                                        [data['IP'].y, pt_end.y],
                                        pen=pg.mkPen('gray', width=1))

        self.plot_widget.addItem(self.ip_line1)
        self.plot_widget.addItem(self.ip_line2)

        # IP 제원 문자
        y_offset = 0

        # 기존 아이템 제거
        if hasattr(self, 'ip_text'):
            self.plot_widget.removeItem(self.ip_text)

        # TextItem 생성
        self.ip_text = pg.TextItem(
            text=f"IP\n"
                 f"IA={degrees_to_dms(math.degrees(data['IA']))}\n"
                 f"R={data['R']}\n"
                 f"TL1={data['spec']['d1']:.3f}\n"
                 f"TL2={data['spec']['d2']:.3f}\n"
                 f"CL={data['L1'] + data['spec']['lc'] + data['L2']:.3f}\n"
                 f"X={data['IP'].x:.4f}\n"
                 f"Y={data['IP'].y:.4f}\n",
            color='w',  # 검은색
            anchor=(0, 0)  # 왼쪽 위 기준
        )
        self.ip_text.setPos(data['IP'].x, data['IP'].y + y_offset)  # 좌표 지정
        self.plot_widget.addItem(self.ip_text)

        #클로소이드 제원문자
        # --- 클로소이드 시작, 끝 중간점 좌표 ---
        y_offset = 20 #마진값
        mid_idx = len(data['x_in']) // 2
        mid_x_in = data['x_in'][mid_idx]
        mid_y_in = data['y_in'][mid_idx] + y_offset

        mid_idx_out = len(data['x_out']) // 2
        mid_x_out = data['x_out'][mid_idx_out]
        mid_y_out = data['y_out'][mid_idx_out] + y_offset

        # 기존 아이템 제거
        if hasattr(self, 'length_a_avalues'):
            for item in self.length_a_avalues:
                self.plot_widget.removeItem(item)
        self.length_a_avalues = []

        # 텍스트, 좌표, 색 지정
        texts = [f"L1={data['L1']}\nA1={data['A1']:.2f}", f"L2={data['L2']}\nA2={data['A2']:.2f}"]
        pts = [(mid_x_in, mid_y_in), (mid_x_out, mid_y_out)]
        colors = ['r', 'r']

        # 각 점마다 TextItem 생성
        for text, (x, y), color in zip(texts, pts, colors):
            item = pg.TextItem(text=text, color=color, anchor=(0, 0))
            item.setPos(x, y)
            self.plot_widget.addItem(item)
            self.length_a_avalues.append(item)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = CurveApp()
    win.show()
    sys.exit(app.exec_())
