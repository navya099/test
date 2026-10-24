# tests/test_ga.py
import unittest

import numpy as np
from shapely import LineString

from ga.ga import GeneticAlgorithm
from core.evaluate import HARD_PENALTY

import logging
logging.basicConfig(level=logging.WARNING)


class TestGeneticAlgorithm(unittest.TestCase):
    # WGS84 (lat, lon) — 서울시청 → 수서역
    START = (37.5665, 126.9780)
    END = (37.4870, 127.1000)

    def test_seed_reproducibility(self):
        """같은 seed → 같은 population."""
        ga1 = GeneticAlgorithm(self.START, self.END,
                               n_candidates=5, n_generations=2, chain=40)
        pop1 = ga1.evolve(seed=42)

        ga2 = GeneticAlgorithm(self.START, self.END,
                               n_candidates=5, n_generations=2, chain=40)
        pop2 = ga2.evolve(seed=42)

        self.assertEqual(len(pop1), len(pop2))
        f1 = [c["fitness"] for c in pop1]
        f2 = [c["fitness"] for c in pop2]
        np.testing.assert_allclose(f1, f2, rtol=1e-9)

    def test_population_size_maintained(self):
        import logging
        logging.basicConfig(level=logging.WARNING)

        ga = GeneticAlgorithm(self.START, self.END,
                              n_candidates=3, n_generations=1, chain=40)

        # 초기화 + 평가
        ga.initialize_population()
        for c in ga.population:
            ga.evaluate_candidate(c)
            print(f"init: fitness={c['fitness']:.2f}, "
                  f"constraints_ok={c.get('constraints_ok')}, "
                  f"converged={c.get('converged')}")

        pop = ga.evolve(seed=1)
        self.assertEqual(len(pop), 3)

    def test_mutation_keeps_endpoints(self):
        import random
        random.seed(0)  # ← 시드 리셋

        ga = GeneticAlgorithm(self.START, self.END, mutation_rate=1.0)
        ls = LineString([(0, 0), (100, 50), (200, 0)])
        mutated = ga.mutate_ip_list(ls)
        coords = list(mutated.coords)
        self.assertEqual(coords[0], (0, 0))
        self.assertEqual(coords[-1], (200, 0))
        self.assertNotEqual(coords[1], (100, 50))

    def test_selection_handles_hard_penalty(self):
        """전부 하드 페널티여도 selection 이 실패하지 않음."""
        ga = GeneticAlgorithm(self.START, self.END,
                              n_candidates=4, n_generations=1, chain=40)
        ga.initialize_population()
        for c in ga.population:
            c["fitness"] = HARD_PENALTY
        elites, parents = ga.selection()
        self.assertGreaterEqual(len(elites), 2)
        self.assertGreaterEqual(len(parents), 2)

    def test_no_all_hard_penalty_after_init(self):
        """초기화 후 모든 후보가 하드 페널티인 경우 없음 (경고 로그 확인)."""
        ga = GeneticAlgorithm(self.START, self.END,
                              n_candidates=3, n_generations=0, chain=40)
        ga.initialize_population()
        for c in ga.population:
            ga.evaluate_candidate(c)
        n_valid = sum(1 for c in ga.population if c["fitness"] > HARD_PENALTY / 2)
        self.assertGreater(n_valid, 0, "초기 후보 중 유효한 것이 있어야 함")


if __name__ == "__main__":
    unittest.main()