# tests/test_visualgraphic.py
import os
import tempfile
import unittest

from visual.visualgraphic import visualize_routes_with_button


class TestVisualize(unittest.TestCase):
    def _alignment(self, i):
        return {
            "ID": i,
            "노선연장": 10.5,
            "공사비": 1234.5,
            "교량갯수": 2,
            "터널갯수": 1,
            "coords": [[37.5 + i * 0.001, 127.0 + i * 0.001]] * 20,
            "station_list": list(range(0, 2000, 100)),
            "collections": [
                {"station": sta, "type": "교량" if sta > 500 else None,
                 "name": "교량1" if sta > 500 else None,
                 "length": 100.0 if sta > 500 else 0.0}
                for sta in range(0, 2000, 100)
            ],
            "fls": [10.0, 12.0, 11.0],
            "grounds": [8.0, 9.0, 8.5],
        }

    def test_generates_html(self):
        """dict 기반 collections 로 크래시 없이 HTML 생성."""
        pop = [self._alignment(0), self._alignment(1)]
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "map.html")
            visualize_routes_with_button(
                pop, start=(37.5, 127.0), end=(37.6, 127.1),
                top_n=2, map_file=path,
            )
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 0)

    def test_empty_population(self):
        """빈 후보 → 크래시 없음."""
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "map.html")
            visualize_routes_with_button(
                [], start=(37.5, 127.0), end=(37.6, 127.1),
                top_n=5, map_file=path,
            )
            self.assertFalse(os.path.exists(path))   # 파일 생성 안 함

    def test_missing_collections(self):
        """collections 누락 → 크래시 없음."""
        a = self._alignment(0)
        a["collections"] = []
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "map.html")
            visualize_routes_with_button(
                [a], start=(37.5, 127.0), end=(37.6, 127.1),
                top_n=1, map_file=path,
            )
            self.assertTrue(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()