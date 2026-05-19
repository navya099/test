from dem import DEMProcessor
from function import read_coordinates, parse_structure, convert_coordinates
from section import SectionProvider


class Processor:
    def __init__(self):
        self.provider = None
        self.stations = None
        self.xyz_list = None
        self.xy_list = None
        self.structure_list = None
        self.dem_processor = None
        self.read_coords = None

    def run(self, read_file, struct_file, slope_ratio, track_width):
        # 2. 데이터 로드 및 파싱 검증
        self.read_coords = read_coordinates(read_file)
        if not self.read_coords:
            raise ValueError("좌표 파일이 비어있거나 형식이 잘못되었습니다.")

        self.structure_list = parse_structure(struct_file)

        # 3. 데이터 추출 (stations, xy_list)
        if len(self.read_coords[0]) == 4:
            self.xy_list = [[x, y] for sta, x, y, z in self.read_coords]
            self.xyz_list = [[x, y, z] for sta, x, y, z in self.read_coords]
            self.stations = [sta for sta, x, y, z in self.read_coords]
        elif len(self.read_coords[0]) == 3:
            self.xy_list = [[x, y] for x, y, z in self.read_coords]
            self.xyz_list = [[x, y, z] for x, y, z in self.read_coords]
            self.stations = [i * 25 for i, (x, y, z) in enumerate(self.read_coords)]
        else:
            raise ValueError("좌표 데이터의 컬럼 수가 맞지 않습니다. (Station, X, Y, Z 필요)")

        # 4. 좌표 변환 및 엔진 가동
        converted_coord = convert_coordinates(self.xy_list, 5186, 4326)

        self.dem_processor = DEMProcessor(converted_coord)

        self.provider = SectionProvider(
            dem_processor=self.dem_processor,
            structure_list=self.structure_list,
            slope_ratio=slope_ratio,
            read_coords=self.read_coords,
            xylist=self.xy_list,
            track_width=track_width,
            xyzlist=self.xyz_list,
            stations=self.stations
        )