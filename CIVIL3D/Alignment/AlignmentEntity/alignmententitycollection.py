from Alignment.AlignmentEntity.alignmententity import AlignmentEntity
from Alignment.AlignmentEntity.alignmentline import AlignmentLine
from point2d import Point2d
from point3d import Point3d

class AlignmentEntityCollection(list):
    """
    AlignmentEntity 컬렉션 클래스입니다. 이 클래스는 Alignment에 속하는 모든 AlignmentEntity 객체의 컬렉션을 나타냅니다.
    """
    def __init__(self):
        super().__init__()

    @property
    def first_entity(self):
        return self[0].entity_id

    @property
    def last_entity(self):
        return self[-1].entity_id

    def add_fixed_line(self, start_point: Point3d, end_point: Point3d):
        """시작점과 끝점으로 정의된 AlignmentLine 엔터티를 만듭니다."""
        #point3d를 2d로 변환
        start_point = start_point.convert_2d()
        end_point = end_point.convert_2d()
        self.append(AlignmentLine(start_point=start_point, end_point=end_point))
        self._update_stations()

    def entity_at_id(self, entity_id: int) -> AlignmentEntity | None:
        for entity in self:
            if entity.entity_id == entity_id:
                return entity
        raise ValueError("해당 ID의 엔티티가 존재하지 않습니다.")

    def remove(self, entity: AlignmentEntity):
        """Remove a AlignmentEntity from the collection."""
        super().remove(entity)
        self._update_prev_next_entity_id()
        self._update_stations()

    def remove_at_index(self, index: int):
        """Remove a AlignmentEntity at a given index from the collection."""
        del self[index]
        self._update_prev_next_entity_id()
        self._update_stations()

    # 비공개 메소드
    def _update_prev_next_entity_id(self):
        """각 entity의 이전/다음 entity ID를 자동 계산"""
        n = len(self)
        for i, entity in enumerate(self):
            entity.entity_before = self[i - 1].entity_id if i > 0 else None
            entity.entity_after = self[i + 1].entity_id if i < n - 1 else None

    def _update_stations(self) -> None:
        """
        컬렉션 내 AlignmentEntity들의 start_station과 end_station을 자동 계산합니다.
        비어 있는 컬렉션일 경우 아무 작업도 수행하지 않습니다.
        """
        if not self:
            return

        # 첫 엔티티의 시작 측점
        first_entity = self[0]
        if hasattr(first_entity, "sub_entities") and first_entity.sub_entities:
            current_sta = first_entity.sub_entities[0].start_station
        else:
            current_sta = first_entity.start_station

        # 각 엔티티 길이에 따라 station 갱신
        for entity in self:
            entity.start_station = current_sta
            entity.end_station = current_sta + entity.length
            current_sta = entity.end_station


