import ezdxf
import math
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import random

class BVEDataLoader:
    """BVE 관련 모든 CSV/TXT 데이터 파일을 통합하여 로드하는 파서 클래스"""

    @staticmethod
    def _safe_read_lines(file_path):
        """안전하게 파일을 열고 줄 단위로 정제하여 반환하는 공통 헬퍼 메서드"""
        if not file_path or not os.path.exists(file_path):
            return []

        # 인코딩 에러 방지를 위해 utf-8 + ignore 공통 적용
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f if line.strip()]

    def load_track_alignment(self, file_path):
        """BVE 선형 파일 파싱 (측점,X,Y,Z...)"""
        lines = self._safe_read_lines(file_path)
        if not lines:
            return []

        if '측점,X,Y,Z,Bearing,Radius,Cant,Pitch,height' not in lines[0]:
            raise ValueError('올바른 BVE 선형 파일이 아닙니다.')

        bve_datas = []
        for line in lines[1:]:
            parts = line.split(',')
            try:
                if len(parts) < 9: continue
                bve_datas.append(BVEData(
                    station=float(parts[0]), x=float(parts[1]), y=float(parts[2]), z=float(parts[3]),
                    bearing=float(parts[4]), radius=float(parts[5]), cant=float(parts[6]),
                    pitch=float(parts[7]), height=float(parts[8])
                ))
            except (ValueError, IndexError):
                continue
        return bve_datas

    def load_rail_info(self, file_path):
        """배선 파일 파싱"""
        lines = self._safe_read_lines(file_path)
        coordinates = []
        for line in lines:
            parts = line.split(',')
            if len(parts) == 5:
                try:
                    coordinates.append(BVERail(
                        station=float(parts[0]), index=int(parts[1]),
                        x=float(parts[2]), y=float(parts[3]), z=float(parts[4])
                    ))
                except ValueError:
                    continue
        return coordinates

    def load_free_objects(self, file_path):
        """프리오브젝트 파싱"""
        lines = self._safe_read_lines(file_path)
        result = []
        for line in lines:
            parts = line.split(',')
            try:
                # 리스트 슬라이싱이나 언패킹을 쓰면 더 직관적입니다.
                result.append((
                    int(parts[2]), parts[3].strip(),
                    float(parts[4]), float(parts[5]), float(parts[6])
                ))
            except (ValueError, IndexError):
                continue
        return result

    def load_stations(self, file_path):
        """역 좌표 파일 파싱"""
        lines = self._safe_read_lines(file_path)
        stations = []
        for line in lines:
            parts = line.split(',')
            if len(parts) == 4:
                try:
                    stations.append((
                        float(parts[0]), float(parts[1]), float(parts[2]), parts[3].strip()
                    ))
                except ValueError:
                    continue
        return stations

class BVERail:
    def __init__(self, station, x, y, z, index):
        self.station = station
        self.x = x
        self.y = y
        self.z = z
        self.index = index

class BVEData:
    def __init__(self, station, x, y, z, bearing, radius, cant, pitch, height):
        self.station = station
        self.x = x
        self.y = y
        self.z = z
        self.bearing = bearing
        self.radius = radius
        self.cant = cant
        self.pitch = pitch
        self.height = height

