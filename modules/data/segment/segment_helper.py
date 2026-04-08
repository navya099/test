from data.segment.cubic_segment import CubicSegment
from data.segment.curve_segment import CurveSegment
from data.segment.straight_segment import StraightSegment
from math_utils import draw_arc


class SegmentHelper:
    @staticmethod
    def segment_to_xy(seg):
        if isinstance(seg, StraightSegment):
            return [(seg.start_coord.x, seg.start_coord.y),
                    (seg.end_coord.x, seg.end_coord.y)]
        if isinstance(seg, CurveSegment):
            x_arc, y_arc = draw_arc(seg.direction, seg.start_coord, seg.end_coord, seg.center_coord)
            return list(zip(x_arc, y_arc))
        return None

    @staticmethod
    def get_midpoint(seg):
        """미드포인트 헬퍼"""
        if isinstance(seg, StraightSegment):
            return None
        if isinstance(seg, CurveSegment):
            return seg.midpoint.x, seg.midpoint.y
        return None

    @staticmethod
    def get_color(seg):
        """세그먼트 컬러링 헬퍼"""
        colors = {
            StraightSegment: "blue",
            CurveSegment: "orange",
            CubicSegment: "green"
        }
        return colors.get(seg.__class__, "gray")