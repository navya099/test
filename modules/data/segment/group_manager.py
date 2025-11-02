from data.segment.segment_group import SegmentGroup
from data.segment.straight_segment import StraightSegment


class GroupManager:
    def __init__(self):
        self.groups = []

    def create_curve_group(self, i, bp, ip, ep, r, isspiral) -> SegmentGroup | None:

        return SegmentGroup.create_from_pi(i, bp, ip, ep, r, isspiral)

    def find_group_near_coord(self, coord):
        """
        주어진 PI 좌표가 영향을 미치는 그룹을 반환.
        (BP~EP 구간 안에 있는 그룹)
        """
        for group in self.groups:
            if group.ip_coordinate == coord:
                return group  # 완전 일치
        return None

