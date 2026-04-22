import logging

from terrain import terrain_builder
from terrain.terrain_modifyer import TerrainModifier


class TerrainAssembler:
    """트랙과 사면을 조립해 최종 결과를 생성하는 클래스"""
    def __init__(self, dem_processor, slope_manger):
        self.dem_processor = dem_processor
        self.slope_manager = slope_manger

    def build(self, idx, slope_left, slope_right, terrain_mesh):
        """트랙과 사면을 조립해 지형 클리핑 및 최종 결과 생성"""
        logging.debug(f"[Segment {idx}] TerrainAssembler 시작")

        # 1. Daylight Points → Polygon 생성
        l_daylight, r_daylight = self.slope_manager.slope_builder.extract_daylight_points(slope_left, slope_right)
        logging.debug(f"[Segment {idx}] Left daylight pts: {len(l_daylight)}, Right daylight pts: {len(r_daylight)}")

        clipping_poly = self.slope_manager.slope_builder.create_polygon(l_daylight, r_daylight)
        logging.debug(f"[Segment {idx}] Clipping polygon bounds: {clipping_poly.bounds}, area: {clipping_poly.area}")

        # 2. 지형 클리핑 및 용접
        terrain_modifyer = TerrainModifier(terrain_mesh)
        clipped_terrain = terrain_modifyer.clip(clipping_poly)
        logging.debug(f"[Segment {idx}] Clipped terrain points: {len(clipped_terrain.points)}, faces: {len(clipped_terrain.cells[0].data)}")

        fixed_slope_l = terrain_modifyer.weld(slope_left)
        logging.debug(f"[Segment {idx}] Welded slope left points: {len(fixed_slope_l.points)}, faces: {len(fixed_slope_l.cells[0].data)}")

        fixed_slope_r = terrain_modifyer.weld(slope_right)
        logging.debug(f"[Segment {idx}] Welded slope right points: {len(fixed_slope_r.points)}, faces: {len(fixed_slope_r.cells[0].data)}")

        logging.debug(f"[Segment {idx}] TerrainAssembler 완료")

        return clipped_terrain, fixed_slope_l, fixed_slope_r
