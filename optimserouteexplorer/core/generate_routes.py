from copy import deepcopy

from coordinate_utils import convert_coordinates
from core.curveadjuster import CurveAdjuster
from core.evaluate import Evaluator
from core.linestringprocessor import LineStringProcessor
from core.profilecreator import ProfileCreator
from core.randomlinestringcreator import RandomLineStringCreator
from core.util import adjust_radius_by_angle, haversine
from shapely.geometry import Point
from geometry.alignment import Alignment
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
from asyncio import as_completed
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
        # WGS84 → TM 변환
        start_tm = convert_coordinates((start[1], start[0]), 4326, 5186)
        end_tm = convert_coordinates((end[1], end[0]), 4326, 5186)

        # 랜덤 라인 생성
        rlc = RandomLineStringCreator()
        rlc.generate_random_linestring(Point(start_tm), Point(end_tm))
        linestring = rlc.linestring

        # 선형 처리 및 각도 계산
        lsp = LineStringProcessor(linestring)
        lsp.process_linestring()
        angles = lsp.angles
        ip_linestring = deepcopy(lsp.linestring)

        # 곡선 반경 생성
        radius_list = [adjust_radius_by_angle(angle, 3100, 20000) for angle in angles]

        # 곡선 보정
        ca = CurveAdjuster(lsp.linestring, angles, radius_list)
        ca.main_loop()
        curves = ca.segments

        start_points = [c.bc_coord for c in curves]
        end_points = [c.ec_coord for c in curves]
        center_points = [c.center_coord for c in curves]
        direction_list = [c.direction for c in curves]

        # 곡선 포함하여 연결
        lsp.create_joined_line_and_arc_linestirng(
            start_points=start_points,
            end_points=end_points,
            center_points=center_points,
            direction_list=direction_list
        )
        lsp.resample_linestring(chain)
        linestring = lsp.linestring
        # TM → WGS84
        tmcoords = list(linestring.coords)
        wgs_coords = convert_coordinates(tmcoords, 5186, 4326)

        station_list = lsp.stations
        return {
            'ip_list': ip_linestring,
            'ia_list': angles,
            'linestring': linestring,
            'tmcoords': tmcoords,
            'wgs_coords': wgs_coords,
            'station_list': station_list,
            'radius_list': radius_list,
        }

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

    ###################################################################
    #GA용 메소드 분리
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
