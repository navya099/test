from dataclasses import dataclass

from Alignment.alignmentcurve import AlignmentCurve
from point2d import Point2D


@dataclass
class AlignmentLine(AlignmentCurve):
    curve_group_index: str = ''
    curve_group_sub_entity_index: str = ''
    direction: float = 0.0
    mid_point: float = 0.0
    pass_through_point1: Point2D = Point2D(x=0, y=0)
    pass_through_point2: Point2D = Point2D(x=0, y=0)


