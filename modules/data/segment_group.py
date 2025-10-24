from dataclasses import dataclass, field
import math
from AutoCAD.point2d import Point2d
from CIVIL3D.Alignment.alignmententitytype import AlignmentEntityType
from curvetype import CurveType
from data.cubic_segment import CubicSegment
from data.segment import Segment
from math_utils import calculate_bearing, is_invalid_arc
from data.curve_segment import CurveSegment

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
    """
    group_id: int = 0
    segments: list[Segment] = field(default_factory=list)
    group_type: AlignmentEntityType = AlignmentEntityType.Arc
    bp_coordinate: Point2d = field(default_factory=lambda: Point2d(0, 0))
    ip_coordinate: Point2d = field(default_factory=lambda: Point2d(0, 0))
    ep_coordinate: Point2d = field(default_factory=lambda: Point2d(0, 0))
    radius: float = 0.0

    @classmethod
    def create_from_pi(cls, group_id, bp, ip, ep, radius, isspiral):
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
        else:
            spiral1 = CubicSegment()
            curve = CurveSegment()
            spiral2 = CubicSegment()
            group.segments.extend([spiral1, curve, spiral2])
        return group

    def update_by_pi(self, ip_coordinate: Point2d):
        """
        기존 세그먼트를 재활용하면서 IP 좌표 변경에 따른 속성 갱신
        - 객체 재생성 없이 내부 속성만 업데이트
        """
        # 좌표만 교체
        self.ip_coordinate = ip_coordinate

        for seg in self.segments:
            if isinstance(seg, CurveSegment):
                seg.start_azimuth = self.bp_azimuth
                seg.end_azimuth = self.ep_azimuth
                seg.ip_coordinate = self.ip_coordinate
                seg.internal_angle = self.internal_angle

            elif isinstance(seg, CubicSegment):
                # 완화곡선의 경우 spline control point만 재조정 (예시)
               raise NotImplementedError

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
        """그룹 전채 길이"""
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
        return ia

    def _process_simple_curve(self):
        pass
    def _process_spiral(self):
        pass