from AutoCAD.point2d import Point2d
from data.alignment.exception.alignment_error import PIOutOfRangeError


class CurveManager:
    """곡선 관리클래스"""
    def __init__(self):
        self.radius_list: list[float | None] = []

    def update_curve(self, index: int, radius: float | None):
        """곡선 반경 갱신/삭제"""
        self.radius_list[index] = radius

    def remove_curve(self, index: int):
        """주어진 인덱스의 곡선 삭제"""
        if index < 0 or index >= len(self.radius_list):
            raise PIOutOfRangeError("PI index out of range")
        del self.radius_list[index]