from dataclasses import dataclass, field
from AutoCAD.point2d import Point2d
from CIVIL3D.Alignment.alignmententitytype import AlignmentEntityType
from data.segment.segment import Segment
from data.segment.segment_group.group_builder import SegmentGroupBuilder
from data.segment.segment_group.group_updater import SegmentGroupUpdater
from math_utils import calculate_bearing, find_curve_direction, calculator_internal_angle
from data.alignment.geometry.spiral.params import TransitionCurveParams


@dataclass
class SegmentGroup:
    """
    세그먼트 묶음 (단곡선, 직선, SCS 등)
    Attributes:
        group_id: 그룹 식별 인덱스
        segments: 세그먼트 객체 리스트
        group_type: 그룹 유형 (단곡선, 완화곡선-완화곡선 등) AlignmentEntityType
        bp_coordinate: BP좌표
        ip_coordinate: IP좌표
        ep_coordinate: EP좌표
        radius: 곡선반경R
        transition1: 시작 완화곡선 파라미터
        transition2: 끝 완화곡선 파라미터
        issync: 대칭 비대칭 여부
    """
    group_id: int = 0
    segments: list[Segment] = field(default_factory=list)
    group_type: AlignmentEntityType = AlignmentEntityType.Arc
    bp_coordinate: Point2d = field(default_factory=lambda: Point2d(0, 0))
    ip_coordinate: Point2d = field(default_factory=lambda: Point2d(0, 0))
    ep_coordinate: Point2d = field(default_factory=lambda: Point2d(0, 0))
    radius: float = 0.0
    # 새로 추가
    transition1: TransitionCurveParams | None = None
    transition2: TransitionCurveParams | None = None

    issync: bool = False

    @classmethod
    def create_from_pi(cls, group_id, bp, ip, ep, radius,
                       isspiral=False, transition1=None, transition2=None, issync=True):
        """BP-IP-EP 좌표와 반경으로 SegmentGroup 생성"""
        group = cls(
            group_id=group_id,
            bp_coordinate=bp,
            ip_coordinate=ip,
            ep_coordinate=ep,
            radius=radius,
        )

        return SegmentGroupBuilder.create_from_pi(group, group_id,bp,ip,ep,radius,isspiral,transition1,transition2,issync)

    def update_by_pi(self, bp_coordinate: Point2d = None, ip_coordinate: Point2d = None,
                         ep_coordinate: Point2d = None):
        """
        그룹 내 BP, IP, EP 좌표를 필요에 따라 갱신하고, 세그먼트 속성 재계산
        """
        if bp_coordinate is not None:
            self.bp_coordinate = bp_coordinate
        if ip_coordinate is not None:
            self.ip_coordinate = ip_coordinate
        if ep_coordinate is not None:
            self.ep_coordinate = ep_coordinate

        # 세그먼트 갱신
        SegmentGroupUpdater.update(self)

    def update_by_radius(self, radius: float):
        """그룹 내 곡선반경 변경"""
        if radius > 0:
            self.radius = radius
            # 세그먼트 갱신
            SegmentGroupUpdater.update(self)

    @property
    def bp_azimuth(self) -> float:
        """BP → IP 방향 방위각"""
        return calculate_bearing(self.bp_coordinate, self.ip_coordinate)

    @property
    def ep_azimuth(self) -> float:
        """IP → EP 방향 방위각"""
        return calculate_bearing(self.ip_coordinate, self.ep_coordinate)

    @property
    def start_coord(self):
        """그룹 첫번째 시작 좌표"""
        return self.segments[0].start_coord

    @property
    def end_coord(self):
        """그룹 마지막 요소 끝 좌표"""
        return self.segments[-1].end_coord

    @property
    def total_length(self):
        """그룹 전체 길이"""
        return sum(seg.length for seg in self.segments)

    @property
    def internal_angle(self):
        return calculator_internal_angle(self.bp_coordinate, self.ip_coordinate, self.ep_coordinate)

    @property
    def curve_direction(self):
        return find_curve_direction(self.bp_coordinate, self.ip_coordinate, self.ep_coordinate)
