from Profile.profileentity import ProfileEntity


class ProfileEntityCollection(list):
    """
    The ProfileEntity collection class. This class represents the collection of all ProfileEntity objects that belong to the Profile.
    """
    def __init__(self):
        super().__init__()

    def append(self, entity: ProfileEntity):
        super().append(entity)
        self._update_prev_next_entity_id()

    def insert(self, index: int, entity: ProfileEntity):
        super().insert(index, entity)
        self._update_prev_next_entity_id()

    @property
    def firstentity(self) -> int | None:
        if self:
            return self[0].entity_id
        return None  # 컬렉션이 비어있으면 None 반환

    @property
    def lastentity(self) -> int | None:
        if self:
            return self[-1].entity_id
        return None

    def entity_at_id(self, entity_id: int) -> ProfileEntity | None:
        for entity in self:
            if entity.entity_id == entity_id:
                return entity
        raise ValueError("해당 ID의 엔티티가 존재하지 않습니다.")

    def remove(self, entity: ProfileEntity):
        """Remove a ProfileEntity from the collection."""
        super().remove(entity)
        self._update_prev_next_entity_id()

    def remove_at_index(self, index: int):
        """Remove a ProfileEntity at a given index from the collection."""
        del self[index]
        self._update_prev_next_entity_id()

    #비공개 메소드
    def _update_prev_next_entity_id(self):
        """각 entity의 이전/다음 entity ID를 자동 계산"""
        n = len(self)
        for i, entity in enumerate(self):
            entity.prev_entity = self[i - 1].entity_id if i > 0 else None
            entity.next_entity = self[i + 1].entity_id if i < n - 1 else None






