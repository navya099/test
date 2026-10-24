# core/generate_routes.py
import logging

from core.profilecreator import ProfileCreator
from xref.srtm30 import SrtmDEM30

logger = logging.getLogger(__name__)


class GenerateRoutes:
    """GA 후보의 종단 생성 담당."""

    def generate_profile_candidate(self, coords, chain, station_list):
        if not station_list:
            raise ValueError("station_list is empty")

        dem = SrtmDEM30(coords)
        ground_elevs = dem.get_elevations()

        gl = [(sta, ele) for sta, ele in zip(station_list, ground_elevs)]
        min_distance = 1000
        max_vip = max(1, int(gl[-1][0] / min_distance))

        pc = ProfileCreator(gl, min_cover=5.0, max_grade=0.035)
        constraints_ok = pc.generate_longitudinal(
            num_points=max_vip, min_distance=min_distance, chain=chain
        )

        return {
            "ground_elevs": ground_elevs,
            "design_elevs": pc.els,
            "fg_profile": pc.profile,
            "slopes": pc.slopes,
            "eg_profile": pc.gl,
            "constraints_ok": constraints_ok,
            "min_cover_violation": pc.min_cover_violation,
        }