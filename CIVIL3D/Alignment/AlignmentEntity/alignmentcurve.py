from dataclasses import dataclass, field
from Alignment.AlignmentEntity.alignmententity import AlignmentEntity
from point2d import Point2d


@dataclass
class AlignmentCurve(AlignmentEntity):
    """
    AlignmentCurve 클래스. AlignmentArc, AlignmentSCS, AlignmentLine과 같은 다른 Alignment Entity 클래스의 추상 기본 클래스입니다.
    """
    end_point: Point2d = field(default_factory=lambda: Point2d(0, 0))
    end_station: float = 0.0
    length: float = 0.0
    start_point: Point2d = field(default_factory=lambda: Point2d(0, 0))
    start_station: float = 0.0