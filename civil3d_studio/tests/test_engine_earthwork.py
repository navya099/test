import pytest


class TestComputeEarthworkVolumes:
    def test_returns_list(self, engine):
        report = engine.compute_earthwork_volumes(interval=100.0)
        assert isinstance(report, list)
        assert len(report) > 0

    def test_report_length_matches_intervals(self, engine):
        """total_length=1000, interval=100 → stations=[0,100,...,1000], report=10행"""
        report = engine.compute_earthwork_volumes(interval=100.0)
        assert len(report) == 10

    def test_each_row_has_required_keys(self, engine):
        report = engine.compute_earthwork_volumes(interval=200.0)
        for row in report:
            for key in ("station", "cut_area", "fill_area",
                        "cut_vol", "fill_vol", "cum_cut", "cum_fill", "structures"):
                assert key in row

    def test_cumulative_monotonic_increase(self, engine):
        """누적 토공량은 항상 증가 (양수 면적 기준)"""
        engine.terrain = __import__("surface.surface", fromlist=["ExistingGroundTerrain"]).ExistingGroundTerrain(
            base_profile_func=lambda s: 35.0   # 설계고(40)보다 낮음 → 성토
        )
        report = engine.compute_earthwork_volumes(interval=100.0)
        cum = [r["cum_fill"] for r in report]
        for i in range(1, len(cum)):
            assert cum[i] >= cum[i - 1] - 1e-9

    def test_first_row_station_correct(self, engine):
        report = engine.compute_earthwork_volumes(interval=100.0)
        assert report[0]["station"] == pytest.approx(100.0)

    def test_last_row_station_is_total_length(self, engine):
        report = engine.compute_earthwork_volumes(interval=100.0)
        assert report[-1]["station"] == pytest.approx(1000.0)

    def test_structures_field_is_list(self, engine):
        engine.add_structure(
            __import__("structure.region", fromlist=["StructureRegion"]).StructureRegion(
                "1교", "BRIDGE", 400.0, 600.0
            )
        )
        report = engine.compute_earthwork_volumes(interval=100.0)
        # STA 500 행에서 구조물 ["1교"] 포함
        row_500 = next((r for r in report if abs(r["station"] - 500.0) < 1e-6), None)
        assert row_500 is not None
        assert "1교" in row_500["structures"]

    def test_bridge_segment_has_zero_earthwork(self, engine):
        """교량 구간은 면적 0 → 부피도 0"""
        from structure.region import StructureRegion
        engine.add_structure(StructureRegion("1교", "BRIDGE", 400.0, 600.0))
        report = engine.compute_earthwork_volumes(interval=100.0)
        # STA 500 근처는 교량 내부
        row_500 = next(r for r in report if abs(r["station"] - 500.0) < 1e-6)
        assert row_500["cut_area"] == pytest.approx(0.0, abs=1e-6)
        assert row_500["fill_area"] == pytest.approx(0.0, abs=1e-6)