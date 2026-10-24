import unittest
import numpy as np
from shapely import LineString

from ga.ga import GeneticAlgorithm
from core.evaluate import HARD_PENALTY


class TestGeneticAlgorithm(unittest.TestCase):
    def test_seed_reproducibility(self):
        """같은 seed → 같은 population."""
        # 서울 → 수서, WGS84 (lat, lon)
        start = (37.5665, 126.9780)  # 서울시청
        end = (37.4870, 127.1000)  # 수서역

        ga1 = GeneticAlgorithm(start, end, n_candidates=5, n_generations=2, chain=40)
        pop1 = ga1.evolve(seed=42)

        ga2 = GeneticAlgorithm(start, end, n_candidates=5, n_generations=2, chain=40)
        pop2 = ga2.evolve(seed=42)

        self.assertEqual(len(pop1), len(pop2))
        f1 = [c["fitness"] for c in pop1]
        f2 = [c["fitness"] for c in pop2]
        np.testing.assert_allclose(f1, f2, rtol=1e-9)

    def test_population_size_maintained(self):
        """세대 간 인구 수 유지."""
        # 서울 → 수서, WGS84 (lat, lon)
        start = (37.5665, 126.9780)  # 서울시청
        end = (37.4870, 127.1000)  # 수서역
        ga = GeneticAlgorithm(start, end, n_candidates=6, n_generations=2, chain=40)
        pop = ga.evolve(seed=1)
        self.assertEqual(len(pop), 6)

    def test_mutation_keeps_endpoints(self):
        """mutation 이 시작/끝점을 유지."""
        # 서울 → 수서, WGS84 (lat, lon)
        start = (37.5665, 126.9780)  # 서울시청
        end = (37.4870, 127.1000)  # 수서역
        ga = GeneticAlgorithm(start, end)

        ls = LineString([(0, 0), (100, 50), (200, 0)])
        mutated = ga.mutate_ip_list(ls)
        coords = list(mutated.coords)
        self.assertEqual(coords[0], (0, 0))
        self.assertEqual(coords[-1], (200, 0))
        # 중간점만 이동
        self.assertNotEqual(coords[1], (100, 50))

    def test_selection_handles_hard_penalty(self):
        """전부 하드 페널티여도 selection 이 실패하지 않음."""
        # 서울 → 수서, WGS84 (lat, lon)
        start = (37.5665, 126.9780)  # 서울시청
        end = (37.4870, 127.1000)  # 수서역
        ga = GeneticAlgorithm(start, end, n_candidates=4, n_generations=1, chain=40)
        ga.initialize_population()
        for c in ga.population:
            c["fitness"] = HARD_PENALTY
        elites, parents = ga.selection()
        self.assertGreaterEqual(len(elites), 2)
        self.assertGreaterEqual(len(parents), 2)
    def debug_tst(self):
        import logging
        logging.basicConfig(level=logging.DEBUG)

        from ga.ga import GeneticAlgorithm
        ga = GeneticAlgorithm((37.5665, 126.9780), (37.4870, 127.1000), n_candidates=3, n_generations=1)
        pop = ga.evolve(seed=1)

        for c in pop:
            print("fitness:", c["fitness"])
            print("constraints_ok:", c.get("constraints_ok"))
            print("radius_list:", c.get("radius_list"))
            print("slopes:", c.get("profile", {}).get("slopes"))
            print("---")

if __name__ == "__main__":
    unittest.main()
