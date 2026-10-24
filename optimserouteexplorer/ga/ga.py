# ga/ga.py
"""
유전 알고리즘 (IP 좌표 탐색).

설계 원칙:
- 재현성: evolve(seed=...) 로 random 전역 시드 고정
- 세대 간 인구 수 유지 (n_candidates)
- 하드 페널티(HARD_PENALTY) 후보는 elite/부모 선택에서 배제
- IP 좌표의 시작/끝점은 mutation 에서 고정
- 무거운 평가 결과(plan_full/profile/result)는 개체에 저장하되,
  elite deepcopy 시 필요한 필드만 복사
"""
import logging
import random
from copy import deepcopy

import numpy as np
from shapely import LineString

from core.evaluate import HARD_PENALTY, Evaluator
from core.generate_routes import GenerateRoutes
from core.linestringprocessor import LineStringProcessor
from core.plan_creator import PlanCreator

logger = logging.getLogger(__name__)


class GeneticAlgorithm:
    def __init__(self, start, end, n_candidates=30, n_generations=20, chain=40,
                 elite_ratio=0.2, mutation_rate=0.1):
        self.start = start
        self.end = end
        self.n_candidates = n_candidates
        self.n_generations = n_generations
        self.chain = chain
        self.elite_ratio = elite_ratio
        self.mutation_rate = mutation_rate

        self.gr = GenerateRoutes()
        self.evl = Evaluator()
        self.ac = PlanCreator(self.start, self.end, self.chain)
        self.population = []

    # ------------------------------------------------------------------
    # 1. 초기 후보 생성
    # ------------------------------------------------------------------
    def initialize_population(self):
        self.population = []
        for _ in range(self.n_candidates):
            plan, ia = self.ac.generate_ip_linestring(self.start, self.end)
            self.population.append({
                "plan": plan,
                "ia": ia,
                "fitness": None,
                "cost": None,
                "score": None,
            })

    # ------------------------------------------------------------------
    # 2. 후보 평가
    # ------------------------------------------------------------------
    def evaluate_candidate(self, candidate):
        """
        후보를 평가하고 개체에 결과를 반영.
        radius_list 는 여기서 1회만 계산.
        constraints_ok=False / 제약 위반 시 evaluate 가 HARD_PENALTY 반환.
        """
        radius_list = self.ac.calculate_radius_list(candidate["ia"])
        plan_full = self.ac.reconstruct_full_plan(
            candidate["plan"], candidate["ia"], radius_list, self.chain
        )
        profile = self.gr.generate_profile_candidate(
            plan_full["wgs_coords"], self.chain, plan_full["station_list"]
        )
        result = self.evl.evaluate(plan_full, profile, self.chain)

        candidate.update({
            "cost": result["total_cost"],
            "score": result["total_score"],
            "fitness": result["total_fitness"],
            "plan_full": plan_full,
            "profile": profile,
            "result": result,
            "radius_list": radius_list,
            "constraints_ok": result.get("constraints_ok", True),
        })
        return plan_full, profile, result

    # ------------------------------------------------------------------
    # 3. 선택
    # ------------------------------------------------------------------
    def selection(self):
        """
        elite: fitness 상위 (HARD_PENALTY 후보 제외)
        parents: 유효 후보에서 random.choices (크기 = 현재 인구수)
        """
        evaluated = [c for c in self.population if c.get("fitness") is not None]
        if not evaluated:
            raise RuntimeError("selection 전에 평가된 개체가 없습니다")

        sorted_pop = sorted(evaluated, key=lambda x: x["fitness"], reverse=True)

        # 하드 페널티 후보 배제
        valid = [c for c in sorted_pop if c["fitness"] > HARD_PENALTY / 2]
        if not valid:
            # 전멸 시: 그래도 상위 일부로 진행 (진화 지속)
            valid = sorted_pop[:max(2, len(sorted_pop) // 10)]
            logger.warning(
                "유효 후보 없음 — 상위 %d개로 진행", len(valid)
            )

        n_elite = max(2, int(self.elite_ratio * len(valid)))
        elites = [self._clone_elite(c) for c in valid[:n_elite]]
        parents = random.choices(valid, k=max(2, len(self.population)))
        return elites, parents

    def _clone_elite(self, candidate: dict) -> dict:
        """
        elite 는 다음 세대에 그대로 평가 결과를 유지해야 하므로 deepcopy.
        단, plan_full/profile/result 는 재사용 가능하므로 얕게 공유.
        """
        return {
            "plan": deepcopy(candidate["plan"]),
            "ia": list(candidate["ia"]),
            "radius_list": list(candidate.get("radius_list", [])),
            "fitness": candidate["fitness"],
            "cost": candidate.get("cost"),
            "score": candidate.get("score"),
            "constraints_ok": candidate.get("constraints_ok", True),
            # 평가 산출물은 공유 (재평가 방지)
            "plan_full": candidate.get("plan_full"),
            "profile": candidate.get("profile"),
            "result": candidate.get("result"),
        }

    # ------------------------------------------------------------------
    # 4. 교배 + 돌연변이
    # ------------------------------------------------------------------
    def crossover_and_mutate(self, parents):
        children = []
        for i in range(0, len(parents) - 1, 2):
            p1, p2 = parents[i], parents[i + 1]

            child_ip = self.crossover_ip_list(p1["plan"], p2["plan"])
            child_ip = self.mutate_ip_list(child_ip)

            lsp = LineStringProcessor(child_ip)
            lsp.process_linestring()

            children.append({
                "plan": deepcopy(lsp.linestring),
                "ia": lsp.angles,
                "fitness": None,
                "cost": None,
                "score": None,
            })
        return children

    def crossover_ip_list(self, ip1: LineString, ip2: LineString) -> LineString:
        coords1 = list(ip1.coords)
        coords2 = list(ip2.coords)
        n = min(len(coords1), len(coords2))
        if n < 2:
            return LineString(coords1)
        cut = random.randint(1, n - 1)
        new_coords = coords1[:cut] + coords2[cut:]
        return LineString(new_coords)

    def mutate_ip_list(self, ip_linestring: LineString) -> LineString:
        """IP 중간 정점만 ±10m 이동. 시작/끝점은 고정."""
        coords = list(ip_linestring.coords)
        if len(coords) <= 2:
            return LineString(coords)
        mutated = [coords[0]]
        for x, y in coords[1:-1]:
            mutated.append((x + random.uniform(-10, 10),
                            y + random.uniform(-10, 10)))
        mutated.append(coords[-1])
        return LineString(mutated)

    # ------------------------------------------------------------------
    # 5. GA 루프
    # ------------------------------------------------------------------
    def evolve(self, seed: int | None = None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self.initialize_population()

        for gen in range(self.n_generations):
            logger.info("Generation %d/%d", gen + 1, self.n_generations)

            # 현재 세대 평가
            for cand in self.population:
                if cand.get("fitness") is None:
                    self.evaluate_candidate(cand)

            elites, parents = self.selection()
            children = self.crossover_and_mutate(parents)

            # 인구 수 유지: 부족하면 추가 교배
            next_pop = elites + children
            guard = 0
            while len(next_pop) < self.n_candidates and guard < 1000:
                guard += 1
                extra = random.choices(parents, k=2)
                next_pop.extend(self.crossover_and_mutate(extra))
            self.population = next_pop[:self.n_candidates]

        # 마지막 세대 평가
        for cand in self.population:
            if cand.get("fitness") is None:
                self.evaluate_candidate(cand)

        # 정렬 (하드 페널티 후보는 뒤로)
        self.population.sort(
            key=lambda x: x["fitness"] if x.get("fitness") is not None else HARD_PENALTY,
            reverse=True,
        )
        return self.population