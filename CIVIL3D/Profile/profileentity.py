from dataclasses import dataclass, field
from Profile.profileentitytype import ProfileEntityType
from utils import generate_entity_id

@dataclass
class ProfileEntity:
    """
    ProfileEntity 데이터 클래스.

    Attributes
    ----------
    end_elevation : float
        끝 표고.
    end_station : float
        끝 측점.
    prev_entity : int
        이전 엔티티 ID.
    next_entity : int
        다음 엔티티 ID.
    entity_id : int
        엔티티 고유 ID (UUID 기반 32비트).
    length : float
        엔티티 길이.
    start_elevation : float
        시작 표고.
    start_station : float
        시작 측점.
    entity_type : ProfileEntityType
        엔티티 타입 (직선, 곡선 등).
    """

    end_elevation: float = 0.0
    end_station: float = 0.0
    prev_entity: int = 0
    next_entity: int = 0
    entity_id: int = field(default_factory=generate_entity_id)
    length: float = 0.0
    start_elevation: float = 0.0
    start_station: float = 0.0
    entity_type: ProfileEntityType = ProfileEntityType.NONE
