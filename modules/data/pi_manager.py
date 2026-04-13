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
        """BP→EP 진행 방향 기준으로 PI 삽입"""
        if not self.coord_list:
            self.coord_list.append(coord)
            self.radius_list.append(radius)
            return

        bp = self.coord_list[0]
        # 각 PI까지의 BP 기준 거리
        distances = [bp.distance_to(c) for c in self.coord_list]
        new_dist = bp.distance_to(coord)

        # 삽입 위치 결정
        insert_index = 0
        for i, d in enumerate(distances):
            if new_dist > d:
                insert_index = i + 1

        self.coord_list.insert(insert_index, coord)
        self.radius_list.insert(insert_index, radius)

        # 안전하게 정렬 (BP→EP 방향)
        combined = list(zip(self.coord_list, self.radius_list))
        combined.sort(key=lambda x: bp.distance_to(x[0]))
        self.coord_list, self.radius_list = zip(*combined)
        self.coord_list = list(self.coord_list)
        self.radius_list = list(self.radius_list)

