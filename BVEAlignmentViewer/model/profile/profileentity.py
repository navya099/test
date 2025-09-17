from dataclasses import dataclass, field

from model.profile.profileentitytype import ProfileEntityType
from utils import generate_entity_id


@dataclass
class ProfileEntity:
    end_elevation: float = 0.0
    end_station: float = 0.0
    prev_entity: int = 0
    next_entity: int = 0
    entity_id: int = field(default_factory=generate_entity_id)
    length: float = 0.0
    start_elevation: float = 0.0
    start_station: float = 0.0
    entity_type: ProfileEntityType = ProfileEntityType.NONE