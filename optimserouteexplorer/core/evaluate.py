import numpy as np
import math
from core.construction_cost_calculator import ConstructionCostCalculator
from core.structure_detector import StructureDetector
from core.structure_generator import StructureGenerator
from math_utils import calculate_distance


class Evaluator:
    """
    노선의 평면/종단 선형 및 공사비를 종합 평가하는 클래스
    """
    def __init__(self, min_radius=600, max_grade=0.025):
        self.cost = 0.0
        self.score = 0.0
        self.fitness = 0.0
        self.min_radius = min_radius  # 최소 곡선반경 (m)
        self.max_grade = max_grade    # 최대 종단기울기 (‰)

    def evaluate(self, plan: dict, profile: dict, chain: float):
        """
        종단 선형 평가 및 교량/터널/토공 구간 판정 + 공사비 산정
        """
        # --- 1. 절성고(dz) 계산 ---
        elevs = np.array(profile["design_elevs"])
        ground = np.array(profile["ground_elevs"])
        dz = elevs - ground

        # --- 2. 구간거리(ds) 계산 ---
        linestring = plan["linestring"]
        coords = list(linestring.coords)


        # --- 3. 교량/터널 판정 ---
        generator = StructureGenerator()
        generator.define_structure(plan['station_list'],dz)
        colletion = generator.structures
        bridges = colletion.get_by_type('교량')
        tunnels = colletion.get_by_type('터널')

        # --- 4. 구간별 총 길이 ---
        total_km = linestring.length * 0.001
        total_bridge_length = sum(b.endsta - b.startsta for b in bridges) * 0.001
        total_tunnel_length = sum(t.endsta - t.startsta for t in tunnels) * 0.001
        total_earth_length = max(total_km - total_bridge_length - total_tunnel_length, 0)

        # --- 5. 공사비 계산 ---
        costcal = ConstructionCostCalculator()
        total_cost = costcal.calculate_total(
            total_earth_length, total_bridge_length, total_tunnel_length, total_km
        )

        # --- 6. 점수 계산 ---
        score = self._evaluate_alignment(plan, profile)
        self.cost = total_cost
        self.score = score

        # --- 7. 적합도 계산 ---
        fitness = self._evaluate_total_fitness(score, total_cost)

        return {
            'bridges': bridges,
            'tunnels': tunnels,
            'total_bridge_length': total_bridge_length,
            'total_tunnel_length': total_tunnel_length,
            'total_earth_length': total_earth_length,
            'total_cost': total_cost,
            'total_score': score,
            'total_fitness': fitness,
            "structure_collection": colletion,
        }


    # =========================================================
    # 내부 메소드: 점수 계산
    # =========================================================
    def _evaluate_alignment(self, plan: dict, profile: dict) -> float:
        """
        평면/종단 기준 점수를 종합 계산
        """
        plan_score = self._evaluate_plan(plan)
        profile_score = self._evaluate_profile(profile)
        return 0.4 * plan_score + 0.6 * profile_score  # 가중합

    def _evaluate_plan(self, plan: dict) -> float:
        """평면 곡선반경 기반 점수"""
        radius_list = plan.get("radius_list", [])
        if not radius_list:
            return 0

        min_r = min(radius_list)
        if min_r < self.min_radius:
            return 30
        elif min_r < self.min_radius * 1.2:
            return 70
        return 100

    def _evaluate_profile(self, profile: dict) -> float:
        """종단 기울기 기반 점수"""
        grades = profile.get("slopes", [])
        if not grades:
            return 0

        max_g = max(abs(g) for g in grades)
        if max_g > self.max_grade:
            return 0
        elif max_g > self.max_grade * 0.8:
            return 60
        return 100

        # =========================================================
        # 내부 메소드: 종합 적합도 계산
        # =========================================================

    def _evaluate_total_fitness(self, score: float, cost: float) -> float:
        """
        종합 적합도 계산 (비용 단위: 백만원)
        점수가 높고 비용이 낮을수록 좋음.
        """
        if cost is None or cost <= 0:
            return float(score)

        # 1️⃣ 비용 로그 스케일로 완화

        denom = 1.0 + math.log10(cost + 1.0)

        # 2️⃣ 점수 정규화 (0~100 → 0~1)
        score_norm = score / 100.0

        # 3️⃣ 적합도 계산 (100 스케일 확대)
        fitness = (score_norm / denom) * 100.0

        # 4️⃣ 안정적 상한 (선택)
        # fitness = min(fitness, 10000)

        return float(fitness)
