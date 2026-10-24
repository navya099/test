# core/evaluate.py
"""
노선 평가: 평면/종단 품질 점수 + 공사비 → fitness.

설계 원칙:
- 제약 위반(최소곡선반경, 최대경사, constraints_ok)은 하드 페널티(-1e6)
- score 와 cost 를 독립 스케일로 가중합 (기본 0.7/0.3)
- Evaluator 는 상태 없는 순수 평가 (병렬/웹 비동기 안전)
"""
import logging
import math

import numpy as np

from core.construction_cost_calculator import ConstructionCostCalculator
from core.structure_generator import StructureGenerator

logger = logging.getLogger(__name__)

HARD_PENALTY = -1e6


class Evaluator:
    """노선의 평면/종단 선형 및 공사비를 종합 평가."""

    def __init__(self, min_radius=600, max_grade=0.025,
                 quality_weight=0.7, cost_weight=0.3,
                 cost_log_scale=10.0):
        """
        Args:
            min_radius: 최소 곡선반경 (m)
            max_grade: 최대 종단경사 (비율, 0.025 = 2.5%)
            quality_weight: 품질 점수 가중치 (0~1)
            cost_weight: 비용 점수 가중치 (0~1). quality + cost = 1 권장
            cost_log_scale: cost 정규화 log 스케일 (cost 10^N → 1.0)
        """
        self.min_radius = min_radius
        self.max_grade = max_grade
        self.quality_weight = quality_weight
        self.cost_weight = cost_weight
        self.cost_log_scale = cost_log_scale

    # ------------------------------------------------------------------
    def evaluate(self, plan: dict, profile: dict, chain: float) -> dict:
        """
        Returns:
            dict: bridges, tunnels, total_*_length, total_cost,
                  total_score, total_fitness, structure_collection, constraints_ok
        """
        # --- 1. 제약 위반 선검사 (하드 페널티) ---
        constraints_ok = profile.get("constraints_ok", True)
        plan_violation = self._check_plan_violation(plan)
        profile_violation = self._check_profile_violation(profile)

        if not constraints_ok or plan_violation or profile_violation:
            # 위반 후보: 구조물/비용 계산 생략 (성능 + 안전)
            return {
                "bridges": [],
                "tunnels": [],
                "total_bridge_length": 0.0,
                "total_tunnel_length": 0.0,
                "total_earth_length": 0.0,
                "total_cost": None,
                "total_score": HARD_PENALTY,
                "total_fitness": HARD_PENALTY,
                "structure_collection": None,
                "constraints_ok": False,
            }

        # --- 2. 교량/터널 판정 ---
        elevs = np.asarray(profile["design_elevs"], dtype=float)
        ground = np.asarray(profile["ground_elevs"], dtype=float)
        dz = elevs - ground

        generator = StructureGenerator()
        generator.define_structure(plan["station_list"], dz)
        collection = generator.structures
        bridges = collection.get_by_type("교량")
        tunnels = collection.get_by_type("터널")

        # --- 3. 구간별 총 길이 ---
        linestring = plan["linestring"]
        total_km = linestring.length * 0.001
        total_bridge_length = sum(b.endsta - b.startsta for b in bridges) * 0.001
        total_tunnel_length = sum(t.endsta - t.startsta for t in tunnels) * 0.001
        total_earth_length = max(
            total_km - total_bridge_length - total_tunnel_length, 0.0
        )

        # --- 4. 공사비 ---
        costcal = ConstructionCostCalculator()
        total_cost = costcal.calculate_total(
            total_earth_length, total_bridge_length, total_tunnel_length, total_km
        )

        # --- 5. 점수 ---
        score = self._evaluate_alignment(plan, profile)

        # --- 6. 적합도 ---
        fitness = self._evaluate_total_fitness(score, total_cost)

        return {
            "bridges": bridges,
            "tunnels": tunnels,
            "total_bridge_length": total_bridge_length,
            "total_tunnel_length": total_tunnel_length,
            "total_earth_length": total_earth_length,
            "total_cost": total_cost,
            "total_score": score,
            "total_fitness": fitness,
            "structure_collection": collection,
            "constraints_ok": True,
        }

    # ------------------------------------------------------------------
    # 제약 검사
    # ------------------------------------------------------------------
    def _check_plan_violation(self, plan: dict) -> bool:
        radius_list = plan.get("radius_list", [])
        if not radius_list:
            return True   # 반경 정보 없음 → 위반
        return min(radius_list) < self.min_radius

    def _check_profile_violation(self, profile: dict) -> bool:
        grades = profile.get("slopes", [])
        if not grades:
            return True
        return max(abs(g) for g in grades) > self.max_grade

    # ------------------------------------------------------------------
    # 점수 (연속 함수)
    # ------------------------------------------------------------------
    def _evaluate_alignment(self, plan: dict, profile: dict) -> float:
        plan_score = self._evaluate_plan(plan)
        profile_score = self._evaluate_profile(profile)
        return 0.4 * plan_score + 0.6 * profile_score

    def _evaluate_plan(self, plan: dict) -> float:
        """평면 곡선반경 점수 (0~100, 연속)."""
        radius_list = plan.get("radius_list", [])
        if not radius_list:
            return 0.0
        min_r = min(radius_list)
        if min_r < self.min_radius:
            return 0.0
        # min_radius 이상: 1.0~1.5 배 구간에서 70→100, 그 이상 100
        ratio = min_r / self.min_radius
        if ratio >= 1.5:
            return 100.0
        return 70.0 + 30.0 * (ratio - 1.0) / 0.5

    def _evaluate_profile(self, profile: dict) -> float:
        """종단 경사 점수 (0~100, 연속)."""
        grades = profile.get("slopes", [])
        if not grades:
            return 0.0
        max_g = max(abs(g) for g in grades)
        if max_g > self.max_grade:
            return 0.0
        # max_grade 의 0.8~1.0 구간에서 60→100
        ratio = max_g / self.max_grade
        if ratio <= 0.8:
            return 100.0
        return 100.0 - 40.0 * (ratio - 0.8) / 0.2

    # ------------------------------------------------------------------
    # 종합 적합도
    # ------------------------------------------------------------------
    def _evaluate_total_fitness(self, score: float, cost: float | None) -> float:
        """
        fitness = quality_weight * score_norm + cost_weight * (1 - cost_norm)
        - score_norm: score / 100 (0~1)
        - cost_norm : log10(cost+1) / cost_log_scale (0~1 근사)
        """
        if score <= 0:
            return HARD_PENALTY
        if cost is None or cost <= 0:
            return float(score)   # 비용 미산정 시 score 그대로

        score_norm = score / 100.0
        cost_norm = min(math.log10(cost + 1.0) / self.cost_log_scale, 1.0)

        fitness = (
            self.quality_weight * score_norm
            + self.cost_weight * (1.0 - cost_norm)
        )
        return float(fitness * 100.0)