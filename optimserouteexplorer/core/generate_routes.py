from core.evaluate import Evaluator
from core.plan_creator import PlanCreator
from core.profilecreator import ProfileCreator
from geometry.alignment import Alignment
from concurrent.futures import ProcessPoolExecutor
from srtm30 import SrtmDEM30

class GenerateRoutes:
    """
    노선후보 생성 클래스
    """
    def __init__(self):
        self.alignments = None

    # ========== 1단계: 평면 선형 생성 ==========
    def generate_plan_candidate(self, start, end, chain):
        """
        시작/끝점을 잇는 평면선형(LineString) + 곡선 반경 등 계산
        Returns:
            dict with keys: coords, radius_list, linestring
        """
        ac = PlanCreator(start, end, chain)
        al = ac.generate()
        return al

    # ========== 2단계: 종단 생성 ==========
    def generate_profile_candidate(self, coords, chain, station_list):
        """
        DEM 기반 종단고 생성 및 설계고 계산
        Returns:
            dict with keys: ground_elevs, design_elevs, profile, slopes
        """
        dem = SrtmDEM30(coords)
        ground_elevs = dem.get_elevations()

        gl = [(sta, ele) for sta, ele in zip(station_list, ground_elevs)]
        min_distance = 1000
        max_vip = int(gl[-1][0] / min_distance)

        pc = ProfileCreator(gl)
        pc.generate_longitudinal(num_points=max_vip, min_distance=min_distance, chain=chain)

        return {
            "ground_elevs": ground_elevs,
            "design_elevs": pc.els,
            "fg_profile": pc.profile,
            "slopes": pc.slopes,
            "eg_profile": pc.gl
        }

    # ========== 3단계: 평가 ==========
    def evaluate_alignment(self, plan, profile, chain):
        """
        노선 평가 (비용, 교량, 터널, 구배 등)
        """
        evaluator = Evaluator()
        evaluate_result = evaluator.evaluate(plan, profile, chain)
        return evaluate_result

    # ========== 통합 실행 ==========
    def generate_candidate(self, idx, start, end, chain):
        """
        한 개 후보노선 생성
        """
        """
        plan ={
            'linestring': linestring,
            'tmcoords': tmcoords,
            'wgs_coords': wgs_coords,
            'station_list': station_list,
            'radius_list': radius_list,
        }
        profile = {
            "ground_elevs": ground_elevs,
            "design_elevs": pc.els,
            "fg_profile": pc.profile,
            "slopes": pc.slopes,
            "eg_profile": pc.gl
        }
        result = {
            'bridges': bridges,
            'tunnels': tunnels,
            'total_bridge_length': total_bridge_length,
            'total_tunnel_length': total_tunnel_length,
            'total_earth_length': total_earth_length,
            'total_cost': total_cost,
            'total_score': score,
            'total_fitness': fitness,
        }
        """
        plan = self.generate_plan_candidate(start, end, chain)
        profile = self.generate_profile_candidate(plan['wgs_coords'], chain, plan['station_list'])
        evaluate_result = self.evaluate_alignment(
            plan, profile, chain
        )
        wgs_coords = plan['wgs_coords']
        wgs_coords = [[y, x] for x, y in wgs_coords]
        return Alignment(
            linestring=plan['linestring'],
            coords=wgs_coords,
            elevations=profile["fg_profile"],
            grounds=profile["eg_profile"],
            bridges=evaluate_result['bridges'],
            tunnels=evaluate_result['tunnels'],
            cost=evaluate_result['total_cost'],
            fls=profile["fg_profile"],
            grades=profile['slopes'],
            radius=plan['radius_list'],
            score=evaluate_result['total_score'],  # ✅ 점수 추가
            fitness=evaluate_result['total_fitness']  # ✅ 적합도 추가
        )

    def generate_and_rank_parallel(self, start, end, n_candidates=30, chain=40):
        alignments = []
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(self.generate_candidate, i, start, end, chain) for i in range(n_candidates)]
            for i, future in enumerate(futures):
                try:
                    alignments.append(future.result())
                except Exception as e:
                    print(f"[ERROR] Candidate {i} 실패: {e}")

        # fitness 또는 cost 기준 정렬
        alignments.sort(key=lambda x: getattr(x, "cost", 0))
        return alignments

    def generate_and_rank(self, start, end, n_candidates=30, chain=40, max_attempts=None):
        """
        여러 후보 노선을 생성하고, fitness/score가 0인 후보는 제외하여
        최종적으로 n_candidates개의 유효 후보만 반환.
        """

        if max_attempts is None:
            max_attempts = n_candidates * 5  # 안전한 상한 설정

        alignments = []
        attempts = 0

        while len(alignments) < n_candidates and attempts < max_attempts:
            attempts += 1
            try:
                candidate = self.generate_candidate(len(alignments), start, end, chain)

                # 유효성 체크: 점수와 적합도가 0이 아니어야 함
                if getattr(candidate, "score", 0) <= 0 or getattr(candidate, "fitness", 0) <= 0:
                    print(f"[SKIP] Candidate {attempts}: 점수 또는 fitness=0 → 폐기")
                    continue

                alignments.append(candidate)
                print(f"[OK] Candidate {len(alignments)}/{n_candidates} 생성 완료 (fitness={candidate.fitness:.3f})")

            except Exception as e:
                print(f"[ERROR] Candidate {attempts} 실패: {e}")
                continue

        if len(alignments) < n_candidates:
            print(f"[WARN] 유효 후보 부족: {len(alignments)}/{n_candidates}개만 생성됨")

        # 적합도 내림차순 정렬 (높을수록 우수)
        alignments.sort(key=lambda x: x.fitness, reverse=True)

        print(f"\n=== 후보 노선 생성 완료 ===")
        print(f"총 시도: {attempts}회")
        print(f"유효 후보: {len(alignments)}개 / 목표: {n_candidates}개")

        return alignments