class DXFManger:
    def __init__(self):
        self.bverails = None
        self.freeobjects = None
        self.stations = None
        self.bvedatas = None
        self.doc = ezdxf.new(dxfversion='R2010')
        self.msp = self.doc.modelspace()

    def create_dxf(self, bvedatas: list[BVEData], stations, freeobjects, output_path, bverails: list[BVERail]):
        self.bvedatas = bvedatas
        self.stations = stations
        self.freeobjects = freeobjects
        self.bverails = bverails

        #평면선형 작성
        self.create_plan()
        #평면 정거장 작성
        self.create_plan_stations()

        #종단선형 작성
        self.create_profile()

        #freeobj작성
        self.create_freeobj()

        #배선 작성
        self.create_layout()
        #저장
        self.doc.saveas(output_path)

    def create_plan(self):
        # Create a 3D polyline
        plan_2d_name = "plan2d"
        plan_3d_name = "plan3d"
        layer_color = 1
        plan_2d_layer = self.doc.layers.new(name=plan_2d_name, dxfattribs={'color': layer_color})
        plan_3d_layer = self.doc.layers.new(name=plan_3d_name, dxfattribs={'color': layer_color})

        xyz_coords = [(data.x, data.y, data.z) for data in self.bvedatas]
        chainages = [(data.station, data.x, data.y) for data in self.bvedatas]
        # 각 station 위치에 텍스트 추가
        for chain, x, y in chainages:
            self.msp.add_text(str(chain), dxfattribs={'height': 4, 'layer': 'chainage', 'insert': (x, y)})

        self.msp.add_polyline3d(xyz_coords, dxfattribs={'layer': plan_3d_name})
        self.msp.add_lwpolyline(xyz_coords, dxfattribs={'layer': plan_2d_name, 'const_width': 4})

    def create_plan_stations(self):
        # 역 표시용 레이어 생성
        station_layer = "plan_station"
        self.doc.layers.new(name=station_layer, dxfattribs={'color': 1})  # 빨강

        # 텍스트 스타일
        self.doc.styles.new("myStandard", dxfattribs={"font": "Gulim.ttf"})

        text_height = 40
        radius = 20
        blank = 15
        textmargin = 5
        num_segments = 36

        for sta, x, y, name in self.stations:
            coord = (x, y)
            offset = (x + text_height, y + text_height)
            offsetx, offsety = offset

            # 원
            self.msp.add_circle(center=coord, radius=radius,
                                dxfattribs={'layer': station_layer})
            hatch = self.msp.add_hatch(color=130, dxfattribs={'layer': station_layer})
            edge_path = hatch.paths.add_edge_path()
            edge_path.add_arc(center=coord, radius=radius, start_angle=0, end_angle=360)

            # 원을 근사하는 폴리선
            points = []
            for i in range(num_segments):
                angle = 2 * math.pi * i / num_segments
                px = x + radius * math.cos(angle)
                py = y + radius * math.sin(angle)
                points.append((px, py))
            points.append(points[0])
            self.msp.add_lwpolyline(points, dxfattribs={'const_width': 2, 'layer': station_layer})

            # 역 이름 텍스트
            self.msp.add_text(name, dxfattribs={'insert': offset, 'height': text_height,
                                                'color': 250, 'style': "myStandard",
                                                'layer': station_layer})

            # 텍스트 박스
            text_width = 40 * len(name) + (blank * len(name))
            lower_left = (offsetx, offsety - textmargin)
            lower_right = (offsetx + text_width, offsety - textmargin)
            upper_left = (offsetx, offsety + text_height + textmargin)
            upper_right = (offsetx + text_width, offsety + text_height + textmargin)

            self.msp.add_lwpolyline([lower_left, lower_right, upper_right, upper_left, lower_left],
                                    dxfattribs={'const_width': 2, 'layer': station_layer})

    def create_profile(self):
        profile_layer = "profile"
        ground_layer = "ground"
        grid_layer = "grid"
        station_layer = "profile_station"

        self.doc.layers.new(name=profile_layer, dxfattribs={'color': 1})  # 빨강
        self.doc.layers.new(name=ground_layer, dxfattribs={'color': 3})  # 녹색
        self.doc.layers.new(name=grid_layer, dxfattribs={'color': 8})  # 회색 (보조선)
        self.doc.layers.new(name=station_layer, dxfattribs={'color': 6})  # 마젠타

        profile_coords = [(data.station, data.z) for data in self.bvedatas]
        ground_coords = [(data.station, data.z - data.height) for data in self.bvedatas]

        # 종단선형 polyline
        self.msp.add_lwpolyline(profile_coords, dxfattribs={'layer': profile_layer})
        self.msp.add_lwpolyline(ground_coords, dxfattribs={'layer': ground_layer})

        # 텍스트
        for sta, h in profile_coords:
            self.msp.add_text(f"{h:.2f}m",
                              dxfattribs={'insert': (sta, h + 10),
                                          'height': 5,
                                          'layer': profile_layer,
                                          'color': 2})
            self.msp.add_text(f"{int(sta)}",
                              dxfattribs={'insert': (sta, 0),
                                          'height': 5,
                                          'layer': profile_layer,
                                          'color': 1})

        # 가로선 (예: 0m ~ 최대고도까지 50m 간격)
        sta_min = min([d.station for d in self.bvedatas])
        sta_max = max([d.station for d in self.bvedatas])
        h_min = min([d.z for d in self.bvedatas]) - 20
        h_max = max([d.z for d in self.bvedatas]) + 20

        for h in range(int(h_min), int(h_max) + 1, 50):
            self.msp.add_line((sta_min, h), (sta_max, h), dxfattribs={'layer': grid_layer})

        # 세로선 (예: 100m 간격)
        for sta in range(int(sta_min), int(sta_max) + 1, 100):
            self.msp.add_line((sta, h_min), (sta, h_max), dxfattribs={'layer': grid_layer})

            # 범위 계산
            sta_min = min([d.station for d in self.bvedatas])
            sta_max = max([d.station for d in self.bvedatas])
            h_min = min([d.z for d in self.bvedatas]) - 20
            h_max = max([d.z for d in self.bvedatas]) + 20

        # 정거장 표시 (수직선 + 텍스트 + 원)

        for chain, x, y, name in self.stations:
            sta = chain
            # 해당 station과 가장 가까운 bvedata 찾기
            nearest = min(self.bvedatas, key=lambda d: abs(d.station - sta))
            level = nearest.z
            # 수직선
            self.msp.add_line((sta, level), (sta, level + 100),
                              dxfattribs={'layer': station_layer})

            # 원 기호 (기준선 근처)
            self.msp.add_circle(center=(sta, level + 50), radius=5,
                                dxfattribs={'layer': station_layer})

            # 텍스트 (원 옆에 배치)
            self.msp.add_text(name,
                              dxfattribs={'insert': (sta + 10, level + 70),
                                          'height': 8,
                                          'layer': station_layer,
                                          'color': 6,
                                          'style': "myStandard"})
    def create_freeobj(self):
        # 프리오브젝트
        if self.freeobjects:
            for objidx, name, x, y, z in self.freeobjects:
                coord = (x, y)
                objname = f'{str(objidx)}[{name}]'
                text = self.msp.add_text(objname,
                                    dxfattribs={'insert': coord, 'height': 1, 'color': 6,
                                                "style": "myStandard"})

    def create_layout(self):
        if not self.bverails:
            return
        # 레이어 및 색상 처리
        color_map = {}
        used_colors = set()
        aci_colors = list(range(256))
        aci_colors.remove(10)  # 10번 컬러는 사용하지 않음

        def get_random_color():
            while True:

                color = random.choice(aci_colors)
                if color not in used_colors:
                    used_colors.add(color)
                    return color

        # Group coordinates by railindex
        rail_coordinates = {}
        stationtexts = {}

        for rail in self.bverails:
            station = rail.station
            railindex = rail.index
            x, y, z = rail.x , rail.y, rail.z

            if railindex not in rail_coordinates:
                rail_coordinates[railindex] = []
            rail_coordinates[railindex].append((x, y, z))

            if railindex not in stationtexts:
                stationtexts[railindex] = []
            stationtexts[railindex].append((station, x, y))

        # Create layers and add polylines for each railindex
        for railindex, coords in rail_coordinates.items():
            layer_name = f"rail {railindex}"
            layer_color = get_random_color()

            # Add layer with specified color
            layer = self.doc.layers.new(name=layer_name, dxfattribs={'color': layer_color})

            # Add 3D polylines to the modelspace
            self.msp.add_polyline3d(coords, dxfattribs={'layer': layer_name})

            # 각 station 위치에 텍스트 추가
            for station, x, y in stationtexts[railindex]:
                self.msp.add_text(str(station), dxfattribs={'height': 4, 'layer': layer_name, 'insert': (x, y)})
