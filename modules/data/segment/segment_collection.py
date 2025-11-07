from AutoCAD.point2d import Point2d
from data.alignment.exception.alignment_error import NotEnoughPIPointError, InvalidGeometryError, PIOutOfRangeError, \
    NoUpdatePIError, NoDeletePIError, RadiusError, GroupNullError, AlreadyHasCurveError
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
        # 그룹 리스트를 coord_list 길이에 맞게 None으로 초기화
        self._group_manager.groups = [None] * len(coord_list)
        self._segment_manager.segment_list.clear()

        # 내부 빌드 호출
        n = len(coord_list)
        for i in range(n - 1):
            self._process_segment_at_index(i)

        self._update_prev_next_entity_id()
        self._update_stations()
        self._update_group_index()

    def add_curve_at_simple_curve(self, index: int, radius: float):
        """
        주어진 PI에 단순 원곡선 추가
        - index: 커브를 추가할 PI 인덱스
        - radius: 커브 반경 (R)
        """
        if not (0 < index < len(self.coord_list) - 1):
            raise PIOutOfRangeError(index)

        # 이미 커브가 존재하면 중복 방지
        existing_group = self._group_manager.groups[index]
        if existing_group:
            raise AlreadyHasCurveError(index)

        #radius 리스트에 추가
        self._pi_manager.radius_list[index] = radius

        # --- 기존 직선 구간 정리 ---
        # index 기준 앞뒤 직선 세그먼트를 삭제해야 새 커브 생성 가능
        prev_seg ,next_seg = self._segment_manager.find_straight_by_coord(self.coord_list[index])

        # --- 커브 그룹 생성 ---
        self._process_segment_at_index(index, rebuild_mode=False)

        # --- 후속 처리 ---
        self._update_prev_next_entity_id()
        self._update_group_index()
        self._update_stations()

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
        if len(self.coord_list) == 3:
            self._process_remove_one_only()
        else:
            self._process_remove_pi(index)

    def add_pi_by_coord(self, coord: Point2d):
        """공개 API PI 삽입"""
        #예외탐지
        if not self.segment_list:
            raise SegmentListNullError()

        # 1️⃣ 가장 가까운 세그먼트 탐색
        nearest_seg = self._segment_manager.find_nearest_segment(coord)

        #예외 없으면 실행
        self._insert_pi_in_segment(coord, nearest_seg)

    def remove_curve_at_pi_by_index(self, index: int):
        """주어진 PI의 커브만 제거 (PI는 남김)"""
        if not (0 <= index < len(self.coord_list)):
            raise PIOutOfRangeError(index)

        target_pi = self.coord_list[index]

        # 삭제 전 PI 주변 그룹 및 직선 참조
        # 이전, 대상, 다음 그룹 얻기
        prev_group, target_group, next_group = self._group_manager.get_prev_next_groups(index)

        # 커브가 없으면 종료
        if not target_group:
            raise GroupNullError()

        # 🧩 1. 그룹 내부 세그먼트 제거
        prev_seg, next_seg = self._segment_manager.remove_segments(target_group)

        # 🧩 2. 그룹 none으로 초기화
        self._group_manager.groups[index] = None

        # 🧩 3. 삭제된 양끝 직선 재연결
        if prev_seg and next_seg:
            # 기존 커브 구간을 하나의 직선으로 대체
            prev_seg.end_coord=target_pi
            next_seg.start_coord=target_pi
        self._update_prev_next_entity_id()

        # 🧩 4. 인접 세그먼트 보정
        if prev_group:
            prev_group.update_by_pi(ep_coordinate=target_pi)
            self._segment_manager.adjust_adjacent_straights(prev_group)
        if next_group:
            next_group.update_by_pi(bp_coordinate=target_pi)
            self._segment_manager.adjust_adjacent_straights(next_group)

        # 4-1 radiuslist NONE 초기화
        self._pi_manager.radius_list[index] = None

        # 🧩 5. 인덱스 및 참조 갱신
        self._update_prev_next_entity_id()
        self._update_group_index()
        self._update_stations()

    def _insert_pi_in_segment(self, coord, nearest_seg):
        """
        주어진 좌표 근처의 세그먼트에 PI를 삽입.
        :param coord: (x, y)
        :return: (삽입된 PI 인덱스)
        """

        # 2️⃣ 삽입 위치(해당 세그먼트의 인덱스) 찾기
        seg_index = nearest_seg.current_index

        #세그먼트 분활
        new_seg = nearest_seg.split_to_segment(coord)

        #세그먼트 리스트에 추가
        self._segment_manager.segment_list.insert(seg_index + 1, new_seg)
        #인덱스 갱신
        self._update_prev_next_entity_id()

        #pi인덱스 찾기
        prev_pi_index, next_pi_index = self._pi_manager.find_pi_interval(coord)
        #pi 삽입
        self._pi_manager.coord_list.insert(next_pi_index, coord)
        # pi추가시 동기화
        self._group_manager.groups.insert(next_pi_index, None)
        self._pi_manager.radius_list.insert(next_pi_index, None)  # 반경도 1:1 유지

        #다시 변경된 리스트에서 이전 다음 pi index 찾기
        prev_pi_index, next_pi_index = self._pi_manager.find_pi_interval(coord)

        # 3️⃣ PI 주변 그룹 찾기
        # 이전, 대상, 다음 그룹 얻기
        prev_group, target_group, next_group = self._group_manager.get_prev_next_groups(prev_pi_index + 1)

        # 4️⃣ 그룹 갱신 (곡선 존재할 때만)
        if prev_group:
            prev_group.update_by_pi(ep_coordinate=coord)
            self._segment_manager.adjust_adjacent_straights(prev_group)
        if next_group:
            next_group.update_by_pi(bp_coordinate=coord)
            self._segment_manager.adjust_adjacent_straights(next_group)

        #인덱스 및 그룹 및 station 갱신
        self._update_prev_next_entity_id()
        self._update_group_index()
        self._update_stations()

    def _process_segment_at_index(self, i: int, *, rebuild_mode=True):
        """
        내부: index 기준 세그먼트(직선/곡선) 생성
        - rebuild_mode=True  → 전체 재생성 루프용
        - rebuild_mode=False → 부분 삽입용 (기존 직선/그룹 유지)
        """
        n = len(self.coord_list)
        if n < 2:
            raise NotEnoughPIPointError()

        # === 곡선이 가능한 구간 ===
        if 0 < i < n - 1:
            bp = self.coord_list[i - 1]
            ip = self.coord_list[i]
            ep = self.coord_list[i + 1]
            r = self.radius_list[i]
            isspiral = False

            # --- 그룹 생성 시도 ---
            group = self._group_manager.create_curve_group(i, bp, ip, ep, r, isspiral)
            if group is None:
                if rebuild_mode:
                    self.groups.clear()
                    self.segment_list.clear()
                raise InvalidGeometryError(f"곡선 그룹 생성 실패: PI {i}")

            # --- 모드별 처리 ---
            if rebuild_mode:
                # 전체 빌드 루프에서 사용하는 경우
                self._adjust_previous_straight(group)
                self._segment_manager.segment_list.extend(group.segments)
                self._append_next_straight(group, i)
            else:
                # 부분 삽입 모드
                for seg in group.segments:
                    self._segment_manager.segment_list.insert(i, seg)
                    i += 1
                self._segment_manager.adjust_adjacent_straights(group)
                self._update_prev_next_entity_id()

            #그룹리스트 갱신
            self._group_manager.groups[i] = group
            #RADIUS리스트 갱신
            self._pi_manager.radius_list[i] = r

        # === 첫/마지막 PI ===
        else:
            bp = self.coord_list[i]
            ep = self.coord_list[i + 1]
            straight = StraightSegment(start_coord=bp, end_coord=ep)
            if rebuild_mode:
                self.segment_list.append(straight)
            else:
                self._segment_manager.insert_straight(i, straight)

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
        if radius is not None:
            self._pi_manager.radius_list[index] = radius

        #이전, 대상, 다음 그룹 얻기
        prev_group ,target_group, next_group =  self._group_manager.get_prev_next_groups(index)


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
    def _update_group_internal(self, prev_group, target_group, next_group, old_pi_coord, pipoint, radius):
        """
        내부 그룹 갱신 메서드
        - prev_group: 이전 그룹
        target_group: 대상 그룹
        next_group: 다음 그룹
        - pipoint: 변경할 PI 좌표 (없으면 PI 변경 안함)
        - radius: 변경할 곡선 반경 (없으면 반경 변경 안함)
        """

        # --- 그룹별 갱신 ---
        if pipoint is not None:
            if target_group:
                target_group.update_by_pi(ip_coordinate=pipoint)
                self._segment_manager.adjust_adjacent_straights(target_group)
            else:
                self._segment_manager.adjust_adjacent_straights_without_group(old_pi_coord, pipoint)
            if prev_group:
                prev_group.update_by_pi(ep_coordinate=pipoint)
                self._segment_manager.adjust_adjacent_straights(prev_group)
            else:
                self._segment_manager.adjust_adjacent_straights_without_group(old_pi_coord, pipoint)
            if next_group:
                next_group.update_by_pi(bp_coordinate=pipoint)
                self._segment_manager.adjust_adjacent_straights(next_group)
            else:
                self._segment_manager.adjust_adjacent_straights_without_group(old_pi_coord, pipoint)

        if radius is not None:
            if target_group:
                target_group.update_by_radius(radius)
                self._segment_manager.adjust_adjacent_straights(target_group)

    def _update_group_index(self):
        """
        groups 리스트에 있는 각 SegmentGroup의 인덱스를 0부터 순서대로 갱신
        """
        for idx, group in enumerate(self.groups):
            if group:
                group.group_index = idx

    def _process_remove_one_only(self):
        # PI 삭제
        self._pi_manager.coord_list.pop(1)

        target_group = self.groups[1]
        # 그룹 내부 세그먼트 제거
        if hasattr(target_group, "segments"):
            for seg in target_group.segments:
                if seg in self.segment_list:
                    self._segment_manager.segment_list.remove(seg)

        # 모든 곡선 그룹 제거 후 NONE 초기화
        self._group_manager.groups = [None] * len(self._pi_manager.coord_list)
        #모든 RADIUS 초기화
        self._pi_manager.radius_list = [None] * len(self._pi_manager.coord_list)

        # 직선 세그먼트 갱신
        # 시작 세그먼트만 남기고 남은 세그먼트 제거
        self._segment_manager.segment_list.pop(-1)

        # 남은 세그먼트 끝점 변경
        self._segment_manager.segment_list[0].end_coord = self.coord_list[-1]

        # 메타데이터 갱신
        self._update_prev_next_entity_id()
        self._update_group_index()
        self._update_stations()

    def _process_remove_pi(self, index: int):
        """지정된 PI 삭제"""
        deleted_pi = self.coord_list[index]

        # 삭제 전 PI 주변 그룹 및 직선 참조
        prev_group, target_group, next_group = self._group_manager.get_prev_next_groups(index)

        # 2️⃣ 그룹 확인
        if target_group:
            self._process_remove_pi_with_group(prev_group, target_group, next_group, deleted_pi)
        else:
            self._process_remove_pi_without_group(deleted_pi)

        # 인접 직선 보정
        if next_group:
            next_group.update_by_pi(bp_coordinate=self.coord_list[index - 1])
            self._segment_manager.adjust_adjacent_straights(next_group)
        if prev_group:
            prev_group.update_by_pi(ep_coordinate=self.coord_list[index + 1])
            self._segment_manager.adjust_adjacent_straights(prev_group)

        # 1️⃣ PI 삭제
        self._pi_manager.coord_list.pop(index)

        # radiuslist에서 삭제
        self._pi_manager.radius_list.pop(index)

        # 4️⃣ 인덱스/그룹/스테이션 갱신
        self._update_prev_next_entity_id()
        self._update_group_index()
        self._update_stations()

    def _process_remove_pi_with_group(self, prev_group, target_group, next_group, deleted_pi_coord):
        #그룹 조정
        self._update_group_after_delete(prev_group, target_group, next_group, deleted_pi_coord)

        #그룹 내부 세그먼트 제거 후 이전 세그 다음 세그 반환
        prev_seg, next_seg = self._segment_manager.remove_segments(target_group)
        #그룹 삭제
        self._group_manager.delete_group(target_group)
        #세그먼트 삭제후 신설
        self._segment_manager.delete_segment_in_list(prev_seg)
        self._segment_manager.delete_segment_in_list(next_seg)

        # 인덱스 갱신
        self._update_prev_next_entity_id()

        #신설
        new_seg = StraightSegment(start_coord=prev_seg.start_coord, end_coord=next_seg.end_coord)
        # 리스트에 추가
        self._segment_manager.segment_list.insert(prev_seg.current_index, new_seg)

        # 인덱스 갱신
        self._update_prev_next_entity_id()

    def _process_remove_pi_without_group(self, deleted_pi):
        """
        그룹이 없는 PI 삭제 시 — 직선 2개를 제거하고 1개의 새 직선으로 연결
        """
        # 1️⃣ 삭제 대상 PI의 인덱스 찾기
        pi_index = self.coord_list.index(deleted_pi)

        # 삭제 전후의 PI 좌표 (직선 2개를 잇기 위한)
        prev_pi = self.coord_list[pi_index - 1] if pi_index > 0 else None
        next_pi = self.coord_list[pi_index + 1] if pi_index + 1 < len(self.coord_list) else None

        if not (prev_pi and next_pi):
            # 양쪽 PI가 모두 있어야 새 직선을 생성 가능
            return

        # 2️⃣ 삭제 대상 PI를 기준으로 직선 세그먼트 탐색
        prev_seg, next_seg = self._segment_manager.find_straight_by_coord(deleted_pi)

        # 3️⃣ 두 직선 삭제
        if prev_seg:
            self._segment_manager.delete_segment_in_list(prev_seg)
        if next_seg:
            self._segment_manager.delete_segment_in_list(next_seg)

        # 4️⃣ 새 직선 생성
        new_seg = StraightSegment(start_coord=prev_pi, end_coord=next_pi)
        insert_index = prev_seg.current_index if prev_seg else 0
        self._segment_manager.segment_list.insert(insert_index, new_seg)
        self._update_prev_next_entity_id()

    def _update_group_after_delete(self, prev_group, target_group, next_group, deleted_pi_coord: Point2d):
        """
        삭제된 PI 기준으로 주변 그룹/직선 갱신
        """
        #이전 그룹와 다음 그룹이 모두 존재할경우
        if prev_group and next_group:
            prev_group.update_by_pi(ep_coordinate=next_group.ip_coordinate)
            next_group.update_by_pi(bp_coordinate=prev_group.ip_coordinate)
            self._segment_manager.adjust_adjacent_straights(prev_group)
            self._segment_manager.adjust_adjacent_straights(next_group)
        #다음 그룹만 존재
        elif prev_group is None and next_group:
            #이전 그룹 대신 이전 pi를 얻어서 갱신
            prev_pi_index = self.coord_list.index(deleted_pi_coord)  - 1
            prev_pi = self.coord_list[prev_pi_index]
            next_group.update_by_pi(bp_coordinate=prev_pi)
            self._segment_manager.adjust_adjacent_straights(next_group)
        #이전 그룹만 존재
        elif next_group is None and prev_group:
            # 다음 그룹 대신 다음 pi를 얻어서 갱신
            next_pi_index = self.coord_list.index(deleted_pi_coord) + 1
            next_pi = self.coord_list[next_pi_index]
            prev_group.update_by_pi(ep_coordinate=next_pi)
            self._segment_manager.adjust_adjacent_straights(prev_group)
        #모두 NONE
        elif next_group is None and prev_group is None:
            # 이전 그룹 및 다음 그룹 대신 이전 다음 pi를 얻어서 갱신
            prev_pi_index = self.coord_list.index(deleted_pi_coord) - 1
            prev_pi = self.coord_list[prev_pi_index]
            next_pi_index = self.coord_list.index(deleted_pi_coord) + 1
            next_pi = self.coord_list[next_pi_index]