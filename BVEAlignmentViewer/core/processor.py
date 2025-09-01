from model.model import BVERouteData, Curve, Pitch

class RouteProcessor:
    """
    BVERouteData 전처리를 위한 프로세서 클래스
    Attributes:
        current_route(BVERouteData): BVERouteData 객체
    """
    def __init__(self, current_route: BVERouteData):
        self.current_route = current_route

    def run(self):
        """
        전처리 실행 메소드
        1. 라스트블럭 인덱스만큼 각 리스트들 자르기
        2. 중복 반경 제거
        3. 중복 구배 제거
        4. coords 크기 맞추기
        5. direction 크기 맞추기
        """
        self._slice_to_lastblock()
        self._remove_duplicate_radius()
        self._remove_duplicate_pitchs()
        self._remove_coords_by_indices()
        self._remove_directions_by_indices()

    def _slice_to_lastblock(self):
        """
        마지막 블럭 인덱스만큼 리스트를 자르는 매소드
        실행 후 curves,pitchs, coords, directions들 크기 상태 변화
        """
        self.current_route.curves = self.current_route.curves[:self.current_route.lastindex + 1]
        self.current_route.pitchs = self.current_route.pitchs[:self.current_route.lastindex + 1]
        self.current_route.coords = self.current_route.coords[:self.current_route.lastindex + 1]
        self.current_route.directions = self.current_route.directions[:self.current_route.lastindex + 1]

    def _remove_duplicate_radius(self):
        """
        블록내 중복된 반경을 제거하는 메소드
        """
        self.removed_indices = [] #1회용 속성
        curves = self.current_route.curves
        for i in range(len(curves) - 1, 0, -1):
            if curves[i].radius == curves[i - 1].radius:
                self.removed_indices.append(i)
                del curves[i]
        self.removed_indices.reverse()

    def _remove_duplicate_pitchs(self):
        """
        블록내 중복된 구배를 제거하는 메소드
        """
        pitchs = self.current_route.pitchs
        i = 1
        while i < len(pitchs):
            if pitchs[i].pitch == pitchs[i - 1].pitch:
                del pitchs[i]
            else:
                i += 1

    def _remove_coords_by_indices(self):
        """
        중복된 곡선반경 리스트 크기를 인덱스를 사용하여 제거하는 메소드
        실행 후 coords의 크기가 curve와 동일해짐
        """
        coords = self.current_route.coords
        for idx in reversed(self.removed_indices):
            del coords[idx]

    def _remove_directions_by_indices(self):
        """
        중복된 곡선반경 리스트 크기를 인덱스를 사용하여 제거하는 메소드
        실행 후 directrion 크기가 curve와 동일해짐
        """
        directions = self.current_route.directions
        for idx in reversed(self.removed_indices):
            del directions[idx]