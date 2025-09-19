from dataclasses import dataclass
import math

from traits.trait_types import self

from Alignment.AlignmentEntity.alignmentcurve import AlignmentCurve
from math_utils import calculate_bearing, calculate_midpoint
from point2d import Point2d


@dataclass
class AlignmentLine(AlignmentCurve):
    """
    AlignmentLine 클래스. 이 클래스는 단일 선 하위 엔터티로 구성된 AlignmentEntity를 나타냅니다.
    Attributes:
        curve_group_index (str): AlignmentLine의 그룹 인덱스를 가져오거나 설정합니다.
        curve_group_sub_entity_index (str): AlignmentLine의 그룹 하위 엔터티 인덱스를 가져오거나 설정합니다.
        pass_through_point1 (Point2d): AlignmentSubEntityLine의 첫 번째 통과 지점을 가져오거나 설정합니다.
        pass_through_point2 (Point2d): AlignmentSubEntityLine 두 번째 통과 지점을 가져오거나 설정합니다.
    Properties:
        direction (float): AlignmentSubEntityLine의 방향 (라디안 단위).
        mid_point (Point2d): AlignmentSubEntityLine 중간점 좌표.

    """
    curve_group_index: str = ''
    curve_group_sub_entity_index: str = ''
    pass_through_point1: Point2d = Point2d(x=0, y=0)
    pass_through_point2: Point2d = Point2d(x=0, y=0)

    @property
    def direction(self):
        return calculate_bearing(self.start_point.x, self.start_point.y, self.end_point.x, self.end_point.y)
    @property
    def mid_point(self):
        return calculate_midpoint(self.start_point, self.end_point)




