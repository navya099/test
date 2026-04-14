from AutoCAD.point2d import Point2d
from data.alignment.exception.alignment_error import PIOutOfRangeError
from data.pi_helper import PIHelper


class PIManager:
    def __init__(self):
        self.coord_list: list[Point2d] = []

    def update_pi(self, index: int, coord: Point2d):
        """주어진 인덱스의 PI 좌표 업데이트"""
        if coord:
            self.coord_list[index] = coord

    def remove_pi(self, index: int):
        """주어진 인덱스의 PI 좌표 삭제"""
        if index < 0 or index >= len(self.coord_list):
            raise PIOutOfRangeError("PI index out of range")
        del self.coord_list[index]

    def add_pi(self, coord: Point2d):
        """PI 추가"""
        insert_index = PIHelper.find_insert_index(self.coord_list, coord) #삽입 인덱스 찾기
        self.coord_list.insert(insert_index, coord)
        PIHelper.sort_coords(self.coord_list)#BP->EP 순으로 정렬


