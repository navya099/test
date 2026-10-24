# core/evaluate.py
import logging
import math

import numpy as np

from core.construction_cost_calculator import ConstructionCostCalculator
from core.structure_generator import StructureGenerator

logger = logging.getLogger(__name__)

HARD_PENALTY = -1e6


class Evaluator:
    def __init__(self, min_radius=600, max_grade=0.035,
                 quality_weight=0.7, cost_weight=0.3,
                 cost_log_scale=10.0):
        self.min_radius = min_radius
        self.max_grade = max_grade
        self.quality_weight = quality_weight
        self.cost_weight = cost_weight
        self.cost_log_scale = cost_log_scale

    def evaluate(self, plan: dict, profile: dict, chain: float) -> dict:
        constraints_ok = profile.get("constraints_ok", True)
        plan_violation = self._check_plan_violation(plan)
        profile_violation = self._check_profile_violation(profile)

        if not constraints_ok or plan_violation or profile_violation:
            return {
                "bridges": [], "tunnels": [],
                "total_bridge_length": 0.0,
                "total_tunnel_length": 0.0,
                "total_earth_length": 0.0,
                "total_cost": None,
                "total_score": HARD_PENALTY,
                "total_fitness": HARD_PENALTY,
                "structure_collection": None,
                "constraints_ok": False,
            }

        elevs = np.asarray(profile["design_elevs"], dtype=float)
        ground = np.asarray(profile["ground_elevs"], dtype=float)
        dz = elevs - ground

        generator = StructureGenerator()
        generator.define_structure(plan["station_list"], dz)
        collection = generator.structures
        bridges = collection.get_by_type("교량")
        tunnels = collection.get_by_type("터널")

        linestring = plan["linestring"]
        total_km = linestring.length * 0.001
        total_bridge_length = sum(b.endsta - b.startsta for b in bridges) * 0.001
        total_tunnel_length = sum(t.endsta - t.startsta for t in tunnels) * 0.001
        total_earth_length = max(total_km - total_bridge_length - total_tunnel_length, 0.0)

        costcal = ConstructionCostCalculator()
        total_cost = costcal.calculate_total(
            total_earth_length, total_bridge_length, total_tunnel_length, total_km
        )

        score = self._evaluate_alignment(plan, profile)

        # min_cover 위반 소프트 감점
        min_cover_violation = profile.get("min_cover_violation", 0.0)
        if min_cover_violation > 0:
            penalty_factor = max(0.0, 1.0 - min_cover_violation / 200.0)
            score *= penalty_factor

        fitness = self._evaluate_total_fitness(score, total_cost)

        return {
            "bridges": bridges, "tunnels": tunnels,
            "total_bridge_length": total_bridge_length,
            "total_tunnel_length": total_tunnel_length,
            "total_earth_length": total_earth_length,
            "total_cost": total_cost,
            "total_score": score,
            "total_fitness": fitness,
            "structure_collection": collection,
            "constraints_ok": True,
        }

    def _check_plan_violation(self, plan: dict) -> bool:
        if not plan.get("converged", True):
            return True
        radius_list = plan.get("radius_list", [])
        if not radius_list:
            return True
        return min(radius_list) < self.min_radius

    def _check_profile_violation(self, profile: dict) -> bool:
        grades = profile.get("slopes", [])
        if not grades:
            return True
        tol = 1e-6
        return max(abs(g) for g in grades) > self.max_grade + tol

    def _evaluate_alignment(self, plan, profile) -> float:
        return 0.4 * self._evaluate_plan(plan) + 0.6 * self._evaluate_profile(profile)

    def _evaluate_plan(self, plan) -> float:
        radius_list = plan.get("radius_list", [])
        if not radius_list:
            return 0.0
        min_r = min(radius_list)
        if min_r < self.min_radius:
            return 0.0
        ratio = min_r / self.min_radius
        if ratio >= 1.5:
            return 100.0
        return 70.0 + 30.0 * (ratio - 1.0) / 0.5

    def _evaluate_profile(self, profile) -> float:
        grades = profile.get("slopes", [])
        if not grades:
            return 0.0
        max_g = max(abs(g) for g in grades)
        if max_g > self.max_grade:
            return 0.0
        ratio = max_g / self.max_grade
        if ratio <= 0.8:
            return 100.0
        return 100.0 - 40.0 * (ratio - 0.8) / 0.2

    def _evaluate_total_fitness(self, score, cost) -> float:
        if score <= 0:
            return HARD_PENALTY
        if cost is None or cost <= 0:
            return float(score)
        score_norm = score / 100.0
        cost_norm = min(math.log10(cost + 1.0) / self.cost_log_scale, 1.0)
        fitness = (
            self.quality_weight * score_norm
            + self.cost_weight * (1.0 - cost_norm)
        )
        return float(fitness * 100.0)