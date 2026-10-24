# tests/test_linestringprocessor.py
import unittest

import numpy as np
from shapely import LineString

from core.linestringprocessor import LineStringProcessor


class TestLineStringProcessor(unittest.TestCase):
    def test_angles_length_matches_coords_minus_2(self):
        """angles 길이 = len(coords) - 2 (정상)."""
        ls = LineString([(0, 0), (100, 50), (200, 0)])
        lsp = LineStringProcessor(ls)
        lsp._calculate_angles()
        self.assertEqual(len(lsp.angles), 1)

    def test_angles_with_duplicate_points(self):
        """중복점이 있어도 angles 길이 유지 (NaN)."""
        ls = LineString([(0, 0), (100, 0), (100, 0), (200, 0)])
        lsp = LineStringProcessor(ls)
        lsp._calculate_angles()
        self.assertEqual(len(lsp.angles), 2)
        self.assertTrue(np.isnan(lsp.angles[1]))

    def test_adjust_linestring_with_duplicates_no_crash(self):
        """중복점 + 급각 정점 조정 시 크래시 없음."""
        ls = LineString([(0, 0), (100, 0), (100, 0), (200, 100), (300, 0)])
        lsp = LineStringProcessor(ls)
        lsp.process_linestring(tolerance=60)
        self.assertIsNotNone(lsp.linestring)

    def test_adjust_removes_sharp_angle(self):
        """급각 정점 제거."""
        ls = LineString([(0, 0), (100, 100), (200, 0)])
        lsp = LineStringProcessor(ls)
        lsp._calculate_angles()
        angle = lsp.angles[0]
        lsp._adjust_linestring(tolerance=60)
        coords = list(lsp.linestring.coords)
        if angle > 60:
            self.assertEqual(len(coords), 2)
        else:
            self.assertEqual(len(coords), 3)

    def test_process_linestring_no_crash(self):
        """일반 경로 process_linestring 크래시 없음."""
        ls = LineString([(0, 0), (500, 100), (1000, 0), (1500, 100), (2000, 0)])
        lsp = LineStringProcessor(ls)
        lsp.process_linestring()
        self.assertIsNotNone(lsp.linestring)
        self.assertGreater(len(lsp.angles), 0)

    def test_resample_dedup(self):
        """재샘플링 후 중복점 없음."""
        ls = LineString([(0, 0), (1000, 0)])
        lsp = LineStringProcessor(ls)
        lsp.resample_linestring(interval=100)
        coords = list(lsp.linestring.coords)
        for i in range(1, len(coords)):
            self.assertGreater(
                LineString([coords[i-1], coords[i]]).length, 1e-6
            )
        self.assertEqual(len(lsp.stations), len(coords))

    def test_empty_linestring(self):
        """빈 LineString 처리."""
        lsp = LineStringProcessor(LineString())   # ← 수정: 빈 LineString
        lsp._calculate_angles()
        self.assertEqual(lsp.angles, [])

    def test_two_point_linestring(self):
        """2점 LineString → angles 빈 리스트 (중간점 없음)."""
        lsp = LineStringProcessor(LineString([(0, 0), (100, 0)]))
        lsp._calculate_angles()
        self.assertEqual(lsp.angles, [])


if __name__ == "__main__":
    unittest.main()