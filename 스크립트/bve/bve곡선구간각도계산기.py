import math
import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
import ezdxf
from shapely.geometry import Point, LineString

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
import csv
import re

def read_stagger_csv(file_path):

        with open(file_path, 'r',encoding='utf-8') as file:
            lines = file.readlines()

        sections = []
        for line in lines:
            try:
                parts = line.strip().split(',')
                if len(parts) == 3:
                    post_number = parts[0]
                    station = float(parts[1].strip())
                    stagger = float(parts[2].strip())
                    sections.append((post_number, station,stagger) ) # Corrected order of z and y
            except ValueError:
                continue
        return sections


# ========================
# 유틸리티 함수
# ========================

def calculate_bearing(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return math.degrees(math.atan2(dy, dx))

def calculate_destination_coordinates(x1, y1, bearing, distance):
    angle = math.radians(bearing)
    x2 = x1 + distance * math.cos(angle)
    y2 = y1 + distance * math.sin(angle)
    return x2, y2

def read_polyline(file_path):
    points = []
    with open(file_path, 'r') as file:
        for line in file:
            x, y, z = map(float, line.strip().split(','))
            points.append((x, y, z))
    return points

def calculate_slope(h1: float, h2: float, gauge: float) -> float:
    """주어진 높이 차이와 수평 거리를 바탕으로 기울기(각도) 계산"""
    slope = (h2 - h1) / gauge  # 기울기 값 (비율)
    return math.degrees(math.atan(slope))  # 아크탄젠트 적용 후 degree 변환

def sort_and_save(coordinates, output_file, target_index=None):
    """
    rail 데이터를 rail별로 정렬해서 저장.
    target_index가 지정되면 해당 rail만 저장.
    """
    grouped = {}
    for railindex, x, y, z in coordinates:
        grouped.setdefault(railindex, []).append((railindex, x, y, z))

    with open(output_file, 'w') as f:
        # railindex 선택: 전체 or 특정 rail만
        indices = [target_index] if target_index is not None else sorted(grouped.keys())
        for railindex in indices:
            if railindex not in grouped:
                continue
            for railindex, x, y, z in grouped[railindex]:
                f.write(f"{x},{y},{z}\n")

def read_coordinates(file_path):
    coordinates = []
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) == 4:
                # rail 번호 추출 ("rail 26" → 26)
                match = re.search(r'\d+', parts[0])
                if not match:
                    continue
                railindex = int(match.group())
                x = float(parts[1].strip())
                y = float(parts[3].strip())
                z = float(parts[2].strip())
                coordinates.append((railindex, x, y, z))
    return coordinates

def calculate_side(bearing_angle, base_point, target_point):
    """
    기준 polyline의 진행 방향 각도와 대상 polyline 최근접점 벡터를 비교해 좌/우 판별.

    bearing_angle : float (라디안 단위 각도)
    base_point    : (x1, y1) 기준 polyline의 현재 점
    target_point  : (xt, yt) 대상 polyline 최근접점

    return: "왼쪽", "오른쪽", "겹침"
    """
    # 방향 벡터 (단위 벡터)
    vx, vy = math.cos(bearing_angle), math.sin(bearing_angle)
    # 대상점까지 벡터
    wx, wy = target_point[0] - base_point[0], target_point[1] - base_point[1]

    cross = vx * wy - vy * wx
    if cross > 0:
        return -1
    elif cross < 0:
        return 1
    else:
        return 0
# ========================
# 클래스 정의
# ========================

class PolylineManager:
    def __init__(self, polyline, sta_interval=25, start_station=0.0):
        self.polyline = polyline
        self.sta_interval = sta_interval
        self.polyline_with_sta = [(start_station + i * sta_interval, *p) for i, p in enumerate(polyline)]

    def interpolate(self, target_sta):
        for i in range(len(self.polyline_with_sta)-1):
            sta1, x1, y1, z1 = self.polyline_with_sta[i]
            sta2, x2, y2, z2 = self.polyline_with_sta[i+1]
            bearing = calculate_bearing(x1, y1, x2, y2)
            if sta1 <= target_sta < sta2:
                t = abs(target_sta - sta1)
                x, y = calculate_destination_coordinates(x1, y1, bearing, t)
                z = z1
                return (x, y, z), (x1, y1, z1), bearing
        raise ValueError("STA 범위를 벗어났습니다.")

class OffsetCalculator:
    @staticmethod
    def offset_point(vector, point, distance):
        vector += -90 if distance>0 else 90
        x, y = calculate_destination_coordinates(point[0], point[1], vector, abs(distance))
        return (x, y, 0)

class DXFSaver:
    @staticmethod
    def save(polyline, offset_points, filename="output.dxf"):
        doc = ezdxf.new()
        msp = doc.modelspace()
        polyline_2d = [(p[0], p[1]) for p in polyline]
        msp.add_lwpolyline(polyline_2d, dxfattribs={"color": 5})
        for p in offset_points:
            msp.add_circle((p[0], p[1]), radius=10, dxfattribs={"color": 1})
        doc.saveas(filename)

