# core/generate_routes.py
"""
GA 후보 생성에 필요한 종단(profile) 생성만 담당.

레거시 제거 (GA 도입 전 파이프라인):
- generate_and_rank / generate_and_rank_parallel
- generate_plan_candidate (GA 는 PlanCreator 직접 사용)
- generate_candidate / evaluate_alignment
- Alignment 반환 (GA 는 dict 사용)
  ※ geometry/alignment.py 는 추후 리팩토링용으로 보존 (현재 미사용)
"""
import logging

from core.profilecreator import ProfileCreator
from xref.srtm30 import SrtmDEM30

logger = logging.getLogger(__name__)


class GenerateRoutes:
    """GA 후보의 종단 생성 담당."""

    def generate_profile_candidate(self, coords, chain, station_list):
        """
        DEM 기반 종단고 생성 및 설계고 계산.

        Args:
            coords: WGS84 좌표 리스트 (경도, 위도) — SrtmDEM30 입력
            chain: 종단 샘플링 간격 (m)
            station_list: 누적 거리 리스트 (m)

        Returns:
            dict: ground_elevs, design_elevs, fg_profile, slopes, eg_profile
        """
        if not station_list:
            raise ValueError("station_list is empty")

        dem = SrtmDEM30(coords)
        ground_elevs = dem.get_elevations()

        gl = [(sta, ele) for sta, ele in zip(station_list, ground_elevs)]
        min_distance = 1000
        max_vip = max(1, int(gl[-1][0] / min_distance))

        pc = ProfileCreator(gl)
        pc.generate_longitudinal(
            num_points=max_vip, min_distance=min_distance, chain=chain
        )

        return {
            "ground_elevs": ground_elevs,
            "design_elevs": pc.els,
            "fg_profile": pc.profile,
            "slopes": pc.slopes,
            "eg_profile": pc.gl,
        }