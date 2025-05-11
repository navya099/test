import ezdxf
import math


def read_csv_by_type(file_path, mode):
    """
    mode: 'coordinates', 'stations', 'freeobjects'
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    result = []
    for line in lines:
        parts = line.strip().split(',')
        try:
            if mode == 'coordinates' and len(parts) == 3:
                x = float(parts[0].strip())
                y = float(parts[1].strip())
                z = float(parts[2].strip())
                result.append((x, y, z))

            elif mode == 'stations' and len(parts) == 3:
                x = float(parts[0].strip())
                y = float(parts[1].strip())
                name = parts[2].strip()
                result.append((x, y, name))

            elif mode == 'freeobjects' and len(parts) == 7:
                station = float(parts[0].strip())
                railindex = int(parts[1].strip())
                object_index = int(parts[2].strip())
                name = parts[3].strip()
                x = float(parts[4].strip())
                y = float(parts[5].strip())
                z = float(parts[6].strip())
                result.append((object_index, name, x, y, z))
            else:
                print('Invalid mode selected!')
                continue  # 이 라인은 루프를 다음 줄로 넘김
        except Exception as e:
            print(f"[Warning] Failed to parse line: {line.strip()} - {e}")
            continue
    return result



def create_dxf(coordinates, stations, freeobjects, output_path):
    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()

    # Create a 3D polyline
    layer_name = "rail 0"
    layer_color = 250
    layer = doc.layers.new(name=layer_name, dxfattribs={'color': layer_color})
    msp.add_polyline3d(coordinates, dxfattribs={'layer': layer_name})
    msp.add_lwpolyline(coordinates, dxfattribs={'layer': layer_name, 'const_width': 4, 'color':10})
    # Add text annotations for stations
    doc.styles.new("myStandard", dxfattribs={"font": "Gulim.ttf"})

    text_height = 40
    radius = 20
    blank = 15
    textmargin = 5
    num_segments = 36
    for x, y, name in stations:
        coord = (x, y)
        offset = (x + text_height, y + text_height)
        offsetx, offsety = offset

        msp.add_circle(center=coord, radius=radius)  # 서클대신 포리선으로 불가능하면 폴리선 생성
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
        msp.add_lwpolyline(points, dxfattribs={'const_width': 2})

        text = msp.add_text(name,
                            dxfattribs={'insert': offset, 'height': text_height, 'color': 250, "style": "myStandard"})

        # Add bounding rectangle
        text_width = 40 * (len(name)) + (blank * len(name))  # Get the width of the text
        lower_left = (offsetx, offsety - textmargin)
        lower_right = (offsetx + text_width, offsety - textmargin)
        upper_left = (offsetx, offsety + text_height + textmargin)
        upper_right = (offsetx + text_width, offsety + text_height + textmargin)

        msp.add_lwpolyline([lower_left, lower_right, upper_right, upper_left, lower_left],
                           dxfattribs={'const_width': 2})

    # 프리오브젝트
    if freeobjects:
        for objidx, name, x, y, z in freeobjects:
            coord = (x, y)
            objname = f'{str(objidx)}[{name}]'
            text = msp.add_text(objname,
                                dxfattribs={'insert': coord, 'height': 1, 'color': 6,
                                            "style": "myStandard"})

    doc.saveas(output_path)


def main():
    coord_file = 'c:/temp/bve_coordinates.txt'
    sta_file = 'c:/temp/bve_stationcoordinates.txt'
    dxf_file = 'c:/temp/bve_coordinates.dxf'
    freeobj_file = 'c:/temp/bve_freeobjcoordinates.txt'

    coordinates = read_csv_by_type(coord_file,'coordinates')
    stations = read_csv_by_type(sta_file,'stations')
    freeobjects = read_csv_by_type(freeobj_file,'freeobjects')
    create_dxf(coordinates, stations, freeobjects, dxf_file)
    print(f"DXF file created successfully at {dxf_file}")


if __name__ == "__main__":
    main()