class BveDxfConverter:
    def __init__(self, root):
        self.root = root
        root.title("BVE DXF 변환기")

        # 좌표 파일
        tk.Label(root, text="BVE선형 파일:").grid(row=0, column=0, sticky="w")
        self.entry_input1 = tk.Entry(root, width=50)
        self.entry_input1.grid(row=0, column=1, padx=5, pady=2)
        tk.Button(root, text="찾기", command=self.browse_input1).grid(row=0, column=2, padx=5)

        # 역 좌표 파일
        tk.Label(root, text="역 좌표 파일:").grid(row=1, column=0, sticky="w")
        self.entry_input2 = tk.Entry(root, width=50)
        self.entry_input2.grid(row=1, column=1, padx=5, pady=2)
        tk.Button(root, text="찾기", command=self.browse_input2).grid(row=1, column=2, padx=5)

        #프리오브젝트 파일
        tk.Label(root, text="프리오브젝트 파일:").grid(row=2, column=0, sticky="w")
        self.entry_input3 = tk.Entry(root, width=50)
        self.entry_input3.grid(row=2, column=1, padx=5, pady=2)
        tk.Button(root, text="찾기", command=self.browse_input3).grid(row=2, column=2, padx=5)

        #배선 파일
        tk.Label(root, text="배선 파일:").grid(row=3, column=0, sticky="w")
        self.layout_entry = tk.Entry(root, width=50)
        self.layout_entry.grid(row=3, column=1, padx=5, pady=2)
        tk.Button(root, text="찾기", command=self.browse_railinfo).grid(row=3, column=2, padx=5)

        # 출력 파일
        tk.Label(root, text="출력 DXF 파일:").grid(row=4, column=0, sticky="w")
        self.entry_output = tk.Entry(root, width=50)
        self.entry_output.grid(row=4, column=1, padx=5, pady=2)
        tk.Button(root, text="저장", command=self.browse_output).grid(row=4, column=2, padx=5)

        frame_buttons = tk.Frame(root)
        frame_buttons.grid(row=5, column=0, columnspan=3, pady=10)

        tk.Button(frame_buttons, text="DXF 생성", command=self.run_process,
                  width=10, bg="lightblue").pack(side="left", padx=5)

        tk.Button(frame_buttons, text="종료", command=root.destroy,
                  width=10, bg="lightblue").pack(side="left", padx=5)

    def run_process(self):
        input_file = self.entry_input1.get()
        input_file2 = self.entry_input2.get()
        input_file3 = self.entry_input3.get() if self.entry_input3.get() else None
        output_file = self.entry_output.get()
        layoutfile = self.layout_entry.get()

        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("에러", "좌표 파일을 선택하세요.")
            return
        if not input_file2 or not os.path.exists(input_file2):
            messagebox.showerror("에러", "역 좌표 파일을 선택하세요.")
            return
        if not output_file:
            messagebox.showerror("에러", "출력 DXF 파일 경로를 지정하세요.")
            return
        # 2. 통합 파서 인스턴스 생성 및 호출
        loader = BVEDataLoader()
        dxfmger = DXFManger()
        try:
            bvedatas = loader.load_track_alignment(input_file)
            stations = loader.load_stations(input_file2)
            freeobjects = loader.load_free_objects(input_file3) if input_file3 else None
            bverails = loader.load_rail_info(layoutfile) if layoutfile else None

            dxfmger.create_dxf(bvedatas, stations, freeobjects, output_file, bverails)
            messagebox.showinfo("완료", f"DXF 파일이 생성되었습니다.\n{output_file}")
        except Exception as e:
            messagebox.showerror("에러", f"처리 중 오류 발생:\n{e}")

    def browse_input1(self):
        filename = filedialog.askopenfilename(title="선형 파일 선택",
                                              filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            self.entry_input1.delete(0, tk.END)
            self.entry_input1.insert(0, filename)

    def browse_input2(self):
        filename = filedialog.askopenfilename(title="역 좌표 파일 선택",
                                              filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            self.entry_input2.delete(0, tk.END)
            self.entry_input2.insert(0, filename)

    def browse_input3(self):
        filename = filedialog.askopenfilename(title="프리오브젝트 파일 선택",
                                              filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            self.entry_input3.delete(0, tk.END)
            self.entry_input3.insert(0, filename)

    def browse_railinfo(self):
        filename = filedialog.askopenfilename(title="배선 파일 선택",
                                              filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            self.layout_entry.delete(0, tk.END)
            self.layout_entry.insert(0, filename)

    def browse_output(self):
        filename = filedialog.asksaveasfilename(title="DXF 파일 저장",
                                                defaultextension=".dxf",
                                                filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")])
        if filename:
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, filename)
    def destroy(self):
        self.root.destroy()

def main():
    root = tk.Tk()
    app = BveDxfConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
