from dataclasses import dataclass, field
import math
from AutoCAD.point2d import Point2d
from CIVIL3D.Alignment.alignmententitytype import AlignmentEntityType
from curvedirection import CurveDirection
from curvetype import CurveType
from data.segment.cubic_segment import CubicSegment
from data.segment.segment import Segment
from math_utils import calculate_bearing, is_invalid_arc, find_curve_direction
from data.segment.curve_segment import CurveSegment
from data.alignment.spiral.geometry import TransitionCurvatureCalculator
from data.alignment.spiral.params import TransitionCurveParams


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
        transition: 완화곡선 파라미터
    """
    group_id: int = 0
    segments: list[Segment] = field(default_factory=list)
    group_type: AlignmentEntityType = AlignmentEntityType.Arc
    bp_coordinate: Point2d = field(default_factory=lambda: Point2d(0, 0))
    ip_coordinate: Point2d = field(default_factory=lambda: Point2d(0, 0))
    ep_coordinate: Point2d = field(default_factory=lambda: Point2d(0, 0))
    radius: float = 0.0
    # 새로 추가
    transition: TransitionCurveParams | None = None

    @classmethod
    def create_from_pi(cls, group_id, bp, ip, ep, radius, isspiral, transition=None):
        """BP-IP-EP 좌표와 반경으로 SegmentGroup 생성"""
        #유효성 검사
        isinvalidcurve, messege =  is_invalid_arc(bp, ip, ep, radius)
        if isinvalidcurve:
            return None
        group = cls(group_id=group_id, bp_coordinate=bp, ip_coordinate=ip, ep_coordinate=ep, radius=radius)

        # 곡선 세그먼트 (IP)
        bp_azimuth = calculate_bearing(bp, ip)
        ep_azimuth = calculate_bearing(ip, ep)

        #단곡선 처리
        if not isspiral:
            curve = CurveSegment(
                start_azimuth=bp_azimuth,
                end_azimuth=ep_azimuth,
                radius=radius,
                ip_coordinate=ip,
                internal_angle=group.internal_angle,
                type=CurveType.Simple
            )

            group.segments.extend([curve])
        else:#완화곡선 처리
            #파라메터 계산 호출
            transition.cal_params(
                radius=radius,
                internal_angle=group.internal_angle,
                sp_type = None,
                m=transition.m,
                v=transition.v,
                z=transition.z
            )

            #좌표계산 호출
            cal = TransitionCurvatureCalculator(
                tr_params=transition,
                h1=bp_azimuth,
                h2=ep_azimuth,
                ip=group.ip_coordinate,
                direction=group.curve_direction
            )
            cal.run()

            #시작 완화곡선
            if group.curve_direction == CurveDirection.LEFT:
                end_theta = bp_azimuth + cal.params.theta_pc
            else:
                end_theta = bp_azimuth - cal.params.theta_pc

            start_spiral = CubicSegment(
                start_azimuth=bp_azimuth,
                end_azimuth=end_theta,
                radius=radius,
                isstarted=True,
                start_coord=cal.start_transition,
                end_coord=cal.start_circle,
                geom=cal,
                type=CurveType.Spiral
            )

            #중간 곡선
            curve = CurveSegment(
                start_azimuth=start_spiral.end_azimuth,
                end_azimuth=start_spiral.end_azimuth + cal.params.circle_internal_angle,
                radius=radius,
                ip_coordinate=ip,
                internal_angle=cal.params.circle_internal_angle,
                type=CurveType.Simple
            )

            #끝 완화곡선
            end_spiral = CubicSegment(
                start_azimuth=curve.end_azimuth,
                end_azimuth=curve.end_azimuth + cal.params.theta_pc,
                radius=radius,
                isstarted=False,
                start_coord=cal.end_circle,
                end_coord=cal.end_transition,
                geom=cal,
                type=CurveType.Spiral
            )
            group.group_type = AlignmentEntityType.SpiralCurveSpiral
            group.segments.extend([start_spiral, curve, end_spiral])
        return group

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
        for seg in self.segments:
            if isinstance(seg, CurveSegment):
                self._process_simple_curve(seg)
            elif isinstance(seg, CubicSegment):
                self._process_spiral(seg)

    def update_by_radius(self, radius: float):
        """그룹 내 곡선반경 변경"""
        if radius > 0:
            self.radius = radius
            # 세그먼트 갱신
            self._refresh_segment()

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
        v1 = calculate_bearing(self.bp_coordinate, self.ip_coordinate)
        v2 = calculate_bearing(self.ip_coordinate, self.ep_coordinate)
        # ±π 범위로 보정
        ia = v2 - v1
        if ia > math.pi:
            ia -= 2 * math.pi
        elif ia < -math.pi:
            ia += 2 * math.pi
        return abs(ia)

    @property
    def curve_direction(self):
        return find_curve_direction(self.bp_coordinate, self.ip_coordinate, self.ep_coordinate)

    def _process_simple_curve(self, segment: Segment):
        segment.start_azimuth = self.bp_azimuth
        segment.end_azimuth = self.ep_azimuth
        segment.ip_coordinate = self.ip_coordinate
        segment.internal_angle = self.internal_angle
        segment.radius = self.radius

    def _process_spiral(self, segment: CubicSegment):
        pass

    def _refresh_segment(self):
        for seg in self.segments:
            if isinstance(seg, CurveSegment):
                self._process_simple_curve(seg)
            elif isinstance(seg, CubicSegment):
                self._process_spiral(seg)