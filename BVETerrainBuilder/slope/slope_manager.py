import numpy as np

from slope.slope_creator import SlopeBuilder
from srtm30 import SrtmDEM30


class SlopeManager:
    """슬로프 빌더"""
    def __init__(self, dem: SrtmDEM30):
        self.dem = dem
        self.slope_builder = None
    def build_slopes(self, track_mesh, slope_ratio=1.5):
        # 좌측 사면
        self.slope_builder = SlopeBuilder(track_mesh)
        slope_left = self.slope_builder.add_slope(track_mesh, self.dem, slope_ratio, side="left")

        # 우측 사면
        slope_right = self.slope_builder.add_slope(track_mesh, self.dem, slope_ratio, side="right")

        return slope_left, slope_right

