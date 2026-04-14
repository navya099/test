from AutoCAD.point2d import Point2d

class CurveHelper:
    """Curve 삽입/정렬 헬퍼"""

    @staticmethod
    def insert_radius(radius_list: list[float | None], insert_index: int, radius: float | None) -> None:
        """반경 삽입"""
        radius_list.insert(insert_index, radius)

    @staticmethod
    def sort_by_coords(coord_list: list[Point2d], radius_list: list[float | None]) -> None:
        """좌표 기준으로 반경 리스트 정렬"""
        if not coord_list or not radius_list:
            return
        bp = coord_list[0]
        combined = list(zip(coord_list, radius_list))
        combined.sort(key=lambda x: bp.distance_to(x[0]))
        coord_list[:], radius_list[:] = zip(*combined)
        coord_list[:] = list(coord_list)
        radius_list[:] = list(radius_list)