import pytest


class TestExtractFeatureLines:
    def test_returns_dict_of_lists(self, engine):
        fl = engine.extract_feature_lines(0.0, 1000.0, interval=100.0)
        assert isinstance(fl, dict)
        for code, line in fl.items():
            assert isinstance(line, list)

    def test_all_7_codes_present(self, engine):
        fl = engine.extract_feature_lines(0.0, 100.0, interval=50.0)
        expected = {"L_DAY", "L_EPS", "L_ETW", "CL", "R_ETW", "R_EPS", "R_DAY"}
        assert set(fl.keys()) == expected

    def test_sample_count(self, engine):
        """0,100,200,...,1000 → 11개 (종점 포함)"""
        fl = engine.extract_feature_lines(0.0, 1000.0, interval=100.0)
        for code, line in fl.items():
            assert len(line) == 11

    def test_each_entry_is_4_tuple(self, engine):
        fl = engine.extract_feature_lines(0.0, 200.0, interval=100.0)
        for code, line in fl.items():
            for entry in line:
                assert isinstance(entry, tuple)
                assert len(entry) == 4   # (sta, e, n, el)

    def test_first_station_matches_start(self, engine):
        fl = engine.extract_feature_lines(100.0, 900.0, interval=200.0)
        for code, line in fl.items():
            assert line[0][0] == pytest.approx(100.0)

    def test_last_station_matches_end(self, engine):
        fl = engine.extract_feature_lines(100.0, 900.0, interval=200.0)
        for code, line in fl.items():
            assert line[-1][0] == pytest.approx(900.0)

    def test_centerline_stays_at_offset_zero(self, engine):
        fl = engine.extract_feature_lines(0.0, 500.0, interval=100.0)
        # CL의 easting은 station과 동일 (MockAlignment 기준)
        for sta, e, n, el in fl["CL"]:
            assert e == pytest.approx(sta)
            assert n == pytest.approx(0.0)

    def test_bridge_changes_daylight_geometry(self, engine):
        """교량 구간: L_DAY offset이 L_EPS offset - 0.6"""
        from structure.region import StructureRegion
        engine.add_structure(StructureRegion("1교", "BRIDGE", 0.0, 1000.0))

        # ★ 개선: point code의 offset([0])을 직접 사용 — 좌표계 독립적
        sec = engine.sample_cross_section(50.0)
        l_day_off = sec["points"]["L_DAY"][0]
        l_eps_off = sec["points"]["L_EPS"][0]

        # BRIDGE: L_DAY = L_EPS - 0.6 (좌측은 음수 방향으로 0.6m 바깥)
        assert l_eps_off - l_day_off == pytest.approx(0.6, abs=1e-3)