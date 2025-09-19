from abc import ABC
from dataclasses import dataclass, field

from Alignment.AlignmentSubEntity.alignmentsubentitytype import AlignmentSubEntityType
from point2d import Point2d


@dataclass
class AlignmentSubEntity(ABC):
    """
    정렬 하위 엔티티 클래스입니다. 이 클래스는 정렬 엔티티를 구성하는 기본 도면 구성 요소를 나타냅니다.
    Attributes:
        curve_group_index: 정렬 하위 엔터티 그룹 인덱스를 가져오거나 설정합니다.
        curve_group_sub_entity_index: 정렬 하위 엔터티 그룹 하위 엔터티 인덱스를 가져오거나 설정합니다.
        end_point: 정렬 하위 엔터티 끝점 좌표를 가져옵니다.
        end_station: 정렬 하위 엔터티 종료 스테이션을 가져옵니다.
        length: 정렬 하위 엔터티 길이를 가져오거나 설정합니다.
        start_point: 정렬 하위 엔터티 시작점 좌표를 가져옵니다.
        start_station: 정렬 하위 엔터티 시작 스테이션을 가져옵니다.
        sub_entity_type: 정렬 하위 엔터티 유형을 가져옵니다.
    """
    curve_group_index: str = ''
    curve_group_sub_entity_index: str = ''
    end_point: Point2d = field(default_factory=lambda: Point2d(0, 0))
    end_station: float = 0.0
    length: float = 0.0
    start_point: Point2d = field(default_factory=lambda: Point2d(0, 0))
    start_station: float = 0.0
    sub_entity_type: AlignmentSubEntityType = AlignmentSubEntityType.Line