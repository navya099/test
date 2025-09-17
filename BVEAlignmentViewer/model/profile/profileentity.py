from dataclasses import dataclass

from model.profile.profileentitytype import ProfileEntityType


@dataclass
class ProfileEntity:
    end_elevation: float = 0.0
    end_station: float = 0.0
    prev_entity: int = 0
    next_entity: int = 0
    entity_id: int = 0
    length: float = 0.0
    start_elevation: float = 0.0
    start_station: float = 0.0
    entity_type: ProfileEntityType = ProfileEntityType.Tangent
