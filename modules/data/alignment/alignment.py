from CIVIL3D.Profile.profile import Profile
from Profile.profiletype import ProfileType
from Structure.structurecollection import StructureCollection
from data.alignment.exception.alignment_error import AlignmentError
from data.segment.segment_collection import SegmentCollection
from datetime import datetime


class Alignment:
    """하나의 노선을 나타내는 고수준 객체"""

    def __init__(self, name: str = "Unnamed"):
        self.name = name
        self.collection = SegmentCollection()
        self.profiles: list[Profile] = []
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
        try:
            self.collection.create_by_pi_coords(coord_list, radius_list)
        except AlignmentError as e:
            # 로깅 or 변환 (예: GUI가 읽기 쉬운 메시지로)
            print(e)

    def update_pi(self, pipoint, index):
        """PI업데이트"""
        self.collection.update_pi_by_index(pipoint, index)

    def update_radius(self, radius, index):
        """반경 업데이트"""
        self.collection.update_radius_by_index(radius, index)

    def remove_pi(self, index):
        """PI 삭제"""
        self.collection.remove_pi_at_index(index)

    def add_pi(self, pi_point):
        """PI추가"""
        self.collection.add_pi_by_coord(pi_point)

    # ---- 고급 기능 ----
    @property
    def start_sta(self):
        return self.collection.segment_list[0].start_sta if self.collection.segment_list else 0.0

    @property
    def end_sta(self):
        return self.collection.segment_list[-1].end_sta if self.collection.segment_list else 0.0

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
        """설계선(FG) 기울기 구간 개수"""
        # Profile 객체들을 순회하며 설계선(FG) 타입 찾기
        for profile in getattr(self, "profiles", []):
            if getattr(profile, "profile_type", None) == ProfileType.FG:
                return len(profile.pvis) if getattr(profile, "pvis", None) else 0
        return 0

    @property
    def max_grade(self):
        """설계선(FG) 최대 기울기"""
        for profile in getattr(self, "profiles", []):
            if getattr(profile, "profile_type", None) == ProfileType.FG:
                return getattr(profile, "max_slope", 0.0)
        return 0.0

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