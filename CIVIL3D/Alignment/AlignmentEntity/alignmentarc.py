from dataclasses import dataclass, field

from Alignment.AlignmentEntity.alignmentcurve import AlignmentCurve
from point2d import Point2d


@dataclass
class AlignmentArc(AlignmentCurve):
    """
    The AlignmentArc class. AlignmentArc derives from the abstract AlignmentCurve class, and represents an AlignmentEntity made up of a single AlignmentSubEntityArc object.
    Attributes:
        center_point: Gets or sets the AlignmentArc's center point.
        chord_direction: Gets the AlignmentArc's chord direction.
        chord_length: Gets or sets the AlignmentArc's chord length.
        clock_wise: Gets a bool value that specifies whether the curve entity is a reverse curve.
        curve_group_index: Gets or sets the AlignmentArc's group index.
        curve_group_sub_entity_index: Gets or sets the AlignmentArc's group subentity index.
        deflected_angle: Gets or sets the AlignmentArc's deflected angle
        delta: Gets or sets the AlignmentArc's delta.
        direction_at_point1: Gets or sets the AlignmentArc's direction at point1.
        direction_at_point2: Gets or sets the AlignmentArc's direction at point2.
        end_direction: Gets the AlignmentArc's end direction.
        external_secant: Gets or sets the AlignmentArc's external secant.
        external_tangent: Gets or sets the AlignmentArc's external tangent.
        greater_than_180: Gets or sets a bool value indicating whether the Arc solution angle is > 180 Degrees.
        mid_ordinate: Gets or sets the AlignmentArc's mid-ordinate.
        pi_station: Gets the AlignmentArc's PI station.
        radius: Gets or sets the AlignmentArc's radius
        reverse_curve: Gets or sets the AlignmentArc's reverse curve.
        start_direction: Gets the AlignmentArc's start direction.

    """
    center_point: Point2d = field(default_factory=lambda: Point2d(0, 0))
    chord_direction: float = 0.0
    chord_length: float = 0.0
    clock_wise: bool = False
    curve_group_index: str = ''
    curve_group_sub_entity_index: str = ''
    deflected_angle: float = 0.0
    delta: float = 0.0
    direction_at_point1: float = 0.0
    direction_at_point2: float = 0.0
    end_direction: float = 0.0
    external_secant: float = 0.0
    external_tangent: float = 0.0
    greater_than_180: bool = False
    mid_ordinate: float = 0.0
    pass_through_point1: Point2d = field(default_factory=lambda: Point2d(0, 0))
    pass_through_point2: Point2d = field(default_factory=lambda: Point2d(0, 0))
    pass_through_point3: Point2d = field(default_factory=lambda: Point2d(0, 0))
    pi_station: float = 0.0
    radius: float = 0.0
    reverse_curve: bool = False
    start_direction: float = 0.0



