from data.segment.segment_group import SegmentGroup


class GroupManager:
    def __init__(self):
        self.groups = []

    def create_curve_group(self, i, bp, ip, ep, r, isspiral) -> SegmentGroup | None:

        return SegmentGroup.create_from_pi(i, bp, ip, ep, r, isspiral)
