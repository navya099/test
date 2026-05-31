from tkinter.filedialog import askopenfilename

from civil3d절성고bve추출기 import make_ground_height, make_rails, Block, BVEData, create_bve_systax, save_txt
from coordinate_utils import convert_coordinates
from srtm30 import SrtmDEM30


def read_coordinates(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    coordinates = []
    for line in lines:
        parts = line.strip().split(',')
        if len(parts) == 3:
            x = float(parts[0].strip())
            y = float(parts[1].strip())
            z = float(parts[2].strip())
            coordinates.append((x,y, z))
    return coordinates

def write_file(path, elevations):
    with open(path, 'w') as file:
        for i, ele in enumerate(elevations):
            file.write(f"{i * 25} {ele}\n")

def assembly_rail(rail_levels, ground_eles):
    bvedata = BVEData()
    # 외부 프로젝트에서 df 없이 직접 사용
    while len(bvedata.blocks) < len(rail_levels):
        bvedata.blocks.append(Block())

    for i, (rl, gl) in enumerate(zip(rail_levels, ground_eles)):
        trackposition = i * 25
        elevation_diff = calc_elevation_diff(gl, rl)

        rails = make_rails(trackposition, elevation_diff, 0.0)
        ground, height = make_ground_height(trackposition, elevation_diff)

        bvedata.blocks[i].track_position = trackposition
        bvedata.blocks[i].rails.extend(rails)
        bvedata.blocks[i].ground = ground
        bvedata.blocks[i].height = height
    return bvedata

def calc_elevation_diff(gl, el):
    return gl - el

if __name__ == '__main__':
    # 1 파일 읽기
    read_file = askopenfilename()
    if read_file:
    # 2 좌표읽기
        read_coords = read_coordinates(read_file)
    # 3 좌표변환
        xy_list = [[x,y] for x,y,z in read_coords]
        z_list = [z for x,y,z in read_coords]
        converterd_coord = convert_coordinates(xy_list, 5186, 4326)
    # 4 표고추출
        strm = SrtmDEM30(converterd_coord)
        evs = strm.get_elevations()
    # 5 bve데이터 생성
        bvedata = assembly_rail(z_list, evs)
    # 6  파일저장
        bve_text_list = create_bve_systax(bvedata)
        save_txt(bve_text_list)
        save_file = r'c:/temp/gl.txt'
        write_file(save_file, evs)


