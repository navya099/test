from data.segment.segment_group import SegmentGroup

class GroupManager:
    def __init__(self):
        self.groups = []

    def create_curve_group(self, i, bp, ip, ep, r, isspiral) -> SegmentGroup | None:
        """커브그룹 생성 팩토리메서드"""
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

    def delete_group(self, group):
        """지정한 그룹 삭제"""
        self.groups.remove(group)

    def remove_group(self, group: SegmentGroup):
        """
        그룹 삭제 + 내부 세그먼트 제거 후, 이전·다음 세그먼트 반환
        """
        if not group:
            return None, None

        prev_seg = group.segments[0].prev_index
        next_seg = group.segments[-1].next_index

        # 세그먼트는 SegmentManager에 위임
        self.segment_manager.remove_group_segments(group.segments)

        # 그룹 리스트에서 삭제
        if group in self.groups:
            self.groups.remove(group)

        prev_seg_obj = self.segment_manager.segment_list[prev_seg] if prev_seg is not None else None
        next_seg_obj = self.segment_manager.segment_list[next_seg] if next_seg is not None else None

        return prev_seg_obj, next_seg_obj