import pytest
from surface.surface import ExistingGroundTerrain


class TestDaylightSearch:
    def test_cut_mode_when_hinge_below_ground(self):
        """설계고 < 지반고 → 절토(CUT), Daylight는 위로 상승"""
        # 지반을 설계고보다 3m 높게 설정
        def eg(station):
            return 50.0

        def design(station):
            return 40.0

        terrain = ExistingGroundTerrain(base_profile_func=lambda s: eg(s))
        mode, off, el = terrain.find_daylight_intersection(
            station=0.0, hinge_offset=5.0, hinge_el=design(0.0),
            side_sign=+1.0, cut_slope_ratio=1.0, fill_slope_ratio=1.5,
            max_search_width=40.0, step=0.25
        )
        assert mode == "CUT"
        assert off > 5.0            # 바깥쪽
        assert el > design(0.0)     # 상승

    def test_fill_mode_when_hinge_above_ground(self):
        """설계고 > 지반고 → 성토(FILL), Daylight는 아래로 하강"""
        def eg(station):
            return 30.0

        def design(station):
            return 40.0

        terrain = ExistingGroundTerrain(base_profile_func=lambda s: eg(s))
        # 최대 탐색 폭 40m, 성토 1:1.5 → 10m 하강 시 지반 도달
        mode, off, el = terrain.find_daylight_intersection(
            station=0.0, hinge_offset=5.0, hinge_el=design(0.0),
            side_sign=+1.0, cut_slope_ratio=1.0, fill_slope_ratio=1.5,
            max_search_width=40.0, step=0.25
        )
        assert mode == "FILL"
        assert off > 5.0
        assert el < design(0.0)

    def test_left_side_sign_negative(self):
        """side_sign=-1: 좌측은 offset이 감소"""
        def eg(station):
            return 30.0

        terrain = ExistingGroundTerrain(base_profile_func=eg)
        mode, off, el = terrain.find_daylight_intersection(
            station=0.0, hinge_offset=-5.0, hinge_el=40.0,
            side_sign=-1.0, fill_slope_ratio=1.5
        )
        assert mode == "FILL"
        assert off < -5.0   # 더 음수 (좌측 바깥)

    def test_returns_max_width_when_no_intersection(self):
        """지반이 너무 멀어 탐색 폭 초과 시 max 반환"""
        terrain = ExistingGroundTerrain(base_profile_func=lambda s: 0.0)
        mode, off, el = terrain.find_daylight_intersection(
            station=0.0, hinge_offset=5.0, hinge_el=100.0,
            side_sign=+1.0, max_search_width=10.0, step=0.5
        )
        assert mode == "FILL"
        assert off == pytest.approx(15.0)   # 5.0 + 10.0

    def test_exact_intersection_is_continuous(self):
        """정밀 보간: 반환점에서 설계고 ≈ 지반고"""
        terrain = ExistingGroundTerrain(base_profile_func=lambda s: 40.0 + s * 0.05)
        mode, off, el = terrain.find_daylight_intersection(
            station=0.0, hinge_offset=5.0, hinge_el=39.0,
            side_sign=+1.0, cut_slope_ratio=1.0, fill_slope_ratio=1.5
        )
        # 반환된 offset에서 지반고와 설계고가 거의 일치
        eg_at = terrain.elevation_at(0.0, 0.0, 0.0, off)
        assert el == pytest.approx(eg_at, abs=0.1)