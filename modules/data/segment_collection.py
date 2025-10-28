from AutoCAD.point2d import Point2d
from data.segment import Segment
from data.segment_group import SegmentGroup
from data.straight_segment import StraightSegment
from math_utils import calculate_bearing


class SegmentCollection:
    """SegmentGroup 관리"""
    """
    Attributes:
        groups: 커브그룹 리스트
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
        """공개api pi와 radius 리스트로 컬렉션 생성"""
        self.coord_list = coord_list
        self.radius_list = radius_list
        self.groups.clear()
        self.segment_list.clear()

        n = len(coord_list)
        for i in range(n - 1):
            self._process_segment_at_index(i)

        self._update_prev_next_entity_id()
        self._update_stations()

    # 기존 메서드들은 내부 호출만 하도록 변경
    def update_pi_by_index(self, pipoint, index):
        """공개API 주어진 PI로 업데이트"""
        self._update_group_internal(index, pipoint=pipoint)

    def update_radius_by_index(self, radius, index):
        """공개API 주어진 radius로 업데이트"""
        self._update_group_internal(index, radius=radius)

    def update_pi_and_radius_by_index(self, pipoint, radius, index):
        """공개API 주어진 PI와 radius로 업데이트"""
        self._update_group_internal(index, pipoint=pipoint, radius=radius)

    def remove_pi_at_index(self, index):
        if index <= 0 or index >= len(self.coord_list) - 1:
            raise ValueError("첫 번째 또는 마지막 PI는 삭제할 수 없습니다.")
        # 1️⃣ PI 삭제
        self.coord_list.pop(index)

        # 2️⃣ 관련 그룹 및 내부 세그먼트 삭제
        target_group_idx = index - 1
        if 0 <= target_group_idx < len(self.groups):
            prev_group = self.groups[index - 2] if index - 2 >= 0 else None
            target_group = self.groups[index - 1]
            next_group = self.groups[index] if index < len(self.groups) else None

            # 이전/다음 그룹 PI 좌표 갱신
            if prev_group:
                #이전 그룹 bp, ip, ep 수정
                prev_group.update_by_pi(ep_coordinate=next_group.ip_coordinate)
            if next_group:
                #다음 그룹 bp,ip,ep 수정
                if prev_group is not None:
                    next_group.update_by_pi(bp_coordinate=prev_group.ip_coordinate)
                else:
                    next_group.update_by_pi(bp_coordinate=self.coord_list[0])

            #이전 , 다음 직선 인덱스 찾기
            prev_seg_index = target_group.segments[0].prev_index
            next_seg_index = target_group.segments[-1].next_index

            #직선 세그먼트 가져오기
            if 0 <= prev_seg_index < len(self.segment_list):
                prev_seg = self.segment_list[prev_seg_index]
            else:
                prev_seg = None

            if 0 <= next_seg_index < len(self.segment_list):
                next_seg = self.segment_list[next_seg_index]

            else:
                next_seg = None

            # 그룹 내부 세그먼트 제거
            if hasattr(target_group, "segments"):
                for seg in target_group.segments:
                    if seg in self.segment_list:
                        self.segment_list.remove(seg)
            # 그룹 제거
            del self.groups[target_group_idx]
            # 다음 직선 삭제 (존재할 경우)
            if next_seg in self.segment_list:
                self.segment_list.remove(next_seg)
            # 삭제 후 직선 재조정
            #  ✅ segment_list 상태 반영: 인덱스 갱신
            self._update_prev_next_entity_id()
            self._update_group_index()  # 필요 시

            if next_group:
                self._adjust_adjacent_straights(next_group)

        # 4️⃣ station 및 인덱스 갱신
        self._update_prev_next_entity_id()
        self._update_stations()
        self._update_group_index()

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

    def _adjust_adjacent_straights(self, group: SegmentGroup):
        """
        target_group 앞/뒤 직선 세그먼트의 start_coord, end_coord 조정
        """
        # 이전 직선
        prev_idx = group.segments[0].prev_index
        if prev_idx is not None:
            prev_seg = self.segment_list[prev_idx]
            if isinstance(prev_seg, StraightSegment):
                prev_seg.end_coord = group.segments[0].start_coord

        # 다음 직선
        next_idx = group.segments[-1].next_index
        if next_idx is not None:
            next_seg = self.segment_list[next_idx]
            if isinstance(next_seg, StraightSegment):
                next_seg.start_coord = group.segments[-1].end_coord

    # SegmentCollection.py
    def _update_group_internal(self, index, pipoint=None, radius=None):
        """
        내부 공용 메서드
        - index: 변경 대상 PI 인덱스
        - pipoint: 변경할 PI 좌표 (없으면 PI 변경 안함)
        - radius: 변경할 곡선 반경 (없으면 반경 변경 안함)
        """
        # 좌표/반경 갱신
        if pipoint is not None:
            self.coord_list[index] = pipoint
        if radius is not None:
            self.radius_list[index] = radius

        if 0 < index < len(self.coord_list) - 1:
            prev_group = self.groups[index - 2] if index - 2 >= 0 else None
            target_group = self.groups[index - 1]
            next_group = self.groups[index] if index < len(self.groups) else None

            # PI 변경
            if pipoint is not None:
                target_group.update_by_pi(ip_coordinate=pipoint)
                if prev_group is not None:
                    prev_group.update_by_pi(ep_coordinate=pipoint)
                if next_group is not None:
                    next_group.update_by_pi(bp_coordinate=pipoint)

            # 반경 변경
            if radius is not None:
                target_group.update_by_radius(radius)

            # 직선 세그먼트 조정 (한 번만 수행)
            self._adjust_adjacent_straights(target_group)

        # 인덱스 및 station 갱신
        self._update_prev_next_entity_id()
        self._update_stations()

    def _update_group_index(self):
        """
        groups 리스트에 있는 각 SegmentGroup의 인덱스를 0부터 순서대로 갱신
        """
        for idx, group in enumerate(self.groups):
            group.group_index = idx
            # 필요하면 내부 세그먼트의 prev/next group index도 갱신
            if hasattr(group, "segments"):
                for seg in group.segments:
                    seg.group_index = idx
