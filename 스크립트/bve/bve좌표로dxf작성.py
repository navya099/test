import ezdxf
import math
import tkinter as tk
from tkinter import filedialog, messagebox
import os

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


class BVEParser:
    def __init__(self):
        self.lines = []
    def read_lines(self, filepath):
        with open(filepath, encoding='utf-8', errors='ignore', mode='r') as f:
            self.lines = f.readlines()

    def parse(self):
        #1 헤더확인
        #측점,X,Y,Z,Bearing,Radius,Cant,Pitch,height
        if not '측점,X,Y,Z,Bearing,Radius,Cant,Pitch,height' in self.lines[0]:
            raise ValueError('올바른 BVE 선형 파일이 아닙니다.')
        bvedatas = []
        for line in self.lines[1:]:
            try:
                line = line.strip()
                parts = line.split(',')
                station = float(parts[0])
                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])
                bearing = float(parts[4])
                radius = float(parts[5])
                cant = float(parts[6])
                pitch = float(parts[7])
                height = float(parts[8])
                bvedatas.append(BVEData(station, x, y, z, bearing, radius, cant,pitch,height))
            except (ValueError, IndexError):
                continue
        return bvedatas

def read_sta(file_path):
    with open(file_path, 'r',encoding='utf-8') as file:
        lines = file.readlines()
        
    stations = []
    for line in lines:
        parts = line.strip().split(',')
        if len(parts) == 3:
            x = float(parts[0].strip())
            y = float(parts[1].strip())
            name = parts[2].strip()
            stations.append((x, y, name))
    return stations

def create_dxf(bvedatas: list[BVEData], stations, output_path):
    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()
    
    # Create a 3D polyline
    layer_name = "rail 0"
    layer_color = 250
    layer = doc.layers.new(name=layer_name, dxfattribs={'color': layer_color})
    xyz_coords = [(data.x, data.y, data.z) for data in bvedatas]
    chainages = [(data.station, data.x, data.y) for data in bvedatas]
    # 각 station 위치에 텍스트 추가
    for chain, x, y in chainages:
        msp.add_text(str(chain), dxfattribs={'height': 4, 'layer': 'chainage', 'insert': (x, y)})

    msp.add_polyline3d(xyz_coords , dxfattribs={'layer': layer_name})
    msp.add_lwpolyline(xyz_coords , dxfattribs={'layer': layer_name,'const_width': 4})
    # Add text annotations for stations
    doc.styles.new("myStandard", dxfattribs={"font" : "Gulim.ttf"})
    
    text_height = 40
    radius = 20
    blank = 15
    textmargin = 5
    num_segments =36
    for x, y, name in stations:
        coord = (x,y)
        offset = (x + text_height,y + text_height)
        offsetx,offsety = offset
        
        msp.add_circle(center=coord, radius=radius)#서클대신 포리선으로 불가능하면 폴리선 생성
        hatch = msp.add_hatch(color=130)
        edge_path = hatch.paths.add_edge_path()
        edge_path.add_arc(center=coord, radius=radius, start_angle=0, end_angle=360)

        # Approximate circle with polyline
        points = []
        for i in range(num_segments):
            angle = 2 * math.pi * i / num_segments
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            points.append((px, py))
        points.append(points[0])  # Close the polyline
        msp.add_lwpolyline(points,dxfattribs={'const_width': 2})
        
        text = msp.add_text(name, dxfattribs={'insert': offset, 'height': text_height, 'color': 250,"style": "myStandard"})

        # Add bounding rectangle
        text_width = 40 * (len(name)) + (blank *len(name))  # Get the width of the text
        lower_left = (offsetx, offsety - textmargin)
        lower_right = (offsetx + text_width, offsety - textmargin)
        upper_left = (offsetx, offsety + text_height + textmargin)
        upper_right = (offsetx + text_width, offsety + text_height + textmargin)
        
        msp.add_lwpolyline([lower_left, lower_right, upper_right, upper_left, lower_left],dxfattribs={'const_width': 2})
    
    doc.saveas(output_path)

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

        # 출력 파일
        tk.Label(root, text="출력 DXF 파일:").grid(row=2, column=0, sticky="w")
        self.entry_output = tk.Entry(root, width=50)
        self.entry_output.grid(row=2, column=1, padx=5, pady=2)
        tk.Button(root, text="저장", command=self.browse_output).grid(row=2, column=2, padx=5)

        # 실행 버튼
        tk.Button(root, text="DXF 생성", command=self.run_process, width=20, bg="lightblue").grid(row=3, column=0, columnspan=3, pady=10)

    def run_process(self):
        input_file = self.entry_input1.get()
        input_file2 = self.entry_input2.get()
        output_file = self.entry_output.get()

        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("에러", "좌표 파일을 선택하세요.")
            return
        if not input_file2 or not os.path.exists(input_file2):
            messagebox.showerror("에러", "역 좌표 파일을 선택하세요.")
            return
        if not output_file:
            messagebox.showerror("에러", "출력 DXF 파일 경로를 지정하세요.")
            return
        parser = BVEParser()

        try:
            parser.read_lines(input_file)
            bvedatas = parser.parse()
            stations = read_sta(input_file2)
            create_dxf(bvedatas, stations, output_file)
            messagebox.showinfo("완료", f"DXF 파일이 생성되었습니다.\n{output_file}")
        except Exception as e:
            messagebox.showerror("에러", f"처리 중 오류 발생:\n{e}")

    def browse_input1(self):
        filename = filedialog.askopenfilename(title="좌표 파일 선택",
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

    def browse_output(self):
        filename = filedialog.asksaveasfilename(title="DXF 파일 저장",
                                                defaultextension=".dxf",
                                                filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")])
        if filename:
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, filename)

def main():
    root = tk.Tk()
    app = BveDxfConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
