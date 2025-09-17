from model.profile.profileentity import ProfileEntity


class ProfileEntityCollection(list):
    """
    The ProfileEntity collection class. This class represents the collection of all ProfileEntity objects that belong to the Profile.
    """
    def __init__(self):
        super().__init__()

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
        """
        ProfileEntity 객체를 컬렉션에서 제거합니다.

        Raises:
            ValueError: 컬렉션에 엔티티가 없으면 발생
        """
        try:
            super().remove(entity)  # list의 remove 호출
        except ValueError:
            raise ValueError("Entity not found in collection.")  # 내장 예외 사용

    def remove_at_index(self, index: int):
        """
        ProfileEntity 객체 인덱스를 컬렉션에서 제거합니다.

        Raises:
            IndexError: 컬렉션 범위를 벗어나면 발생
        """
        try:
            del self[index]  # 인덱스로 삭제
        except IndexError:
            raise IndexError("Index out of range.")  # 내장 예외 사용





