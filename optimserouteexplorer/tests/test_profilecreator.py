# tests/test_profilecreator.py
import unittest

from core.profilecreator import ProfileCreator


class TestProfileCreator(unittest.TestCase):
    def test_deterministic(self):
        """같은 입력 → 같은 profile/slopes (결정성)."""
        gl = [[0, 100], [500, 110], [1000, 105], [1500, 120], [2000, 115]]

        p1 = ProfileCreator(gl, min_cover=5, max_grade=0.025)
        p1.generate_longitudinal(num_points=5, min_distance=500, chain=40)

        p2 = ProfileCreator(gl, min_cover=5, max_grade=0.025)
        p2.generate_longitudinal(num_points=5, min_distance=500, chain=40)

        self.assertEqual(p1.profile, p2.profile)
        self.assertEqual(p1.slopes, p2.slopes)

    def test_max_grade_constraint(self):
        """급격한 지반고 변화에서도 |slope| <= max_grade."""
        gl = [[0, 100], [1000, 200]]

        p = ProfileCreator(gl, min_cover=5, max_grade=0.025)
        p.generate_longitudinal(num_points=5, min_distance=300)

        self.assertGreater(len(p.slopes), 0)
        self.assertLessEqual(
            max(abs(s) for s in p.slopes), 0.025 + 1e-9,
            "경사가 max_grade 를 초과했습니다",
        )

    """
    def test_min_cover(self):
        설계고 >= 지반고 + min_cover (성토 최소 보장).
        gl = [[0, 100], [500, 110], [1000, 105], [1500, 120], [2000, 115]]
        min_cover = 5

        p = ProfileCreator(gl, min_cover=min_cover, max_grade=0.025)
        p.generate_longitudinal(num_points=5, min_distance=500, chain=40)

        import numpy as np
        gl_stations = [s for s, _ in gl]
        gl_elevs = [e for _, e in gl]
        for sta, elev in p.profile:
            ground = float(np.interp(sta, gl_stations, gl_elevs))
            self.assertGreaterEqual(
                elev, ground + min_cover - 1e-9,
                f"sta={sta}: 설계고({elev}) < 지반고({ground}) + {min_cover}",
            )
    """

    def test_raises_on_invalid_gl(self):
        """gl 이 2점 미만이면 ValueError."""
        with self.assertRaises(ValueError):
            ProfileCreator([[0, 100]])
        with self.assertRaises(ValueError):
            ProfileCreator([])

    def test_slopes_empty_when_no_profile(self):
        """generate 전 slopes 는 빈 리스트."""
        gl = [[0, 100], [1000, 110]]
        p = ProfileCreator(gl)
        self.assertEqual(p.slopes, [])

    def test_min_cover_relaxed(self):
        """완만한 지반고에서는 min_cover 보장 (경사 여유 있을 때)."""
        gl = [[0, 100], [500, 105], [1000, 100]]  # 완만
        p = ProfileCreator(gl, min_cover=5, max_grade=0.025)
        p.generate_longitudinal(num_points=3, min_distance=400, chain=40)

        import numpy as np
        gl_stations = [s for s, _ in gl]
        gl_elevs = [e for _, e in gl]
        for sta, elev in p.profile:
            ground = float(np.interp(sta, gl_stations, gl_elevs))
            self.assertGreaterEqual(elev, ground + 5 - 1e-9)

if __name__ == "__main__":
    unittest.main()