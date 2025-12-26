import math

from curvedirection import CurveDirection
from data.alignment.geometry.simplecurve.curvegeometry import CurveGeometry
from data.alignment.geometry.spiral.spiral_geometry import SpiralGeometry
from data.alignment.transition.calulator import TransitionCalulator
from data.alignment.transition.designresult import TransitionDesignResult
from data.alignment.transition.point_calulator import TransitionPointCalulator
from data.alignment.transition.tsinputdata import TransitionDesignInput


class TransitionDesignCalculator:
    """완화곡선 설계값을 토대로 결과 산출"""
    @staticmethod
    def solve(inputdata: TransitionDesignInput) -> TransitionDesignResult:
        """static: 설계 정보로부터 완화곡선 생성 (비대칭 / 대칭 모두 가능)
        Arugments:
            inputdata: 설계 데이터
        Return:
            TransitionDesignResult
        """
        bp_coordinate = inputdata.bp_coordinate
        ip_coordinate = inputdata.ip_coordinate
        ep_coordinate = inputdata.ep_coordinate
        ia = inputdata.internal_angle
        radius = inputdata.radius
        direction = inputdata.direction

        bp_azimuth = inputdata.bp_azimuth
        ep_azimuth = inputdata.ep_azimuth

        # 시작 완화곡선 파라메터 계산
        entry_params = inputdata.entry_params
        entry_params.cal_params()

        # 끝 완화곡선 파라메터 계산
        # 대칭인경우 동일하게
        issync = inputdata.issync
        if issync:
            exit_params = entry_params
        exit_params = inputdata.exit_params
        exit_params.cal_params()

        # 접선장 및 CL계산
        d1, d2, delta, lc = TransitionCalulator.cal_spec(radius, entry_params, exit_params, ia)

        # 좌표계산
        spiral_point_calculator = TransitionPointCalulator(
            ip=ip_coordinate,
            h1=bp_azimuth,
            h2=ep_azimuth,
            params1=entry_params,
            params2=exit_params,
            tl1=d1,
            tl2=d2,
            direction=direction,
        )
        spiral_point_calculator.run()
        #주요 좌표
        ts = spiral_point_calculator.start_transition
        st = spiral_point_calculator.end_transition
        sc = spiral_point_calculator.start_circle
        cs = spiral_point_calculator.end_circle
        cc = spiral_point_calculator.center_circle

        #주요 각도
        az_ts = bp_azimuth
        if direction == CurveDirection.LEFT:
            az_sc = bp_azimuth + entry_params.theta_pc
            az_cs = az_sc + delta
        else:
            az_sc = bp_azimuth - entry_params.theta_pc
            az_cs = az_sc - delta

        az_st = ep_azimuth

        # 지오메트리 생성
        entry_geometry = SpiralGeometry(direction=direction, params=entry_params)
        exit_geometry = SpiralGeometry(direction=direction, params=exit_params)
        curve_geometry = CurveGeometry(
            radius=radius,
            direction=direction,
            start_azimuth=az_sc,
            end_azimuth=az_cs,
            start_coord=sc,
            end_coord=cs,
        )
        # 세그먼트 생성은 밖에서 처리

        #결과 반환
        final_result = TransitionDesignResult(
            entry_geometry=entry_geometry,
            curve_geometry=curve_geometry,
            exit_geometry=exit_geometry,
            ts=ts,st=st,sc=sc,cs=cs,cc=cc,
            az_ts = az_ts,az_sc = az_sc,az_cs = az_cs,az_st = az_st
        )

        return final_result