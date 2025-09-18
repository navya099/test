from Profile.profileentitytype import ProfileEntityType
from Profile.profilepvi import ProfilePVI


class ProfilePVICollection(list):
    """
    The ProfilePVI collection class represents the collection of all ProfilePVI objects that belong to a Profile.
    """
    def __init__(self):
        super().__init__()

    def add_pvi(self, station: float, elevation: float):
        """단순 PVI 추가"""
        pvi = ProfilePVI(station=station, elevation=elevation, pvitype=ProfileEntityType.Tangent)
        self.append(pvi)
        self._update_grades()

    def add_pvi_arc(self, station: float, elevation: float, radius: float):
        pass
    def add_pvi_asym_parabola(self, station: float, elevation: float, tangentlen1: float, tangentlen2: float):
        pass
    def add_pvi_sym_parabola(self, station: float, elevation: float, curvelength: float):
        pass
        # --- 검색 & 삭제 ---

    def get_pvi_at_station_elevation(self, station: float, elevation: float) -> ProfilePVI | None:
        """
        지정된 station, elevation에 가장 가까운 ProfilePVI 객체를 반환합니다.

        Args:
            station (float): 기준 station 값
            elevation (float): 기준 elevation 값

        Returns:
            ProfilePVI | None: 가장 가까운 ProfilePVI 객체, 없으면 None
        """
        if not self:
            raise ValueError("ProfilePVICollection is empty.")

        # station, elevation과의 거리 계산 (유클리드 거리 제곱 사용)
        def distance(pvi: ProfilePVI) -> float:
            return (pvi.station - station) ** 2 + (pvi.elevation - elevation) ** 2

        # 가장 가까운 PVI 찾기
        _, closest_pvi = min(enumerate(self), key=lambda item: distance(item[1]))
        return closest_pvi

    def remove_pvi(self, pvi: ProfilePVI):
        """
        지정된 ProfilePVI 객체를 컬렉션에서 제거합니다.

        Raises:
            ValueError: PVI가 컬렉션에 존재하지 않을 때
            RuntimeError: 첫 번째나 마지막 PVI를 삭제하려고 할 때
        """
        if not self:
            raise ValueError("ProfilePVICollection is empty.")

        if pvi not in self:
            raise ValueError("PVI not found in collection.")

        index = self.index(pvi)

        # Civil 3D와 동일하게: 첫/마지막 PVI는 삭제 불가
        if index == 0 or index == len(self) - 1:
            raise RuntimeError("Cannot remove the first or last PVI.")

        super().remove(pvi)
        self._update_grades()
    def remove_at_index(self, index: int):
        """
        ProfilePVI 객체 인덱스를 컬렉션에서 제거합니다.

        Raises:
            IndexError: 컬렉션 범위를 벗어나면 발생
        """
        try:
            del self[index]  # 인덱스로 삭제
            self._update_grades()
        except IndexError:
            raise IndexError("Index out of range.")  # 내장 예외 사용

    def remove_at_station_elevation(self, station: float, elevation: float):
        """
        지정된 station, elevation에 가장 가까운 ProfilePVI 객체를 삭제합니다.

        Raises:
            InvalidOperationException: 첫 번째나 마지막 PVI를 삭제하려고 할 때
            ValueError: 컬렉션이 비어있거나 매칭되는 객체가 없을 때
        """
        if not self:
            raise ValueError("ProfilePVICollection is empty.")

        # 각 PVI와의 거리 계산 (station, elevation 모두 고려)
        def distance(pvi):
            return (pvi.station - station) ** 2 + (pvi.elevation - elevation) ** 2

        # 가장 가까운 PVI 찾기
        closest_index, closest_pvi = min(enumerate(self), key=lambda item: distance(item[1]))

        # 첫 번째나 마지막이면 삭제 불가
        if closest_index == 0 or closest_index == len(self) - 1:
            raise RuntimeError("Cannot remove the first or last PVI.")

        # 삭제 실행
        del self[closest_index]
        self._update_grades()
    #비공개 메소드
    def _update_grades(self):
        """각 PVI의 gradein과 gradeout을 자동 계산"""
        n = len(self)
        for i, pvi in enumerate(self):
            # gradein
            if i == 0:
                pvi.gradein = 0.0  # 첫 PVI 진입 구배 0
            else:
                prev = self[i - 1]
                distance = pvi.station - prev.station
                pvi.gradein = (pvi.elevation - prev.elevation) / distance if distance != 0 else 0.0

            # gradeout
            if i == n - 1:
                pvi.gradeout = 0.0  # 마지막 PVI 진출 구배 0
            else:
                next_pvi = self[i + 1]
                distance = next_pvi.station - pvi.station
                pvi.gradeout = (next_pvi.elevation - pvi.elevation) / distance if distance != 0 else 0.0


