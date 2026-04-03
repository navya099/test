from AutoCAD.point2d import Point2d
from data.alignment.exception.alignment_error import PIOutOfRangeError


class PIManager:
    def __init__(self):
        self.coord_list: list[Point2d] = []
        self.radius_list: list[float] = []

    def update_pi(self, index: int, coord: Point2d, radius: float):
        """주어진 인덱스의 PI 좌표 업데이트"""
        if coord:
            self.coord_list[index] = coord
        if radius:
            self.radius_list[index] = radius

    def remove_pi(self, index: int):
        """주어진 인덱스의 PI 좌표 삭제"""
        if index < 0 or index >= len(self.coord_list):
            raise PIOutOfRangeError("PI index out of range")
        del self.coord_list[index]
        del self.radius_list[index]

    def add_pi(self, coord: Point2d, radius: float = 0.0):
        """가장 가까운 PI 위치를 찾아 삽입"""
        if not self.coord_list:
            # 리스트가 비어있으면 그냥 추가
            self.coord_list.append(coord)
            self.radius_list.append(radius)
            return

        # 각 PI와의 거리 계산
        distances = [coord.distance_to(existing) for existing in self.coord_list]

        # 가장 가까운 인덱스 찾기
        nearest_index = min(range(len(distances)), key=lambda i: distances[i])

        # 해당 위치에 삽입
        self.coord_list.insert(nearest_index, coord)
        self.radius_list.insert(nearest_index, radius)

