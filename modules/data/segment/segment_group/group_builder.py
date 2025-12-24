from data.alignment.simplecurve.simple_curve_dc import SimpleCurveDesignCalculator
from data.alignment.simplecurve.simplec_inputdata import SimpleCurveDesignInput
from data.alignment.transition.tsdesigncal import TransitionDesignCalculator
from data.alignment.transition.tsinputdata import TransitionDesignInput
from data.segment.cubic_segment import CubicSegment
from data.segment.curve_segment import CurveSegment
from math_utils import is_invalid_arc, calculate_bearing, find_curve_direction, calculator_internal_angle
from CIVIL3D.Alignment.alignmententitytype import AlignmentEntityType

class SegmentGroupBuilder:
    @staticmethod
    def create_from_pi(group, group_id, bp, ip, ep, radius,
                       isspiral=False, transition1=None, transition2=None, issync=True):

        """BP-IP-EP 좌표와 반경으로 SegmentGroup 생성"""
        # 유효성 검사
        isinvalidcurve, messege = is_invalid_arc(bp, ip, ep, radius)
        if isinvalidcurve:
            return None

        # 시작 , 끝 방위각 계산
        bp_azimuth = calculate_bearing(bp, ip)
        ep_azimuth = calculate_bearing(ip, ep)

        # 방향
        direction = find_curve_direction(bp, ip, ep)

        # 교각 계산
        ia = calculator_internal_angle(bp, ip, ep)

        # 단곡선 처리
        if not isspiral:
            # 입력데이터 주입
            simpleinput = SimpleCurveDesignInput(
                bp_coordinate=bp, ip_coordinate=ip, ep_coordinate=ep, radius=radius,
                internal_angle=ia,
                bp_azimuth=bp_azimuth, ep_azimuth=ep_azimuth, direction=direction
            )
            # 지오메트리 계산
            curve_goem = SimpleCurveDesignCalculator.solve(simpleinput)
            # 세그먼트 생성
            curve_segment = CurveSegment(_geom=curve_goem)

            group.segments.extend([curve_segment])
        else:  # 완화곡선 처리
            # 파라메터 계산 호출
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
            # 지오메트리 계산
            final_result = TransitionDesignCalculator.solve(spiral_input)
            # 세그먼트 생성
            # 시작 완화곡선
            start_spiral = CubicSegment(isstarted=True, geom=final_result.entry_geometry,
                                        params=transition1, start_coord=final_result.ts,
                                        end_coord=final_result.sc,
                                        start_azimuth=final_result.az_ts,
                                        end_azimuth=final_result.az_sc,
                                        )
            # 중간 원곡선
            curve = CurveSegment(_geom=final_result.curve_geometry)

            # 끝 완화곡선
            end_spiral = CubicSegment(isstarted=False, geom=final_result.exit_geometry,
                                      params=transition2, start_coord=final_result.cs,
                                      end_coord=final_result.st,
                                      start_azimuth=final_result.az_cs,
                                      end_azimuth=final_result.az_st,
                                      )

            group.group_type = AlignmentEntityType.SpiralCurveSpiral
            group.segments.extend([start_spiral, curve, end_spiral])
        return group
