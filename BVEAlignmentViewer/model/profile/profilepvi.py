from dataclasses import dataclass

from model.profile.profileentity import ProfileEntity
from model.profile.profileentitytype import ProfileEntityType

@dataclass
class ProfilePVI:
    """
    프로파일에서 두 접선 엔티티가 형성하는 선이 만나는 지점(엔티티가 만나든 만나지 않든)("수직 교차점")입니다.
    Attributes:
        elevation(float): 표고 값
        pvitype(ProfileEntityType): 종단 유형(직선,곡선)
        station(float):  측점
    """
    elevation: float = 0.0
    pvitype: ProfileEntityType = ProfileEntityType.Tangent
    station: float = 0.0
    verticalcurve: ProfileEntity = None