class Visualizer:
    @staticmethod
    def plot(polyline, points_original, points_offset):
        plt.figure(figsize=(8,6))
        x_poly, y_poly = zip(*[(p[0], p[1]) for p in polyline])
        plt.plot(x_poly, y_poly, 'b-', label="폴리선")
        for p in points_original:
            plt.scatter(p[0], p[1], color='green')
        for p in points_offset:
            plt.scatter(p[0], p[1], color='red', marker='x')
        for po, off in zip(points_original, points_offset):
            plt.plot([po[0], off[0]], [po[1], off[1]], 'k--', alpha=0.5)
        plt.plot([points_offset[0][0], points_offset[1][0]],
                 [points_offset[0][1], points_offset[1][1]],
                 'r-', label="전차선")
        plt.xlabel("X 좌표")
        plt.ylabel("Y 좌표")
        plt.title("폴리선과 오프셋 점 시각화")
        plt.grid()
        plt.axis('equal')
        plt.legend()
        plt.show()

# ========================
# Tkinter GUI
# ========================

class OffsetGUI:
    def __init__(self, master):
        self.master = master
        master.title("Railway Offset Tool")
        row = 0

        tk.Label(master, text="BVE 좌표 파일").grid(row=row, column=0)
        self.entry_file = tk.Entry(master, width=40)
        self.entry_file.grid(row=row, column=1)
        tk.Button(master, text="찾기", command=self.browse_file).grid(row=0, column=2)

        row += 1
        tk.Label(master, text="Stagger CSV 파일").grid(row=row, column=0)
        self.entry_csv = tk.Entry(master, width=40)
        self.entry_csv.grid(row=row, column=1)
        tk.Button(master, text="찾기", command=self.browse_csv).grid(row=row, column=2)

        row += 1
        tk.Label(master, text="BVE배선 파일").grid(row=row, column=0)
        self.entry_layout_csv = tk.Entry(master, width=40)
        self.entry_layout_csv.grid(row=row, column=1)
        tk.Button(master, text="찾기", command=self.browse_file2).grid(row=row, column=2)

        labels = [
            ("선형 시작 측점", "startblock"),
            ("시작측점", "pos"),
            ("경간", "span"),
            ("시점 offset", "stagger"),
            ("끝 offset", "stagger2"),
            ("파정값", "brokenchain"),

        ]

        self.entries = {}
        for text, key in labels:
            row += 1
            tk.Label(master, text=text).grid(row=row, column=0)
            entry = tk.Entry(master, width=40)
            entry.grid(row=row, column=1)
            self.entries[key] = entry
        row += 1
        buttonframe = tk.Frame(root)  # ✅ Frame 객체 생성
        buttonframe.grid(row=row, column=1, padx=10, pady=10)

        tk.Button(buttonframe, text="계산 및 DXF 저장", command=self.run_calculation).grid(row=row, column=0,
                                                                                      pady=10)
        tk.Button(buttonframe, text="계산 및 리스트 저장", command=self.run_csv_calculation).grid(row=row, column=1,
                                                                                          pady=10)
        tk.Button(buttonframe, text="정거장구간 계산", command=self.run_stationsection_calculation).grid(row=row, column=2,
                                                                                                  pady=10)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Text files","*.txt")])
        if filename:
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, filename)

    def browse_csv(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filename:
            self.entry_csv.delete(0, tk.END)
            self.entry_csv.insert(0, filename)

    def browse_file2(self):
        filename = filedialog.askopenfilename(filetypes=[("Text files","*.txt")])
        if filename:
            self.entry_layout_csv.delete(0, tk.END)
            self.entry_layout_csv.insert(0, filename)

    def run_calculation(self):
        try:
            filepath = self.entry_file.get()
            polyline = read_polyline(filepath)
            startblock = float(self.entries["startblock"].get())
            pos = int(self.entries["pos"].get())
            span = int(self.entries["span"].get())
            stagger = float(self.entries["stagger"].get())
            stagger2 = float(self.entries["stagger2"].get())

            manager = PolylineManager(polyline, start_station=startblock)
            point_a, _, vector_a = manager.interpolate(pos)
            point_b, _, vector_b = manager.interpolate(pos + span)

            offset_a = OffsetCalculator.offset_point(vector_a, point_a, stagger)
            offset_b = OffsetCalculator.offset_point(vector_b, point_b, stagger2)

            a_b_angle = calculate_bearing(offset_a[0], offset_a[1], offset_b[0], offset_b[1])
            finale_angle = vector_a - a_b_angle

            #height1 =  float(self.entry_height.get())
            #height2 = float(self.entry_height2.get())
            #z_angle = calculate_slope(height1, height2, span)

            messagebox.showinfo("완료", f"DXF 저장 완료!\n전차선 각도: {a_b_angle:.4f}\n폴리선과 전차선 각도: {finale_angle:.4f}\n")
            DXFSaver.save(polyline, [offset_a, offset_b], "c:/temp/railway_offset.dxf")
            Visualizer.plot(polyline, [point_a, point_b], [offset_a, offset_b])


        except Exception as e:
            messagebox.showerror("오류", str(e))

    def run_csv_calculation(self):
        try:
            final = []
            filepath = self.entry_file.get()
            polyline = read_polyline(filepath)
            csvpath = self.entry_csv.get()
            stagger_data = read_stagger_csv(csvpath)
            startblock_value = float(self.entries["startblock"].get())
            manager = PolylineManager(polyline, start_station=startblock_value)
            offset = float(self.entries["brokenchain"].get())
            spans = {25: 669, 30:668, 35: 667, 40: 477, 45:484, 50:478, 55:485, 60:479}
            for i in range(len(stagger_data) - 1):
                post_number, station, staager = stagger_data[i]
                if i < len(stagger_data) - 1:
                    _, next_station, next_stagger = stagger_data[i + 1]
                else:
                    next_station, next_stagger = station, staager  # 혹은 적절한 기본값
                next_station += offset
                pos = station + offset
                span = next_station - pos
                span_key = nearest_span(int(span), spans)

                index = spans.get(span_key, 478)
                stagger = staager
                stagger2 = next_stagger

                point_a, _, vector_a = manager.interpolate(pos)
                point_b, _, vector_b = manager.interpolate(pos + span)

                offset_a = OffsetCalculator.offset_point(vector_a, point_a, stagger)
                offset_b = OffsetCalculator.offset_point(vector_b, point_b, stagger2)

                a_b_angle = calculate_bearing(offset_a[0], offset_a[1], offset_b[0], offset_b[1])
                finale_angle = vector_a - a_b_angle
                final.append((post_number, station, staager, index,span, finale_angle))
            messagebox.showinfo("완료",'작업이 끝났습니다,.')
            save_data(final)
            return final

        except Exception as e:
            messagebox.showerror("에러", f'작업이 실패했습니다 {e}')

    def run_stationsection_calculation(self):
        try:
            final = []
            filepath = self.entry_file.get()
            polyline = read_polyline(filepath)
            csvpath = self.entry_csv.get()
            stagger_data = read_stagger_csv(csvpath)
            input_file = self.entry_layout_csv.get()

            coords = read_coordinates(input_file)
            target_index = 4
            output_file = f'c:/temp/rail{target_index}.txt'
            # 특정 rail만 저장 (예: rail 26만)
            sort_and_save(coords, output_file, target_index=target_index)

            # 대상 polyline (예: 여러 점으로 구성된 선)
            target = read_polyline(output_file)
            target_polyline = LineString(target)

            startblock_value = float(self.entries["startblock"].get())
            manager = PolylineManager(polyline, start_station=startblock_value)
            offset = float(self.entries["brokenchain"].get())
            spans = {25: 669, 30:668, 35: 667, 40: 477, 45:484, 50:478, 55:485, 60:479}
            for i in range(len(stagger_data) - 1):
                post_number, station, stagger = stagger_data[i]
                if i < len(stagger_data) - 1:
                    _, next_station, next_stagger = stagger_data[i + 1]
                else:
                    next_station, next_stagger = station, stagger  # 혹은 적절한 기본값
                next_station += offset
                pos = station + offset
                span = next_station - pos
                span_key = nearest_span(int(span), spans)

                index = spans.get(span_key, 478)
                point_a, a, vector_a = manager.interpolate(pos)
                point_b, b, vector_b = manager.interpolate(pos + span)
                point_ap = Point(point_a)
                point_bp = Point(point_b)

                #선로에서 ㅅ너로까지 거리
                offseta = point_ap.distance(target_polyline)
                offsetb = point_bp.distance(target_polyline)
                nearest_point = target_polyline.interpolate(target_polyline.project(point_ap))
                side = calculate_side(math.radians(vector_a), a,(nearest_point.x, nearest_point.y))
                stagger = stagger + (offseta * side)
                stagger2 = next_stagger + (offsetb * side)

                offset_a = OffsetCalculator.offset_point(vector_a, point_a, stagger)
                offset_b = OffsetCalculator.offset_point(vector_b, point_b, stagger2)

                a_b_angle = calculate_bearing(offset_a[0], offset_a[1], offset_b[0], offset_b[1])
                finale_angle = vector_a - a_b_angle
                final.append((post_number, station, stagger, index,span, finale_angle))
            messagebox.showinfo("완료",'작업이 끝났습니다,.')
            save_data(final)
            return final

        except Exception as e:
            messagebox.showerror("에러", f'작업이 실패했습니다 {e}')

def nearest_span(span, spans):
    # spans.keys() 중 가장 가까운 값 찾기
    return min(spans.keys(), key=lambda k: abs(k - span))



def save_data(data):
    with open('c:/temp/wiredata.txt', 'w', newline='') as f:
        for post_number, station, staager, index, span, finale_angle in data:
            f.write(f',;{post_number}\n{station}\n,;SPAN={span}\n,.freeobj 0;{index};{staager};0;{finale_angle};0;,;contact\n')

# ========================
# 실행
# ========================

if __name__ == "__main__":
    root = tk.Tk()
    app = OffsetGUI(root)
    root.mainloop()
