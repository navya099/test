import pytest
from structure.region import StructureRegion


class TestSampleCrossSection:
    def test_basic_returns_dict_with_required_keys(self, engine):
        sec = engine.sample_cross_section(100.0)
        assert isinstance(sec, dict)
        for key in ("station", "points", "left_mode", "right_mode",
                    "cut_area", "fill_area", "structures"):
            assert key in sec

    def test_station_echoed_correctly(self, engine):
        sec = engine.sample_cross_section(123.456)
        assert sec["station"] == 123.456

    def test_centerline_elevation_matches_profile(self, engine, mock_profile):
        for sta in (0.0, 100.0, 500.0, 999.0):
            sec = engine.sample_cross_section(sta)
            cl_el = sec["points"]["CL"][3]
            expected = mock_profile.elevation_at(sta)
            assert cl_el == pytest.approx(expected, abs=1e-6)

    def test_centerline_offset_zero(self, engine):
        sec = engine.sample_cross_section(200.0)
        assert sec["points"]["CL"][0] == pytest.approx(0.0)

    def test_etw_offsets_match_lane_widths(self, engine):
        sec = engine.sample_cross_section(200.0)
        l_etw = sec["points"]["L_ETW"][0]
        r_etw = sec["points"]["R_ETW"][0]
        assert l_etw == pytest.approx(-3.5)
        assert r_etw == pytest.approx(+3.5)

    def test_hinge_offsets_are_etw_plus_1_5(self, engine):
        sec = engine.sample_cross_section(200.0)
        assert sec["points"]["L_EPS"][0] == pytest.approx(-3.5 - 1.5)
        assert sec["points"]["R_EPS"][0] == pytest.approx(+3.5 + 1.5)

    def test_etw_elevation_applies_superelevation(self, engine):
        """편경사 -2%, 폭 3.5m → 좌/우 ETW EL = CL EL - 0.07"""
        sec = engine.sample_cross_section(200.0)
        cl_el = sec["points"]["CL"][3]
        l_etw_el = sec["points"]["L_ETW"][3]
        r_etw_el = sec["points"]["R_ETW"][3]
        assert l_etw_el == pytest.approx(cl_el - 3.5 * 0.02)
        assert r_etw_el == pytest.approx(cl_el - 3.5 * 0.02)

    def test_seven_point_codes_present(self, engine):
        sec = engine.sample_cross_section(50.0)
        expected_codes = {"L_DAY", "L_EPS", "L_ETW", "CL", "R_ETW", "R_EPS", "R_DAY"}
        assert set(sec["points"].keys()) == expected_codes

    def test_all_points_have_4_tuple(self, engine):
        sec = engine.sample_cross_section(50.0)
        for code, val in sec["points"].items():
            assert isinstance(val, tuple)
            assert len(val) == 4, f"{code} must have (off, e, n, el)"

    def test_daylight_offsets_beyond_hinge(self, engine):
        """일반 토공: Daylight는 Hinge보다 더 바깥쪽"""
        sec = engine.sample_cross_section(50.0)
        l_day_off = sec["points"]["L_DAY"][0]
        r_day_off = sec["points"]["R_DAY"][0]
        l_hinge_off = sec["points"]["L_EPS"][0]
        r_hinge_off = sec["points"]["R_EPS"][0]
        assert l_day_off < l_hinge_off   # 더 음수 (좌측 바깥)
        assert r_day_off > r_hinge_off   # 더 양수 (우측 바깥)