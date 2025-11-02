from AutoCAD.point2d import Point2d
from data.alignment.exception.alignment_error import NotEnoughPIPointError, InvalidGeometryError, PIOutOfRangeError, \
    NoUpdatePIError, NoDeletePIError, RadiusError, GroupNullError
from data.segment.exception.segment_exception import SegmentListNullError
from data.segment.group_manager import GroupManager
from data.pi_manager import PIManager
from data.segment.segment import Segment
from data.segment.segment_group import SegmentGroup
from data.segment.segment_manager import SegmentManager
from data.segment.straight_segment import StraightSegment

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
        self._pi_manager = PIManager()
        self._segment_manager = SegmentManager()
        self._group_manager = GroupManager()

    # 외부 참조용 property
    @property
    def coord_list(self) -> list[Point2d]:
        return self._pi_manager.coord_list

    @property
    def radius_list(self) -> list[float]:
        return self._pi_manager.radius_list

    @property
    def segment_list(self) -> list[Segment]:
        return self._segment_manager.segment_list

    @property
    def groups(self) -> list[SegmentGroup]:
        return self._group_manager.groups

    def create_by_pi_coords(self, coord_list, radius_list):
        """공개api pi와 radius 리스트로 컬렉션 생성"""

        self._pi_manager.coord_list = coord_list
        self._pi_manager.radius_list = radius_list
        self._group_manager.groups.clear()
        self._segment_manager.segment_list.clear()

        # 내부 빌드 호출
        n = len(coord_list)
        for i in range(n - 1):
            self._process_segment_at_index(i)

        self._update_prev_next_entity_id()
        self._update_stations()
        self._update_group_index()

    # 기존 메서드들은 내부 호출만 하도록 변경
    def update_pi_by_index(self, pipoint, index):
        """공개API 주어진 PI로 업데이트"""
        if index <= 0 or index >= len(self.coord_list) - 1:
            raise NoUpdatePIError(index)
        self._update_pi(index, pipoint=pipoint)

    def update_radius_by_index(self, radius, index):
        """공개API 주어진 radius로 업데이트"""
        if index <= 0 or index >= len(self.coord_list) - 1:
            raise NoUpdatePIError(index)
        self._update_pi(index, radius=radius)

    def update_pi_and_radius_by_index(self, pipoint, radius, index):
        """공개API 주어진 PI와 radius로 업데이트"""
        if index <= 0 or index >= len(self.coord_list) - 1:
            raise NoUpdatePIError(index)
        self._update_pi(index, pipoint=pipoint, radius=radius)

    def remove_pi_at_index(self, index):
        """공개API 주어진 인덱스로 PI 삭제"""
        if index <= 0 or index >= len(self.coord_list) - 1:
            raise NoDeletePIError(index)

        # PI가 하나뿐인 경우 — 전체를 시점–종점 직선으로 복원
        if len(self.groups) <= 1:
            self._process_remove_one_only()
        else:
            self._process_remove_pi(index)

    def add_pi_by_coord(self, coord: Point2d):
        """공개 API PI 삽입"""
        # 예외탐지
        if not self.segment_list:
            raise SegmentListNullError()

        # 1️⃣ 가장 가까운 세그먼트 탐색
        nearest_seg = self._segment_manager.find_nearest_segment(coord)

        # 예외 없으면 실행
        self._insert_pi_in_segment(coord, nearest_seg)

    def _insert_pi_in_segment(self, coord, nearest_seg):
        """
        주어진 좌표 근처의 세그먼트에 PI를 삽입.
        :param coord: (x, y)
        :return: (삽입된 PI 인덱스)
        """

        # 2️⃣ 삽입 위치(해당 세그먼트의 인덱스) 찾기
        seg_index = nearest_seg.current_index

        # 세그먼트 분활
        new_seg = nearest_seg.split_to_segment(coord)

        # 세그먼트 리스트에 추가
        self._segment_manager.segment_list.insert(seg_index + 1, new_seg)
        # 인덱스 갱신
        self._update_prev_next_entity_id()

        # pi인덱스 찾기
        prev_pi_index, next_pi_index = self._pi_manager.find_pi_interval(coord)
        self._pi_manager.coord_list.insert(next_pi_index, coord)
        prev_pi_index, next_pi_index = self._pi_manager.find_pi_interval(coord)

        # 3️⃣ PI 주변 그룹 찾기
        prev_group = self._group_manager.find_group_near_coord(self.coord_list[next_pi_index - 1])
        next_group = self._group_manager.find_group_near_coord(self.coord_list[next_pi_index + 1]) \
            if next_pi_index + 1 < len(self.coord_list) else None

        # 4️⃣ 그룹 갱신 (곡선 존재할 때만)
        if prev_group:
            prev_group.update_by_pi(ep_coordinate=coord)
            self._segment_manager.adjust_adjacent_straights(prev_group)
        if next_group:
            next_group.update_by_pi(bp_coordinate=coord)
            self._segment_manager.adjust_adjacent_straights(next_group)

        # 인덱스 및 그룹 및 station 갱신
        self._update_prev_next_entity_id()
        self._update_group_index()
        self._update_stations()

    def _process_segment_at_index(self, i: int):
        """내부: index 기준 세그먼트(직선/곡선) 생성"""
        n = len(self.coord_list)
        if n < 2:
            raise NotEnoughPIPointError()

        # === 곡선이 가능한 구간 ===
        if 0 < i < n - 1:
            bp = self.coord_list[i - 1]
            ip = self.coord_list[i]
            ep = self.coord_list[i + 1]
            r = self.radius_list[i - 1]
            isspiral = False  # 나중에 조건으로 확장 가능

            group = self._group_manager.create_curve_group(i, bp, ip, ep, r, isspiral)
            if group is None:
                self.groups.clear()
                self.segment_list.clear()
                raise InvalidGeometryError("곡선 그룹 생성 실패")

            self.groups.append(group)
            self._adjust_previous_straight(group)
            self.segment_list.extend(group.segments)
            self._append_next_straight(group, i)

        # === 첫/마지막 PI ===
        else:
            bp = self.coord_list[i]
            ep = self.coord_list[i + 1]
            straight = StraightSegment(start_coord=bp, end_coord=ep)
            self.segment_list.append(straight)

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

    def _update_pi(self, index, pipoint=None, radius=None):
        """
        내부 공용 메서드
        - index: 변경 대상 PI 인덱스
        - pipoint: 변경할 PI 좌표 (없으면 PI 변경 안함)
        - radius: 변경할 곡선 반경 (없으면 반경 변경 안함)
        """
        if radius == 0:
            raise RadiusError(radius)

        # --- 기존 PI 좌표 백업 ---
        old_pi_coord = self.coord_list[index]
        prev_pi_coord = self.coord_list[index - 1] if index > 0 else None
        next_pi_coord = self.coord_list[index + 1] if index + 1 < len(self.coord_list) else None

        # PI 좌표 / 반경 리스트 갱신
        if pipoint is not None:
            self._pi_manager.coord_list[index] = pipoint
        if radius is not None and index - 1 < len(self.radius_list):
            self._pi_manager.radius_list[index - 1] = radius

        # --- 그룹 탐색은 기존 좌표 기준 ---
        prev_group = self._group_manager.find_group_near_coord(prev_pi_coord) if prev_pi_coord else None
        target_group = self._group_manager.find_group_near_coord(old_pi_coord)
        next_group = self._group_manager.find_group_near_coord(next_pi_coord) if next_pi_coord else None

        # 일치하는 그룹이 없으면 (직선 PI) → 그룹 갱신 스킵
        if prev_group is None and target_group is None and next_group is None:
            # pi 변경시 직선을 조정
            if pipoint:
                self._segment_manager.adjust_adjacent_straights_without_group(old_pi_coord, pipoint)
            self._update_prev_next_entity_id()
            self._update_stations()
            self._update_group_index()
            return

        #그룹이 하나라도 있으면 그룹갱신
        if prev_group or target_group or next_group:
            self._update_group_internal(prev_group, target_group, next_group, old_pi_coord, pipoint, radius)

        # 인덱스 및 station 갱신
        self._update_prev_next_entity_id()
        self._update_stations()
        self._update_group_index()
        
    # SegmentCollection.py
    def _update_group_internal(self, index, pipoint=None, radius=None):
        """
        내부 공용 메서드
        - index: 변경 대상 PI 인덱스
        - pipoint: 변경할 PI 좌표 (없으면 PI 변경 안함)
        - radius: 변경할 곡선 반경 (없으면 반경 변경 안함)
        """
        if radius == 0:
            raise RadiusError(radius)
        # 좌표/반경 갱신
        if pipoint is not None:
            self.coord_list[index] = pipoint
        if radius is not None:
            self.radius_list[index - 1] = radius

        if 0 < index < len(self.coord_list) - 1:
            prev_group = self.groups[index - 2] if index - 2 >= 0 else None
            target_group = self.groups[index - 1]
            next_group = self.groups[index] if index < len(self.groups) else None

            # PI 변경
            if pipoint is not None:
                target_group.update_by_pi(ip_coordinate=pipoint)
                self._adjust_adjacent_straights(target_group)
                if prev_group is not None:
                    prev_group.update_by_pi(ep_coordinate=pipoint)
                    # 직선 세그먼트 조정 (한 번만 수행)
                    self._adjust_adjacent_straights(prev_group)
                if next_group is not None:
                    next_group.update_by_pi(bp_coordinate=pipoint)
                    # 직선 세그먼트 조정 (한 번만 수행)
                    self._adjust_adjacent_straights(next_group)

            # 반경 변경
            if radius is not None:
                target_group.update_by_radius(radius)
                # 직선 세그먼트 조정 (한 번만 수행)
                self._adjust_adjacent_straights(target_group)

        # 인덱스 및 station 갱신
        self._update_prev_next_entity_id()
        self._update_stations()
        self._update_group_index()

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

    def _process_remove_one_only(self):
        # PI 삭제
        self.coord_list.pop(1)

        target_group = self.groups[0]
        # 그룹 내부 세그먼트 제거
        if hasattr(target_group, "segments"):
            for seg in target_group.segments:
                if seg in self.segment_list:
                    self.segment_list.remove(seg)

        # 모든 곡선 그룹 제거
        self.groups.clear()

        # 직선 세그먼트 갱신
        # 시작 세그먼트만 남기고 남은 세그먼트 제거
        self.segment_list.pop(-1)

        # 남은 세그먼트 끝점 변경
        self.segment_list[0].end_coord = self.coord_list[-1]

        # 메타데이터 갱신
        self._update_prev_next_entity_id()
        self._update_group_index()
        self._update_stations()

    def _process_remove_pi(self, index: int):
        """지정된 PI 삭제 (복수 PI 존재 시 전용 루틴)"""
        self._remove_pi_coord(index)

        prev_group, target_group, next_group = self._find_adjacent_groups(index)
        if target_group is None:
            return
        self._finalize_update(prev_group, next_group)

        prev_seg, next_seg = self._remove_group_and_segments(target_group, target_group_idx=index - 1)

        self._cleanup_segments(prev_group, next_group, prev_seg, next_seg)


    # ================== 하위 메소드 ==================

    def _remove_pi_coord(self, index: int):
        """coord_list에서 PI 삭제"""
        self.coord_list.pop(index)

    def _find_adjacent_groups(self, index: int):
        """이전/현재/다음 그룹 반환"""
        target_group_idx = index - 1
        if 0 <= target_group_idx < len(self.groups):
            prev_group = self.groups[index - 2] if index - 2 >= 0 else None
            target_group = self.groups[index - 1]
            next_group = self.groups[index] if index < len(self.groups) else None
            return prev_group, target_group, next_group
        else:
            return None, None, None
    def _remove_group_and_segments(self, target_group, target_group_idx: int):
        """타깃 그룹과 그 내부 세그먼트 제거 후, 이전·다음 세그먼트 인덱스 반환"""
        prev_seg_index = target_group.segments[0].prev_index
        next_seg_index = target_group.segments[-1].next_index

        # 직선 세그먼트 탐색
        prev_seg = self.segment_list[prev_seg_index] if 0 <= prev_seg_index < len(self.segment_list) else None
        next_seg = self.segment_list[next_seg_index] if 0 <= next_seg_index < len(self.segment_list) else None

        # 그룹 세그먼트 제거
        for seg in list(target_group.segments):
            if seg in self.segment_list:
                self.segment_list.remove(seg)

        # 그룹 자체 제거
        if 0 <= target_group_idx < len(self.groups):
            del self.groups[target_group_idx]

        return prev_seg, next_seg

    def _cleanup_segments(self, prev_group, next_group, prev_seg, next_seg):
        """삭제 후 불필요한 직선 제거 및 연결 보정"""
        # 필요없는 직선 제거
        if next_group is None:
            if prev_seg in self.segment_list:
                self.segment_list.remove(prev_seg)
        else:
            if next_seg in self.segment_list:
                self.segment_list.remove(next_seg)

        # 인덱스 갱신
        self._update_prev_next_entity_id()
        self._update_group_index()

        # 인접 직선 보정
        if next_group:
            self._adjust_adjacent_straights(next_group)
        elif prev_group:
            self._adjust_adjacent_straights(prev_group)

    def _finalize_update(self, prev_group, next_group):
        """삭제 후 전체 메타데이터 갱신"""
        # 그룹 PI 좌표 갱신
        if prev_group and next_group:
            prev_group.update_by_pi(ep_coordinate=next_group.ip_coordinate)
            next_group.update_by_pi(bp_coordinate=prev_group.ip_coordinate)
        elif prev_group:
            prev_group.update_by_pi(ep_coordinate=self.coord_list[-1])
        elif next_group:
            next_group.update_by_pi(bp_coordinate=self.coord_list[0])

        # station 갱신
        self._update_stations()

    def _find_pi_interval(self, coord: Point2d) -> tuple[int, int]:
        """
        주어진 좌표(coord)가 어느 두 PI 사이에 속하는지 반환.
        (예: (1,2) → coord_list[1]과 coord_list[2] 사이)
        """
        if len(self.coord_list) < 2:
            raise ValueError("PI가 2개 이상 필요합니다.")

        min_dist = float('inf')
        nearest_index = None

        for i in range(len(self.coord_list) - 1):
            p1, p2 = self.coord_list[i], self.coord_list[i + 1]
            seg = StraightSegment(start_coord=p1, end_coord=p2)
            dist = seg.distance_to_point(coord)
            if dist < min_dist:
                min_dist = dist
                nearest_index = i

        return nearest_index, nearest_index + 1