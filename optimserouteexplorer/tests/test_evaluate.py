import unittest
from core.evaluate import Evaluator, HARD_PENALTY


class FakeStructureCollection:
    def get_by_type(self, t): return []
    def get_structure_type_at(self, sta): return None
    def find_containing(self, sta): return None


class FakeLineString:
    def __init__(self, length): self.length = length
    @property
    def coords(self): return [(0, 0), (self.length, 0)]


class FakeStructures:
    def __init__(self): pass


class TestEvaluator(unittest.TestCase):
    def _plan(self, radius_list, length=1000):
        return {
            "linestring": FakeLineString(length),
            "station_list": [0, 500, 1000],
            "radius_list": radius_list,
        }

    def _profile(self, slopes, constraints_ok=True):
        n = len(slopes) + 1
        return {
            "design_elevs": [10.0] * n,
            "ground_elevs": [5.0] * n,
            "slopes": slopes,
            "constraints_ok": constraints_ok,
        }

    def test_hard_penalty_on_radius_violation(self):
        ev = Evaluator(min_radius=600, max_grade=0.025)
        r = ev.evaluate(self._plan([500, 1000]), self._profile([0.01]), 40)
        self.assertEqual(r["total_fitness"], HARD_PENALTY)

    def test_hard_penalty_on_grade_violation(self):
        ev = Evaluator(min_radius=600, max_grade=0.025)
        r = ev.evaluate(self._plan([3000]), self._profile([0.03]), 40)
        self.assertEqual(r["total_fitness"], HARD_PENALTY)

    def test_hard_penalty_on_constraints_ok_false(self):
        ev = Evaluator(min_radius=600, max_grade=0.025)
        r = ev.evaluate(
            self._plan([3000]), self._profile([0.01], constraints_ok=False), 40
        )
        self.assertEqual(r["total_fitness"], HARD_PENALTY)

    def test_fitness_responds_to_score(self):
        ev = Evaluator(min_radius=600, max_grade=0.025)
        # 좋은 품질
        good = ev.evaluate(self._plan([5000]), self._profile([0.005]), 40)
        # 나쁜 품질 (위반은 아님)
        bad = ev.evaluate(self._plan([700]), self._profile([0.02]), 40)
        self.assertGreater(good["total_fitness"], bad["total_fitness"])


if __name__ == "__main__":
    unittest.main()