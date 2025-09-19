from dataclasses import dataclass, field

from Alignment.AlignmentSubEntity.alignmentsubentity import AlignmentSubEntity
from Alignment.AlignmentSubEntity.alignmentsubentitytype import AlignmentSubEntityType
from Alignment.AlignmentSubEntity.spiralcurvetype import SpiralCurveType
from Alignment.AlignmentSubEntity.spiraldirectiontype import SpiralDirectionType
from Civil.spiraltype import SpiralType
from point2d import Point2d


@dataclass
class AlignmentSubEntitySpiral(AlignmentSubEntity):
    """
    AlignmentSubEntitySpiral 클래스.
    AlignmentSubEntity를 상속하며, 나선형 곡선의 세부 속성을 포함합니다.

    Attributes:
        a: Gets the spiral A value.
        compound: Gets the alignment spiral entity Simple/Compound flag.
        curve_type: Gets the alignment spiral entity Incurve/Outcurve type.
        delta: Gets the curve delta angle.
        direction: Gets the curve direction (AlignmentSpiralDirectionType: left or right).
        end_direction: Gets the direction value at the end point.
        k: Gets the spiral K value.
        long_tangent: Gets the spiral long tangent.
        minimum_transition_length: Gets the minimum transition length according to the design speed check.
        p: Gets the spiral P value.
        radial_point: Gets the alignment spiral subentity radial Point2D coordinate.
        radius_in: Gets the incoming curve radius, in radians.
        radius_out: Gets the outgoing curve radius, in radians.
        short_tangent: Gets the spiral short tangent.
        spi_angle: Gets the alignment spiral entity SPI angle.
        spi_point: Gets the alignment spiral entity SPI Point2D coordinate.
        spiral_definition: Gets the alignment spiral entity spiral type.
        spi_station: Gets the alignment spiral entity SPI station.
        start_direction: Gets the direction value at the start point.
        total_x: Gets the spiral total X value.
        total_y: Gets the spiral total Y value.
        sub_entity_type: Overrides AlignmentSubEntity.sub_entity_type, set to Spiral.

    Inherited Attributes from AlignmentSubEntity:
        curve_group_index: Gets or sets the alignment sub-entity group index.
        curve_group_sub_entity_index: Gets or sets the alignment sub-entity group subentity index.
        start_point: Gets the alignment sub-entity start point coordinate.
        end_point: Gets the alignment sub-entity end point coordinate.
        start_station: Gets the alignment sub-entity starting station.
        end_station: Gets the alignment sub-entity ending station.
        length: Gets or sets the alignment sub-entity length.
    """
    a: float = 0.0
    compound: bool = False
    curve_type: SpiralCurveType = SpiralCurveType.InCurve
    delta: float = 0.0
    direction: SpiralDirectionType = SpiralDirectionType.DirectionLeft
    end_direction: float = 0.0
    k: float = 0.0
    long_tangent: float = 0.0
    minimum_transition_length: float = 0.0
    p: float = 0.0
    radial_point: Point2d = field(default_factory=lambda: Point2d(0, 0))
    radius_in: float = 0.0
    radius_out: float = 0.0
    short_tangent: float = 0.0
    spi_angle: float = 0.0
    spi_point: Point2d = field(default_factory=lambda: Point2d(0, 0))
    spiral_definition: SpiralType = SpiralType.JapaneseCubic
    spi_station: float = 0.0
    start_direction: float = 0.0
    total_x: float = 0.0
    total_y: float = 0.0
    sub_entity_type: AlignmentSubEntityType = AlignmentSubEntityType.Spiral