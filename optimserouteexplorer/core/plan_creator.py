from copy import deepcopy

from coordinate_utils import convert_coordinates
from core.curveadjuster import CurveAdjuster
from core.linestringprocessor import LineStringProcessor
from core.randomlinestringcreator import RandomLineStringCreator
from shapely import Point

from core.util import adjust_radius_by_angle


class PlanCreator:
    """평면 선형 생성 담당"""
    def __init__(self, start, end, chain):
        self.start = start
        self.end = end
        self.chain = chain

    def generate(self):
        """
        평면 선형 제작 통합 메소드
        Returns:
            dict
        """
        ip_linestring, angles = self.generate_ip_linestring(self.start, self.end)
        radius_list = self.calculate_radius_list(angles)
        plan = self.reconstruct_full_plan(ip_linestring, angles, radius_list, self.chain)
        return {
            "ip_list": ip_linestring,
            "angles": angles,
            "radius_list": radius_list,
            **plan
        }

    ###################################################################
    # GA용 메소드 분리
    ###################################################################
    def generate_ip_linestring(self, start, end):
        """
        랜덤 IP(LineString) 생성 + 각도 계산
        Returns:
            ip_linestring: 원본 IP(LineString, deepcopy)
            angles: 곡선 각도 리스트
        """
        start_tm = convert_coordinates((start[1], start[0]), 4326, 5186)
        end_tm = convert_coordinates((end[1], end[0]), 4326, 5186)

        rlc = RandomLineStringCreator()

        rlc.generate_random_linestring(Point(start_tm), Point(end_tm))
        linestring = rlc.linestring

        lsp = LineStringProcessor(linestring)
        lsp.process_linestring()
        ip_linestring = deepcopy(lsp.linestring)
        angles = lsp.angles
        return ip_linestring, angles

    def calculate_radius_list(self, angles, min_radius=3100, max_radius=20000):
        """
        각도 리스트로 radius 리스트 생성
        Args:
            angles: 각도 리스트(도)
            min_radius: 최소곡선반경
            max_radius: 최대곡선반경

        Returns:
            list
        """
        return [adjust_radius_by_angle(angle, min_radius, max_radius) for angle in angles]

    def reconstruct_full_plan(self, ip_linestring, angles, radius_list, chain):
        """
        IP 좌표 + 각도 + 반경 → 전체 LineString 생성 (곡선 포함)
        Returns:
            dict: linestring, tmcoords, wgs_coords, station_list
        """
        lsp = LineStringProcessor(ip_linestring)
        curves = []
        # 곡선 보정
        ca = CurveAdjuster(ip_linestring, angles, radius_list)
        ca.main_loop()
        curves = ca.segments

        start_points = [c.bc_coord for c in curves]
        end_points = [c.ec_coord for c in curves]
        center_points = [c.center_coord for c in curves]
        direction_list = [c.direction for c in curves]

        lsp.create_joined_line_and_arc_linestirng(
            start_points=start_points,
            end_points=end_points,
            center_points=center_points,
            direction_list=direction_list
        )
        lsp.resample_linestring(chain)
        linestring = lsp.linestring
        tmcoords = list(linestring.coords)
        wgs_coords = convert_coordinates(tmcoords, 5186, 4326)
        station_list = lsp.stations

        return {
            "linestring": linestring,
            "tmcoords": tmcoords,
            "wgs_coords": wgs_coords,
            "station_list": station_list
        }
