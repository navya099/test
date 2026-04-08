from AutoCAD.point2d import Point2d
from data.alignment.geometry.segmentgeometry import SegmentGeometry
from data.alignment.geometry.straight.straightgeometry import StraightGeometry
from data.segment.curve_segment import CurveSegment
from data.segment.exception.segment_exception import SegmentNotFoundError
from data.segment.segment_group.segment_group import SegmentGroup

from data.segment.straight_segment import StraightSegment


class SegmentManager:
    def __init__(self):
        self.segment_list = []

    def add_boundary_straights(self, segments, coord_list, groups):
        """시작과 끝 직선 세그먼트 추가"""
        # 시작 직선
        if len(groups) > 1 and groups[1] is not None:
            first_group = groups[1]
            bp = coord_list[0]
            start_coord = bp
            end_coord = first_group.segments[0].start_coord
            start_straight = StraightSegment.from_coord(start_point=start_coord, end_point=end_coord)
            segments.insert(0, start_straight)

        # 끝 직선
        if len(groups) > 1 and groups[-2] is not None:
            last_group = groups[-2]
            ep = coord_list[-1]
            start_coord = last_group.segments[-1].end_coord
            end_coord = ep
            end_straight = StraightSegment.from_coord(start_point=start_coord, end_point=end_coord)
            segments.append(end_straight)

        return segments

    def update_prev_next_entity_id(self):
        """전체 세그먼트 인덱스 연결"""
        n = len(self.segment_list)

        # 1️⃣ current_index 먼저 부여
        for i, seg in enumerate(self.segment_list):
            seg.current_index = i

        # 2️⃣ prev, next는 이미 current_index가 세팅된 후 연결
        for i, seg in enumerate(self.segment_list):
            seg.prev_index = i - 1 if i > 0 else None
            seg.next_index = i + 1 if i < n - 1 else None

    def update_stations(self):
        """start_sta, end_sta 자동 계산"""
        current_sta = 0.0
        for seg in self.segment_list:
            seg.start_sta = current_sta
            seg.end_sta = current_sta + seg.length
            current_sta = seg.end_sta