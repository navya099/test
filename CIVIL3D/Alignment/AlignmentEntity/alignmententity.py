from abc import ABC
from dataclasses import dataclass, field

from Alignment.AlignmentEntity.alignmententitytype import AlignmentEntityType
from utils import generate_entity_id


@dataclass
class AlignmentEntity(ABC):
    """
    AlignmentEntity 클래스. AlignmentCurve가 상속하는 추상 클래스입니다.
    Attributes:
       entity_before:  Gets the ID of the AlignmentEntity BEFORE this one.
       entity_after:  Gets the ID of the AlignmentEntity after this one.
       entity_id:  Gets the ID of the AlignmentEntity.
       entity_type:  Gets the AlignmentEntityType of the AlignmentEntity.
    """
    entity_before: int = 0
    entity_after: int = 0
    entity_id: int = field(default_factory=generate_entity_id)
    entity_type: AlignmentEntityType = AlignmentEntityType.Line
    _sub_entities: list = field(default_factory=list)  # 내부 보관 (비공개 느낌)
    ''
    @property
    def sub_entity_count(self) -> int:
        return len(self._sub_entities)

    def __getitem__(self, index: int):
        """Civil3D의 Item 속성 대응 → SubEntity 반환"""
        return self._sub_entities[index]
