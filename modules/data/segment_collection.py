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
        """PI 좌표와 반경 리스트로 전체 선형(T–C–T–C–T) 생성"""
        self.coord_list = coord_list
        self.radius_list = radius_list
        self.groups.clear()
        self.segment_list.clear()

        n = len(coord_list)

        for i in range(n - 1):
            bp = coord_list[i]
            ep = coord_list[i + 1]

            # 이전 PI가 존재하면 곡선 추가
            if 0 < i < n - 1:
                bp_prev = coord_list[i - 1]
                ip = coord_list[i]
                ep_next = coord_list[i + 1]
                r = radius_list[i - 1] if i - 1 < len(radius_list) else 0

                group = SegmentGroup.create_from_pi(i, bp_prev, ip, ep_next, r, isspiral=False)
                if group is None:
                    print("해결할 수 있는 솔루션이 없습니다.")
                    self.groups.clear()
                    self.segment_list.clear()
                    return None
                self.groups.append(group)

                # ── ① 직전 직선의 끝점을 곡선 시작점으로 보정 ──
                if len(self.segment_list) > 0:
                    last_straight = self.segment_list[-1]
                    if isinstance(last_straight, StraightSegment):
                        last_straight.end_coord = group.segments[0].start_coord  # curve.start_coord

                # ── ② 곡선 추가 ──
                self.segment_list.extend(group.segments)

                # ── ③ 다음 직선의 시작점을 곡선 끝점으로 보정 ──
                #   단, 다음 점(ep)이 존재하는 경우
                if i + 1 < n - 1:
                    next_bp = group.segments[-1].end_coord
                    next_ep = coord_list[i + 1]
                    straight = StraightSegment(start_coord=next_bp, end_coord=next_ep)
                    self.segment_list.append(straight)
                    continue  # 다음 루프는 이 직선에서 이어짐

            # ── ④ 첫 번째 직선 또는 마지막 직선 처리 ──
            straight = StraightSegment(start_coord=bp, end_coord=ep)
            self.segment_list.append(straight)

        # 인덱스 및 station 갱신
        self._update_prev_next_entity_id()
        self._update_stations()

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


