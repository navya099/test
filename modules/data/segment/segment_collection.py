from AutoCAD.point2d import Point2d
from data.alignment.exception.alignment_error import NoUpdatePIError, CurveCreationError

from data.segment.group_manager import GroupManager
from data.pi_manager import PIManager
from data.segment.segment import Segment
from data.segment.segment_group.segment_group import SegmentGroup
from data.segment.segment_manager import SegmentManager


class SegmentCollection:
    """SegmentGroup 관리 컬렉션"""
    def __init__(self):
        self._pi_manager = PIManager()
        self._segment_manager = SegmentManager()
        self._group_manager = GroupManager()

    # 외부 참조용 property
    @property
    def coord_list(self) -> list[Point2d]:
        """PI좌표 리스트"""
        return self._pi_manager.coord_list

    @property
    def radius_list(self) -> list[float]:
        """곡선반경 리스트"""
        return self._pi_manager.radius_list

    @property
    def segment_list(self) -> list[Segment]:
        """세그먼트 리스트"""
        return self._segment_manager.segment_list

    @property
    def groups(self) -> list[SegmentGroup]:
        """그룹들"""
        return self._group_manager.groups

    def create_by_pi_coords(self, coord_list, radius_list):
        """PI와 radius 리스트로 전체 세그먼트 빌드"""
        self._pi_manager.coord_list = coord_list
        self._pi_manager.radius_list = radius_list
        self._group_manager.groups = [None] * len(coord_list)
        self._segment_manager.segment_list.clear()

        # 그룹 생성 위임
        n = len(coord_list)
        i = 0
        try:
            for i in range(n - 1):
                self._group_manager.create_group_at_index(i, self._pi_manager)

            # 그룹 연결 + 경계 직선 추가 → 세그먼트 리스트 완성
            self._segment_manager.build_segments(self.coord_list, self.groups)

            # 세그먼트 인덱스/STA 갱신
            self._update_attirbutes()
        except Exception as e:
            raise CurveCreationError(i)

    # API 노출 메서드
    def update_pi_and_radius_by_index(self, pipoint, radius, index):
        """공개API 주어진 PI와 radius로 업데이트"""
        if index <= 0 or index >= len(self.coord_list) - 1:
            raise NoUpdatePIError(index)
        self._update_pi(index=index, pipoint=pipoint, radius=radius)

    def _update_pi(self, index=None, pipoint=None, radius=None):
        """pi 갱신 API"""
        self._pi_manager.update_pi(index=index, coord=pipoint, radius=radius)
        self.create_by_pi_coords(self.coord_list, self.radius_list)

    def remove_pi(self, index=None):

        """pi 삭제 API"""
        self._pi_manager.remove_pi(index=index)
        self.create_by_pi_coords(self.coord_list, self.radius_list)

    def add_pi(self, pipoint=None, radius=None):
        """pi 추가 API"""
        self._pi_manager.add_pi(coord=pipoint, radius=radius)
        self.create_by_pi_coords(self.coord_list, self.radius_list)

    def update_bp_ep(self, index, point):
        """노선 시작점(BP), 끝점(EP) 갱신 API"""
        if not self.coord_list:
            return
        # 시작점(0) 또는 끝점(len-1)만 허용
        if index != 0 and index != len(self.coord_list) - 1:
            return
        # 좌표 갱신
        self._pi_manager.update_pi(index=index, coord=point, radius=None)
        # 세그먼트 재생성
        self.create_by_pi_coords(self.coord_list, self.radius_list)

    #내부 비공개 메서드
    #private
    def _update_attirbutes(self):
        self._segment_manager.update_prev_next_entity_id()
        self._segment_manager.update_stations()
        self._group_manager.update_group_index()




