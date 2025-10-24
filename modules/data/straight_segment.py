from dataclasses import dataclass, field

from AutoCAD.point2d import Point2d
from data.segment import Segment
from math_utils import calculate_bearing, calculate_distance


@dataclass
class StraightSegment(Segment):
    """
    직선 세그먼트
    """
    start_coord: Point2d = field(default_factory=lambda: Point2d(0, 0))
    end_coord: Point2d = field(default_factory=lambda: Point2d(0, 0))

    @property
    def start_azimuth(self):
        return calculate_bearing(self.start_coord, self.end_coord)

    @property
    def end_azimuth(self):
        return self.start_azimuth

    @property
    def length(self):
        return calculate_distance(self.start_coord, self.end_coord)
