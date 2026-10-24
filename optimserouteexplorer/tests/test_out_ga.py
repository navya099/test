# tests/test_out_ga.py
import json
import unittest

from out.out_ga import format_top10


class FakeStructureCollection:
    def get_structure_type_at(self, sta):
        return "교량" if sta > 500 else None

    def find_containing(self, sta):
        if sta > 500:
            return type("S", (), {"name": "교량1", "length": 100.0})()
        return None


class FakeLineString:
    length = 1000.0


class TestFormatTop10(unittest.TestCase):
    def _make_candidate(self, i, with_collection=True):
        return {
            "plan_full": {
                "linestring": FakeLineString(),
                "wgs_coords": [(127.0 + i * 0.001, 37.5 + i * 0.001)],
                "station_list": [0, 600, 1000],
            },
            "profile": {
                "slopes": [0.01, -0.02],
                "fg_profile": [10.0, 12.0],
                "eg_profile": [8.0, 9.0],
            },
            "result": {
                "bridges": [1, 2],
                "tunnels": [],
                "structure_collection": (
                    FakeStructureCollection() if with_collection else None
                ),
            },
            "radius_list": [3000.0, 4000.0],
            "cost": 1234.567,
            "fitness": 75.5,
            "score": 80.0,
        }

    def test_json_serializable(self):
        """결과가 json.dumps 가능 (jsonify 안전)."""
        pop = [self._make_candidate(i) for i in range(3)]
        top = format_top10(pop, 10)
        s = json.dumps(top)   # 크래시 없으면 OK
        self.assertGreater(len(s), 0)

    def test_expected_keys(self):
        pop = [self._make_candidate(0)]
        top = format_top10(pop, 10)
        for key in ("ID", "노선연장", "공사비", "교량갯수", "터널갯수",
                    "곡선갯수", "최소곡선반경", "coords", "collections"):
            self.assertIn(key, top[0])

    def test_collections_are_dicts(self):
        """collections 가 list[dict] 로 변환."""
        pop = [self._make_candidate(0)]
        top = format_top10(pop, 10)
        self.assertIsInstance(top[0]["collections"], list)
        self.assertIsInstance(top[0]["collections"][0], dict)
        for entry in top[0]["collections"]:
            self.assertIn("station", entry)
            self.assertIn("type", entry)

    def test_empty_population(self):
        self.assertEqual(format_top10([], 10), [])

    def test_missing_keys_no_crash(self):
        """필드 누락 시 크래시 없음."""
        pop = [{}]
        top = format_top10(pop, 10)
        self.assertEqual(len(top), 1)

    def test_empty_radius_and_slopes(self):
        """빈 radius_list/slopes → 가드."""
        c = self._make_candidate(0)
        c["radius_list"] = []
        c["profile"]["slopes"] = []
        top = format_top10([c], 10)
        self.assertIsNone(top[0]["최소곡선반경"])
        self.assertEqual(top[0]["최급기울기"], 0.0)


if __name__ == "__main__":
    unittest.main()