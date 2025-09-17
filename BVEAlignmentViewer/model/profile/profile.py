from model.profile.profilepvicollection import ProfilePVICollection


class Profile:
    """
    종단 정보 저장용 클래스.
    """
    def __init__(self, name: str):
        self.name = name
        self.max_slope = max(pvi.elevation for pvi in self.pvis)
        self.min_slope = 0.0
        self.max_elevation = 0.0
        self.min_elevation = 0.0
        self.end_station = 0.0
        self.start_station = 0.0
        self.length = 0.0
        self.pvis: ProfilePVICollection = ProfilePVICollection()

    # ✅ 예시 메서드들
    def calculate_statistics(self):
        """
        PVI 목록 기반으로 최대/최소 경사 및 고도 계산
        """
        if not self.pvis:
            return
        self.max_slope = max(pvi.elevation for pvi in self.pvis)
        self.min_slope = min(pvi.elevation for pvi in self.pvis)
        self.max_elevation = max(pvi.elevation for pvi in self.pvis)
        self.max_elevation = min(pvi.elevation for pvi in self.pvis)
        self.start_station = self.pvis[0].station
        self.end_station = self.pvis[-1].station
        self.length = self.end_station - self.start_station

    def elevation_at_station(self, station: float) -> float:
        """
        해당 측점에서의 고도 반환
        Args:
            station:

        Returns:
            elevation: float
        """
        pass


