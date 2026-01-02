import math
import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
import ezdxf

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
import csv

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
        tk.Label(master, text="Stagger CSV 파일").grid(row=1, column=0)
        self.entry_csv = tk.Entry(master, width=40)
        self.entry_csv.grid(row=row, column=1)
        tk.Button(master, text="찾기", command=self.browse_csv).grid(row=1, column=2)

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

        tk.Button(master, text="계산 및 DXF 저장", command=self.run_calculation).grid(row=row, column=0, columnspan=3, pady=10)
        row += 1
        tk.Button(master, text="계산 및 리스트 저장", command=self.run_csv_calculation).grid(row=row, column=0, columnspan=3, pady=10)

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


    def run_calculation(self):
        try:
            filepath = self.entry_file.get()
            polyline = read_polyline(filepath)
            startblock = float(self.entry_startblock.get())
            pos = int(self.entry_pos.get())
            span = int(self.entry_span.get())
            stagger = float(self.entry_stagger.get())
            stagger2 = float(self.entry_stagger2.get())

            manager = PolylineManager(polyline, start_station=startblock)
            point_a, _, vector_a = manager.interpolate(pos)
            point_b, _, vector_b = manager.interpolate(pos + span)

            offset_a = OffsetCalculator.offset_point(vector_a, point_a, stagger)
            offset_b = OffsetCalculator.offset_point(vector_b, point_b, stagger2)

            a_b_angle = calculate_bearing(offset_a[0], offset_a[1], offset_b[0], offset_b[1])
            finale_angle = vector_a - a_b_angle

            height1 =  float(self.entry_height.get())
            height2 = float(self.entry_height2.get())
            z_angle = calculate_slope(height1, height2, span)

            messagebox.showinfo("완료", f"DXF 저장 완료!\n전차선 각도: {a_b_angle:.4f}\n폴리선과 전차선 각도: {finale_angle:.4f}\n높이각도: {z_angle}\n")
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
