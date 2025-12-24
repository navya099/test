from CIVIL3D.Alignment.alignmententitytype import AlignmentEntityType
from data.alignment.simplecurve.simple_curve_dc import SimpleCurveDesignCalculator
from data.alignment.simplecurve.simplec_inputdata import SimpleCurveDesignInput
from data.alignment.transition.tsdesigncal import TransitionDesignCalculator
from data.alignment.transition.tsinputdata import TransitionDesignInput

class SegmentGroupUpdater:
    @staticmethod
    def update(group):
        if group.group_type == AlignmentEntityType.Arc:
            SegmentGroupUpdater._update_arc(group)
        else:
            SegmentGroupUpdater._update_spiral(group)

    @staticmethod
    def _update_arc(group):
        """단곡선 변경사항 처리"""
        changeinput = SimpleCurveDesignInput(
            bp_coordinate=group.bp_coordinate,
            ip_coordinate=group.ip_coordinate,
            ep_coordinate=group.ep_coordinate,
            radius=group.radius,
            internal_angle=group.internal_angle,
            bp_azimuth=group.bp_azimuth,
            ep_azimuth=group.ep_azimuth,
            direction=group.curve_direction
        )
        # 지오메트리 계산
        new_goem = SimpleCurveDesignCalculator.solve(changeinput)
        # 세그먼트 지오메트리 변경
        group.segments[0]._geom = new_goem

    @staticmethod
    def _update_spiral(group):
        """완화곡선 변경사항 처리"""
        # 파라메터 계산 호출
        # 입력데이터 주입
        spiral_input = TransitionDesignInput(
            bp_coordinate=group.bp_coordinate,
            ip_coordinate=group.ip_coordinate,
            ep_coordinate=group.ep_coordinate,
            radius=group.radius,
            internal_angle=group.internal_angle,
            bp_azimuth=group.bp_azimuth,
            ep_azimuth=group.ep_azimuth,
            direction=group.curve_direction,
            entry_params=group.transition1,
            exit_params=group.transition2,
            issync=group.issync
        )
        # 지오메트리 계산
        final_result = TransitionDesignCalculator.solve(spiral_input)
        # 세그먼트 갱신
        start_spiral = group.segments[0]
        middle_circle = group.segments[1]
        end_spiral = group.segments[-1]

        # 시작 완화곡선
        start_spiral.geom = final_result.entry_geometry
        start_spiral.params = group.transition1
        start_spiral.start_coord = final_result.ts
        start_spiral.end_coord = final_result.sc
        start_spiral.start_azimuth = final_result.az_ts
        start_spiral.end_azimuth = final_result.az_sc
        # 중간 원곡선
        middle_circle.geom = final_result.curve_geometry
        # 끝 완화곡선
        end_spiral.geom = final_result.exit_geometry
        end_spiral.params = group.transition2
        end_spiral.start_coord = final_result.cs
        end_spiral.end_coord = final_result.st
        end_spiral.start_azimuth = final_result.az_cs
        end_spiral.end_azimuth = final_result.az_st