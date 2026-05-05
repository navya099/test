class BVEAlignmentIntersapter:

    @staticmethod
    def load_coordinates():
        """BVE 좌표 데이터를 텍스트 파일에서 불러오는 함수"""
        coord_filepath = 'c:/temp/bve_coordinates.txt'
        return BVEAlignmentIntersapter.read_polyline(coord_filepath)

    @staticmethod
    def load_layout_coordinates():
        """BVE 좌표 데이터를 텍스트 파일에서 불러오는 함수"""
        filepath = 'c:/temp/rail_info.txt'
        return BVEAlignmentIntersapter.read_layout_polyline(filepath)

    @staticmethod
    def read_layout_polyline(file_path):
        points = {}
        with open(file_path, 'r') as file:
            for line in file:
                # 쉼표로 구분된 값 읽기
                sta_str, railkey, x_str, y_str, z_str = line.strip().split(',')
                railkey = int(railkey)
                sta, x, y, z = float(sta_str), float(x_str), float(y_str), float(z_str)

                # railkey별로 리스트 누적
                if railkey not in points:
                    points[railkey] = []
                points[railkey].append((sta, x, y, z))

        return points

    @staticmethod
    def read_polyline(file_path):
        points = []
        with open(file_path, 'r') as file:
            for line in file:
                # 쉼표로 구분된 값을 읽어서 float로 변환
                x, y, z = map(float, line.strip().split(','))
                points.append((x, y, z))
        return points

    @staticmethod
    def create_linestring(polyline):
        from shapely.geometry import LineString
        line = LineString(polyline)
        return line

    @staticmethod
    def get_alignment():
        pl = BVEAlignmentIntersapter.load_coordinates()
        return BVEAlignmentIntersapter.create_linestring(pl)

    @staticmethod
    def get_layout_alignment():
        return BVEAlignmentIntersapter.load_layout_coordinates()