import logging
import numpy as np
import meshio
from shapely.validation import explain_validity
from terrain.terrain_modifyer import TerrainModifier

class TerrainAssembler:
    """트랙과 사면을 조립해 최종 결과를 생성하는 클래스"""
    def __init__(self, dem_processor, slope_manager):
        self.dem_processor = dem_processor
        self.slope_manager = slope_manager

    def build(self, idx, slope_left_list, slope_right_list, terrain_mesh):
        """
        여러 토공 구간의 사면 리스트를 받아서
        각각 클리핑 후 최종 병합 결과를 반환
        """
        logging.debug(f"[Segment {idx}] TerrainAssembler 시작 (multi-section)")

        fixed_slopes_left = []
        fixed_slopes_right = []

        # 현재 지형을 누적 갱신
        current_terrain = terrain_mesh

        for section_idx, (slope_left, slope_right) in enumerate(zip(slope_left_list, slope_right_list), start=1):
            logging.debug(f"[Segment {idx}] Section {section_idx} 처리 시작")

            # 1. Daylight Points → Polygon 생성
            l_daylight, r_daylight = self.slope_manager.slope_builder.extract_daylight_points(slope_left, slope_right)
            clipping_poly = self.slope_manager.slope_builder.create_polygon(l_daylight, r_daylight)

            logging.debug(
                f"[Segment {idx}] Section {section_idx} polygon bounds: {clipping_poly.bounds}, area: {clipping_poly.area}")
            logging.debug(
                f"[Segment {idx}] Section {section_idx} polygon valid: {clipping_poly.is_valid}, validity: {explain_validity(clipping_poly)}")

            # 2. 현재 지형을 클리핑
            terrain_modifier = TerrainModifier(current_terrain)
            clipped_terrain = terrain_modifier.clip(clipping_poly)

            # 3. 사면 용접
            fixed_slope_l = terrain_modifier.weld(slope_left)
            fixed_slope_r = terrain_modifier.weld(slope_right)

            fixed_slopes_left.append(fixed_slope_l)
            fixed_slopes_right.append(fixed_slope_r)

            # 다음 섹션은 클리핑된 결과를 이어받음
            current_terrain = clipped_terrain

            logging.debug(f"[Segment {idx}] Section {section_idx} 완료")

        logging.debug(f"[Segment {idx}] TerrainAssembler 전체 클리핑 완료")

        logging.debug(f"[Segment {idx}] TerrainAssembler 전체 병합 완료")

        return clipped_terrain, fixed_slopes_left, fixed_slopes_right
