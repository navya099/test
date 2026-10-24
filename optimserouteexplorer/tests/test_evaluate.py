# tests/test_evaluate.py
import unittest

from core.evaluate import Evaluator, HARD_PENALTY


class FakeStructureCollection:
    def get_by_type(self, t):
        return []


class FakeLineString:
    def __init__(self, length):
        self.length = length


class TestEvaluator(unittest.TestCase):
    def _plan(self, radius_list, length=1000, converged=True):
        return {
            "linestring": FakeLineString(length),
            "station_list": [0, 500, 1000],
            "radius_list": radius_list,
            "converged": converged,
        }

    def _profile(self, slopes, constraints_ok=True, min_cover_violation=0.0):
        n = len(slopes) + 1
        return {
            "design_elevs": [10.0] * n,
            "ground_elevs": [5.0] * n,
            "slopes": slopes,
            "constraints_ok": constraints_ok,
            "min_cover_violation": min_cover_violation,
        }

    def test_hard_penalty_on_radius_violation(self):
        ev = Evaluator(min_radius=600, max_grade=0.035)
        r = ev.evaluate(self._plan([500, 1000]), self._profile([0.01]), 40)
        self.assertEqual(r["total_fitness"], HARD_PENALTY)

    def test_hard_penalty_on_grade_violation(self):
        ev = Evaluator(min_radius=600, max_grade=0.035)
        r = ev.evaluate(self._plan([3000]), self._profile([0.04]), 40)
        self.assertEqual(r["total_fitness"], HARD_PENALTY)

    def test_hard_penalty_on_constraints_ok_false(self):
        ev = Evaluator(min_radius=600, max_grade=0.035)
        r = ev.evaluate(
            self._plan([3000]), self._profile([0.01], constraints_ok=False), 40
        )
        self.assertEqual(r["total_fitness"], HARD_PENALTY)

    def test_hard_penalty_on_not_converged(self):
        ev = Evaluator(min_radius=600, max_grade=0.035)
        r = ev.evaluate(
            self._plan([3000], converged=False), self._profile([0.01]), 40
        )
        self.assertEqual(r["total_fitness"], HARD_PENALTY)

    def test_fitness_responds_to_score(self):
        ev = Evaluator(min_radius=600, max_grade=0.035)
        good = ev.evaluate(self._plan([5000]), self._profile([0.005]), 40)
        bad = ev.evaluate(self._plan([700]), self._profile([0.02]), 40)
        self.assertGreater(good["total_fitness"], bad["total_fitness"])

    def test_min_cover_violation_reduces_score(self):
        """min_cover 위반 소프트 감점."""
        ev = Evaluator(min_radius=600, max_grade=0.035)
        no_violation = ev.evaluate(
            self._plan([3000]), self._profile([0.01], min_cover_violation=0.0), 40
        )
        violation = ev.evaluate(
            self._plan([3000]), self._profile([0.01], min_cover_violation=100.0), 40
        )
        self.assertGreater(no_violation["total_score"], violation["total_score"])
        self.assertGreater(no_violation["total_fitness"], violation["total_fitness"])


if __name__ == "__main__":
    unittest.main()