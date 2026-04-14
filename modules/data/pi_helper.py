from AutoCAD.point2d import Point2d

class PIHelper:
    """PI 삽입/정렬 헬퍼"""

    @staticmethod
    def find_insert_index(coord_list: list[Point2d], new_coord: Point2d) -> int:
        """BP 기준 거리로 삽입 위치 결정"""
        if not coord_list:
            return 0

        bp = coord_list[0]
        new_dist = bp.distance_to(new_coord)
        distances = [bp.distance_to(c) for c in coord_list]

        insert_index = 0
        for i, d in enumerate(distances):
            if new_dist > d:
                insert_index = i + 1
        return insert_index

    @staticmethod
    def sort_coords(coord_list: list[Point2d]) -> None:
        """BP→EP 방향으로 좌표 정렬"""
        if not coord_list:
            return
        bp = coord_list[0]
        coord_list.sort(key=lambda c: bp.distance_to(c))
