from dataclasses import dataclass
import math

from curvedirection import CurveDirection
from data.alignment.geometry.simplecurve.curvegeometry import CurveGeometry
from data.alignment.simplecurve.simplec_inputdata import SimpleCurveDesignInput


@dataclass
class SimpleCurveDesignCalculator:
    """설계 정보로부터 단곡선 생성 클래스"""
    @staticmethod
    def solve(inputdata: SimpleCurveDesignInput):
        """static: 설계 정보로부터 단곡선 생성 메서드
            Arugments:
                inputdata: 설계 데이터
            Return:
                curve_geomtry
            """
        bp_coordinate = inputdata.bp_coordinate
        ip = inputdata.ip_coordinate
        ep_coordinate = inputdata.ep_coordinate
        ia = inputdata.internal_angle
        radius = inputdata.radius
        direction = inputdata.direction

        bp_azimuth = inputdata.bp_azimuth
        ep_azimuth = inputdata.ep_azimuth

        tl = radius * math.tan( ia / 2)
        bc = ip.moved(bp_azimuth + math.pi, tl)
        ec = ip.moved(ep_azimuth, tl)

        if direction == CurveDirection.LEFT:
            cc = bc.moved(bp_azimuth + math.pi / 2, radius)
        else:
            cc = bc.moved(bp_azimuth - math.pi / 2, radius)

        curve_geomtry = CurveGeometry(
            radius=radius,
            direction=direction,
            start_angle=bp_azimuth,
            end_angle=ep_azimuth,
            center=cc,
        )
        return curve_geomtry