from tkinter import messagebox

from model.model import BVERouteData, Curve, Pitch


class RouteProcessor:
    def __init__(self, current_route):
        self.current_route = current_route

    @staticmethod
    def remove_duplicate_radius(curves: list[Curve]) -> None:
        """
        연속된 동일 곡선 반경을 원본 리스트에서 제거한다.
        """
        i = 1
        while i < len(curves):
            if curves[i].radius == curves[i - 1].radius:
                del curves[i]  # 현재 요소 삭제
            else:
                i += 1

    @staticmethod
    def remove_duplicate_pitchs(pitchs: list[Pitch]) -> None:
        """
        연속된 동일 구배를 원본 리스트에서 제거한다.
        """
        i = 1
        while i < len(pitchs):
            if pitchs[i].pitch == pitchs[i - 1].pitch:
                del pitchs[i]  # 현재 요소 삭제
            else:
                i += 1