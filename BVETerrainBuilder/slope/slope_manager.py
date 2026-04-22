import numpy as np

from slope.slope_creator import SlopeBuilder
from srtm30 import SrtmDEM30


class SlopeManager:
    """슬로프 빌더"""
    def __init__(self, dem, terrain_mesh):
        self.dem = dem
        self.slope_builder = None
        self.terrain_mesh = terrain_mesh
    def build_slopes(self, track_edges, slope_ratio=1.5):
        #트랙 사이드
        left_side, right_side = track_edges
        #빌더 초기화
        self.slope_builder = SlopeBuilder(self.terrain_mesh)

        # 좌측 사면
        slope_left = self.slope_builder.add_slope(left_side, self.dem, slope_ratio, side="left")

        # 우측 사면
        slope_right = self.slope_builder.add_slope(right_side, self.dem, slope_ratio, side="right")

        return slope_left, slope_right

