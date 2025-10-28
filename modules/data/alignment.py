from CIVIL3D.Profile.profile import Profile
from Structure.structurecollection import StructureCollection
from data.segment_collection import SegmentCollection
from datetime import datetime

class Alignment:
    """하나의 노선을 나타내는 고수준 객체"""

    def __init__(self, name: str = "Unnamed"):
        self.name = name
        self.collection = SegmentCollection()
        self.profile = Profile(name)
        self.structures = StructureCollection()
        self.metadata = {
            "designer": '',
            "date_created": datetime.now(),
            "remarks": "",
            "design_speed": 0,
            "route_type": ''
        }

    # ---- Proxy (컬렉션 기능 연결) ----
    def create(self, coord_list, radius_list):
        """PI/반경으로 노선 생성"""
        self.collection.create_by_pi_coords(coord_list, radius_list)

    def update_pi(self, pipoint, index):
        self.collection.update_pi_by_index(pipoint, index)

    def update_radius(self, radius, index):
        self.collection.update_radius_by_index(radius, index)

    def remove_pi(self, index):
        self.collection.remove_pi_at_index(index)

    # ---- 고급 기능 ----
    @property
    def start_sta(self):
        return self.collection.segment_list[0].start_sta

    @property
    def end_sta(self):
        return self.collection.segment_list[-1].end_sta
    
    @property
    def length(self):
        """노선 총연장 반환"""
        return self.end_sta - self.start_sta

    @property
    def bridge_count(self):
        """교량 갯수"""
        return 0

    @property
    def tunnel_count(self):
        """터널 갯수"""
        return 0

    @property
    def cost(self):
        """공사비"""
        return 0

    @property
    def radius_count(self):
        """곡선 갯수"""
        return len(self.collection.radius_list) if self.collection.radius_list else 0

    @property
    def grades_count(self):
        """기울기 갯수"""
        return len(self.profile.pvis) if self.profile.pvis else 0

    @property
    def max_grade(self):
        """최급기울기"""
        return self.profile.max_slope if self.profile.pvis else 0.0

    @property
    def min_radius(self):
        """최소곡선반경"""
        return min(self.collection.radius_list) if self.collection.radius_list else 0.0

    def summary(self):
        """요약정보 출력"""
        print(f"Alignment: {self.name}")
        print(f"Total length: {self.length:.3f} m")
        print(f"PI count: {len(self.collection.coord_list)}")
        print(f"Segment count: {len(self.collection.segment_list)}")