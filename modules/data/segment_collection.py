from AutoCAD.point2d import Point2d
from data.segment import Segment
from data.segment_group import SegmentGroup
from data.straight_segment import StraightSegment
from math_utils import calculate_bearing


class SegmentCollection:
    """SegmentGroup 관리"""
    """
    Attributes:
        groups: 커브그룹
        coord_list: PI좌표 리스트
        radius_list: 곡선반경 리스트
        segment_list: 세그먼트 리스트(그룹 포함)
    """
    def __init__(self):
        self.groups: list[SegmentGroup] = []
        self.coord_list: list[Point2d] = []
        self.radius_list: list[float] = []
        self.segment_list: list[Segment] = []

    def create_by_pi_coords(self, coord_list, radius_list):
        self.coord_list = coord_list
        self.radius_list = radius_list
        self.groups.clear()
        self.segment_list.clear()

        n = len(coord_list)
        for i in range(n - 1):
            self._process_segment_at_index(i)

        self._update_prev_next_entity_id()
        self._update_stations()

    def _process_segment_at_index(self, i):
        bp = self.coord_list[i]
        ep = self.coord_list[i + 1]

        # 곡선 처리
        if 0 < i < len(self.coord_list) - 1:
            group = self._create_curve_group(i)
            if group is None:
                print("해결할 수 있는 솔루션이 없습니다.")
                self.groups.clear()
                self.segment_list.clear()
                return

            self.groups.append(group)
            self._adjust_previous_straight(group)
            self.segment_list.extend(group.segments)
            self._append_next_straight(group, i)
        else:
            # 첫/마지막 직선
            straight = StraightSegment(start_coord=bp, end_coord=ep)
            self.segment_list.append(straight)

    def _create_curve_group(self, i) -> SegmentGroup | None:
        bp_prev = self.coord_list[i - 1]
        ip = self.coord_list[i]
        ep_next = self.coord_list[i + 1]
        r = self.radius_list[i - 1] if i - 1 < len(self.radius_list) else 0
        return SegmentGroup.create_from_pi(i, bp_prev, ip, ep_next, r, isspiral=False)

    def _adjust_previous_straight(self, group: SegmentGroup):
        if len(self.segment_list) > 0:
            last_straight = self.segment_list[-1]
            if isinstance(last_straight, StraightSegment):
                last_straight.end_coord = group.segments[0].start_coord

    def _append_next_straight(self, group: SegmentGroup, i):
        if i + 1 < len(self.coord_list):
            next_bp = group.segments[-1].end_coord
            next_ep = self.coord_list[i + 1]
            straight = StraightSegment(start_coord=next_bp, end_coord=next_ep)
            self.segment_list.append(straight)

    def _update_prev_next_entity_id(self):
        """전체 세그먼트 인덱스 연결"""
        n = len(self.segment_list)

        # 1️⃣ current_index 먼저 부여
        for i, seg in enumerate(self.segment_list):
            seg.current_index = i

        # 2️⃣ prev, next는 이미 current_index가 세팅된 후 연결
        for i, seg in enumerate(self.segment_list):
            seg.prev_index = i - 1 if i > 0 else None
            seg.next_index = i + 1 if i < n - 1 else None

    def _update_stations(self):
        """start_sta, end_sta 자동 계산"""
        current_sta = 0.0
        for seg in self.segment_list:
            seg.start_sta = current_sta
            seg.end_sta = current_sta + seg.length
            current_sta = seg.end_sta

    # === SegmentCollection.py ===
    def update_by_index(self, pipoint, index):
        """
        특정 PI 좌표 변경 시 그룹 및 인접 그룹 재계산
        """
        # 좌표 갱신
        self.coord_list[index] = pipoint

        # 변경 대상 그룹
        if 0 < index < len(self.coord_list) - 1:
            target_group = self.groups[index - 1]
            bp = self.coord_list[index - 1]
            ip = self.coord_list[index]
            ep = self.coord_list[index + 1]
            r = self.radius_list[index - 1] if index - 1 < len(self.radius_list) else 0
            target_group.update_by_pi(ip)

        # 인접 그룹 (다음 그룹의 BP가 바뀌었으므로 재계산)
        if index < len(self.groups):
            next_group = self.groups[index]
            bp = self.coord_list[index]
            ip = self.coord_list[index + 1]
            ep = self.coord_list[index + 2] if index + 2 < len(self.coord_list) else None
            if ep is not None:
                r = self.radius_list[index] if index < len(self.radius_list) else 0
                next_group.update_by_pi(ip)

        # 인덱스 및 station 갱신
        self._update_prev_next_entity_id()
        self._update_stations()


