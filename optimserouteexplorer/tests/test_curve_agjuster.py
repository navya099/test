# tests/test_curve_agjuster.py
import unittest

from shapely import LineString

from core.curveadjuster import CurveAdjuster
from core.linestringprocessor import LineStringProcessor


class TestCurveAdjuster(unittest.TestCase):
    def _make(self, coords):
        ls = LineString(coords)
        lsp = LineStringProcessor(ls)
        lsp.process_linestring()
        angles = lsp.angles
        radius_list = [3000.0] * len(angles)
        return CurveAdjuster(lsp.linestring, angles, radius_list)

    def test_length_mismatch_raises(self):
        ls = LineString([(0, 0), (1000, 100), (2000, 0)])
        ca = CurveAdjuster(ls, [30.0], [])
        with self.assertRaises(ValueError):
            ca.main_loop()

    def test_main_loop_returns_bool(self):
        """2km 경로도 100m 기준에서는 수렴."""
        ca = self._make([(0, 0), (1000, 100), (2000, 0)])
        ok = ca.main_loop()   # 기본 100m
        self.assertIsInstance(ok, bool)
        self.assertTrue(ok, "100m 기준에서는 수렴해야 함")
        self.assertTrue(ca.converged)

    def test_radius_updated_after_loop(self):
        ca = self._make([(0, 0), (1000, 100), (2000, 0)])
        original = list(ca.radius_list)
        ca.main_loop()
        self.assertEqual(len(ca.radius_list), len(original))

    def test_min_arc_distance_2000m_fails_short(self):
        """2000m 기준은 짧은 경로에서 수렴 실패 (실무 기준과 대비)."""
        ca = self._make([(0, 0), (1000, 100), (2000, 0)])
        ok = ca.main_loop(min_arc_to_arc_distance=2000, max_iterations=20)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()