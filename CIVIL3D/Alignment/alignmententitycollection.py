from point3d import Point3D

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

    def add_fixed_line(self, start_point: Point3D, end_point: Point3D):
        """시작점과 끝점으로 정의된 AlignmentLine 엔터티를 만듭니다."""
        pass
