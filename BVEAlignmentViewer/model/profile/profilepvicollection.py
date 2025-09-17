from model.profile.profileentity import ProfileEntity
from model.profile.profilepvi import ProfilePVI


class ProfilePVICollection(list):
    """
    ProfilePVICollection 클래스
    Attributes:
    """
    def __init__(self):
        super().__init__()

    def add_pvi(self, station: float, elevation: float):
        """단순 PVI 추가"""
        pvi = ProfilePVI(station=station, elevation=elevation)
        self.append(pvi)

    def add_pvi_arc(self, station: float, elevation: float, radius: float):
        pass
    def add_pvi_asym_parabola(self, station: float, elevation: float, tangentlen1: float, tangentlen2: float):
        pass
    def add_pvi_sym_parabola(self, station: float, elevation: float, curvelength: float):
        pass
        # --- 검색 & 삭제 ---

    def get_pvi_at(self, station: float, elevation: float) -> ProfilePVI | None:
        if not self:
            return None
        return min(self, key=lambda p: (abs(p.station - station) + abs(p.elevation - elevation)))

    def remove_pvi(self, pvi: ProfilePVI):
        if pvi in self:
            self.remove(pvi)

    def remove_pvi_at_index(self, index: int):
        if 0 <= index < len(self):
            self.pop(index)

    def remove_pvi_at(self, station: float, elevation: float):
        target = self.get_pvi_at(station, elevation)
        if target:
            self.remove(target)