from dataclasses import dataclass, field
import math
from AutoCAD.point2d import Point2d
from CIVIL3D.Alignment.alignmententitytype import AlignmentEntityType
from curvedirection import CurveDirection
from curvetype import CurveType
from data.alignment.geometry.simplecurve.curvegeometry import CurveGeometry
from data.alignment.geometry.spiral.spiral_geometry import SpiralGeometry
from data.alignment.simplecurve.simple_curve_dc import SimpleCurveDesignCalculator
from data.alignment.simplecurve.simplec_inputdata import SimpleCurveDesignInput
from data.alignment.transition.tsdesigncal import TransitionDesignCalculator
from data.alignment.transition.tsinputdata import TransitionDesignInput
from data.segment.cubic_segment import CubicSegment
from data.segment.segment import Segment
from math_utils import calculate_bearing, is_invalid_arc, find_curve_direction, calculator_internal_angle
from data.segment.curve_segment import CurveSegment
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
        #유효성 검사
        isinvalidcurve, messege =  is_invalid_arc(bp, ip, ep, radius)
        if isinvalidcurve:
            return None
        group = cls(group_id=group_id, bp_coordinate=bp, ip_coordinate=ip, ep_coordinate=ep, radius=radius)

        #시작 , 끝 방위각 계산
        bp_azimuth = calculate_bearing(bp, ip)
        ep_azimuth = calculate_bearing(ip, ep)

        #방향
        direction = find_curve_direction(bp, ip, ep)

        #교각 계산
        ia = calculator_internal_angle(bp, ip, ep)

        #단곡선 처리
        if not isspiral:
            #입력데이터 주입
            simpleinput = SimpleCurveDesignInput(
                bp_coordinate=bp, ip_coordinate=ip, ep_coordinate=ep, radius=radius,
                internal_angle=ia,
                bp_azimuth=bp_azimuth,ep_azimuth=ep_azimuth,direction=direction
            )
            #지오메트리 계산
            curve_goem = SimpleCurveDesignCalculator.solve(simpleinput)
            #세그먼트 생성
            curve_segment = CurveSegment(_geom=curve_goem)

            group.segments.extend([curve_segment])
        else:#완화곡선 처리
            #파라메터 계산 호출
            # 입력데이터 주입
            spiral_input = TransitionDesignInput(
                bp_coordinate=bp,
                ip_coordinate=ip,
                ep_coordinate=ep,
                radius=radius,
                internal_angle=ia,
                bp_azimuth=bp_azimuth,
                ep_azimuth=ep_azimuth,
                direction=direction,
                entry_params=transition1,
                exit_params=transition2,
                issync=issync
            )
            #지오메트리 계산
            final_result = TransitionDesignCalculator.solve(spiral_input)
            #세그먼트 생성
            #시작 완화곡선
            start_spiral = CubicSegment(isstarted=True,geom=final_result.entry_geometry,
                                        params=transition1,start_coord=final_result.ts,
                                        end_coord=final_result.sc,
                                        start_azimuth=final_result.az_ts,
                                        end_azimuth=final_result.az_sc,
                )
            #중간 원곡선
            curve = CurveSegment(_geom=final_result.curve_geometry)

            #끝 완화곡선
            end_spiral = CubicSegment(isstarted=False,geom=final_result.exit_geometry,
                                        params=transition2,start_coord=final_result.cs,
                                        end_coord=final_result.st,
                                        start_azimuth=final_result.az_cs,
                                        end_azimuth=final_result.az_st,
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
        self._refresh_segment()

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
        return calculator_internal_angle(self.bp_coordinate, self.ip_coordinate, self.ep_coordinate)

    @property
    def curve_direction(self):
        return find_curve_direction(self.bp_coordinate, self.ip_coordinate, self.ep_coordinate)

    def _process_simple_curve(self, segment: CurveSegment):
        """단곡선 변경사항 처리"""
        changeinput = SimpleCurveDesignInput(
            bp_coordinate=self.bp_coordinate,
            ip_coordinate=self.ip_coordinate,
            ep_coordinate=self.ep_coordinate,
            radius=self.radius,
            internal_angle=self.internal_angle,
            bp_azimuth=self.bp_azimuth,
            ep_azimuth=self.ep_azimuth,
            direction=self.curve_direction
        )
        # 지오메트리 계산
        new_goem = SimpleCurveDesignCalculator.solve(changeinput)
        # 세그먼트 지오메트리 변경
        segment._geom = new_goem


    def _process_spiral(self, segments: list[Segment]):
        """완화곡선 변경사항 처리"""
        # 파라메터 계산 호출
        # 입력데이터 주입
        spiral_input = TransitionDesignInput(
            bp_coordinate=self.bp_coordinate,
            ip_coordinate=self.ip_coordinate,
            ep_coordinate=self.ep_coordinate,
            radius=self.radius,
            internal_angle=self.internal_angle,
            bp_azimuth=self.bp_azimuth,
            ep_azimuth=self.ep_azimuth,
            direction=self.curve_direction,
            entry_params=self.transition1,
            exit_params=self.transition2,
            issync=self.issync
        )
        # 지오메트리 계산
        final_result = TransitionDesignCalculator.solve(spiral_input)
        # 세그먼트 갱신
        start_spiral = segments[0]
        middle_circle = segments[1]
        end_spiral = segments[-1]

        # 시작 완화곡선
        start_spiral.geom=final_result.entry_geometry
        start_spiral.params=self.transition1
        start_spiral.start_coord=final_result.ts
        start_spiral.end_coord=final_result.sc
        start_spiral.start_azimuth=final_result.az_ts
        start_spiral.end_azimuth=final_result.az_sc
        #중간 원곡선
        middle_circle.geom=final_result.curve_geometry
        # 끝 완화곡선
        end_spiral.geom = final_result.exit_geometry
        end_spiral.params = self.transition2
        end_spiral.start_coord = final_result.cs
        end_spiral.end_coord = final_result.st
        end_spiral.start_azimuth = final_result.az_cs
        end_spiral.end_azimuth = final_result.az_st

    def _refresh_segment(self):
        if self.group_type == AlignmentEntityType.Arc:
            for seg in self.segments:
                if isinstance(seg, CurveSegment):
                    self._process_simple_curve(seg)
        elif self.group_type == AlignmentEntityType.SpiralCurveSpiral:
            self._process_spiral(self.segments)