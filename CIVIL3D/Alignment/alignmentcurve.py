from dataclasses import dataclass
from Alignment.alignmententity import AlignmentEntity

@dataclass
class AlignmentCurve(AlignmentEntity):
    end_point: float = 0.0
    end_station: float = 0.0
    length: float = 0.0
    start_point: float = 0.0
    start_station: float = 0.0
    sub_entity_count: int = 0