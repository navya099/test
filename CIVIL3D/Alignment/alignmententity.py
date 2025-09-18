from abc import ABC
from dataclasses import dataclass, field

from Alignment.alignmententitytype import AlignmentEntityType
from utils import generate_entity_id


@dataclass
class AlignmentEntity(ABC,list):
    """
    AlignmentEntity 클래스. AlignmentCurve가 상속하는 추상 클래스입니다.
    """
    entity_prev: int = 0
    entity_after: int = 0
    entity_id: int = field(default_factory=generate_entity_id)
    entity_type: AlignmentEntityType = AlignmentEntityType.Line