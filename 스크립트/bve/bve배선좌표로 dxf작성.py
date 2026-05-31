import random
import ezdxf

def read_coordinates(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        
    coordinates = []
    for line in lines:
        parts = line.strip().split(',')
        if len(parts) == 5:
            station = float(parts[0].strip())
            railindex = int(parts[1].strip())
            x = float(parts[2].strip())
            y = float(parts[3].strip())
            z = float(parts[4].strip())
            coordinates.append((station, railindex, x, y, z))  # Corrected order of z and y
            
    return coordinates

def create_dxf(coordinates, output_path):
    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()

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
    for station, railindex, x, y, z in coordinates:
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
        layer = doc.layers.new(name=layer_name, dxfattribs={'color': layer_color})

        # Add 3D polylines to the modelspace
        msp.add_polyline3d(coords, dxfattribs={'layer': layer_name})

        # 각 station 위치에 텍스트 추가
        for station, x, y in stationtexts[railindex]:
            msp.add_text(str(station), dxfattribs={'height': 4, 'layer': layer_name, 'insert': (x,y)})

    doc.saveas(output_path)
    print(f"DXF file created successfully at {output_path}")

def main():
    input_file = 'c:/temp/rail_info.txt'
    output_file = 'c:/temp/rail_info.dxf'
    
    coordinates = read_coordinates(input_file)
    create_dxf(coordinates, output_file)

if __name__ == "__main__":
    main()
