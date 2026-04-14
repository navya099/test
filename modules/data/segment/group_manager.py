from data.alignment.exception.alignment_error import NotEnoughPIPointError, InvalidGeometryError
from data.alignment.geometry.straight.straightgeometry import StraightGeometry
from data.segment.segment import Segment
from data.segment.segment_group.segment_group import SegmentGroup
from data.segment.straight_segment import StraightSegment


class GroupManager:
    def __init__(self):
        self.groups: list[SegmentGroup] = []

    def create_curve_group(self, i, bp, ip, ep, r, isspiral) -> SegmentGroup | None:
        """커브그룹 생성 팩토리메서드"""
        return SegmentGroup.create_from_pi(i, bp, ip, ep, r, isspiral)

    def collect_segments(self) -> list[Segment]:
        """모든 그룹 내부 세그먼트를 모아 반환"""
        segments = []
        for group in self.groups:
            if group:
                segments.extend(group.segments)
        return segments


    def create_group_at_index(self, i, pi_manager, radius_manger):
        """
        핵심 로직 내부: index 기준 그룹 생성
        """
        n = len(pi_manager.coord_list)
        if n < 2:
            raise NotEnoughPIPointError()

        # === 곡선이 가능한 구간 ===
        if 0 < i < n - 1:
            bp = pi_manager.coord_list[i - 1]
            ip = pi_manager.coord_list[i]
            ep = pi_manager.coord_list[i + 1]
            r = radius_manger.radius_list[i]
            isspiral = False

            # --- 그룹 생성 시도 ---
            if r is None:
                return
            group = self.create_curve_group(i, bp, ip, ep, r, isspiral)
            if group is None:
                raise InvalidGeometryError(f"곡선 그룹 생성 실패: PI {i}")

            #그룹리스트 갱신
            self.groups[i] = group
            #RADIUS리스트 갱신
            radius_manger.radius_list[i] = r

    def update_group_index(self):
        """
        groups 리스트에 있는 각 SegmentGroup의 인덱스를 0부터 순서대로 갱신
        """
        for idx, group in enumerate(self.groups):
            if group:
                group.group_index = idx
