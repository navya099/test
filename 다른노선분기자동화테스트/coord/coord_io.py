import logging

class CoordinateLoader:
    """좌표 로더"""
    def load(self, coord_file):
        logging.debug("좌표 파일 읽기")
        return self.read_coordinates(coord_file)

    def read_coordinates(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()
        coordinates = []
        for line in lines:
            parts = line.strip().split(',')
            if len(parts) == 3:
                x = float(parts[0].strip())
                y = float(parts[1].strip())
                z = float(parts[2].strip())
                coordinates.append((x,y,z))
        return coordinates
