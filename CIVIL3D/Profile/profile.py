from Profile.profileentitycollection import ProfileEntityCollection
from Profile.profilepvicollection import ProfilePVICollection


class Profile:
    """
    A record of elevation against distance along a horizontal Alignment or other line. Profiles are used to visualize the terrain along a route of interest, such as a proposed road, or simply to show how the elevation changes across a particular region.
    """
    def __init__(self, name: str):
        self.name: str = name
        self.pvis: ProfilePVICollection = ProfilePVICollection()
        self.entities: ProfileEntityCollection = ProfileEntityCollection()

    @property
    def max_slope(self):
        gradin = max((pvi.gradein for pvi in self.pvis), default=0.0)
        gradeout = max((pvi.gradeout for pvi in self.pvis), default=0.0)
        return max(gradin, gradeout)

    @property
    def min_slope(self):
        gradin = min((pvi.gradein for pvi in self.pvis), default=0.0)
        gradeout = min((pvi.gradeout for pvi in self.pvis), default=0.0)
        return min(gradin, gradeout)

    @property
    def max_elevation(self):
        return max((pvi.elevation for pvi in self.pvis), default=0.0)

    @property
    def min_elevation(self):
        return min((pvi.elevation for pvi in self.pvis), default=0.0)

    @property
    def start_station(self):
        return self.pvis[0].station if self.pvis else 0.0

    @property
    def end_station(self):
        return self.pvis[-1].station if self.pvis else 0.0

    @property
    def length(self):
        return self.end_station - self.start_station if self.pvis else 0.0

    def elevation_at_station(self, station: float) -> float:
        """
        특정 측점에서의 고도 반환 (직선 보간 방식)

        Args:
            station (float): 조회할 측점

        Returns:
            float: 계산된 표고
        """
        if not self.pvis:
            return 0.0

        # 정확히 같은 PVI가 있으면 반환
        for pvi in self.pvis:
            if pvi.station == station:
                return pvi.elevation

        # PVI 정렬 (혹시 정렬 안된 경우)
        pvis = sorted(self.pvis, key=lambda p: p.station)

        # 범위 밖이면 경계값 반환
        if station <= pvis[0].station:
            return pvis[0].elevation
        if station >= pvis[-1].station:
            return pvis[-1].elevation

        # 두 PVI 사이에서 직선 보간
        for i in range(len(pvis) - 1):
            p1, p2 = pvis[i], pvis[i + 1]
            if p1.station <= station <= p2.station:
                ratio = (station - p1.station) / (p2.station - p1.station)
                return p1.elevation + ratio * (p2.elevation - p1.elevation)

        # 여기까지 오면 논리 오류
        return 0.0



