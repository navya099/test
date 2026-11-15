import pytest
from structure.region import StructureRegion


class TestBridge:
    def test_bridge_sets_both_modes(self, engine):
        engine.add_structure(StructureRegion("1교", "BRIDGE", 400.0, 520.0))
        sec = engine.sample_cross_section(450.0)
        assert sec["left_mode"] == "BRIDGE"
        assert sec["right_mode"] == "BRIDGE"

    def test_bridge_daylight_is_railing(self, engine):
        """교량: 난간 0.6m 폭, +0.8m 높이"""
        engine.add_structure(StructureRegion("1교", "BRIDGE", 400.0, 520.0))
        sec = engine.sample_cross_section(450.0)
        l_hinge_off = sec["points"]["L_EPS"][0]
        l_hinge_el = sec["points"]["L_EPS"][3]
        l_day_off = sec["points"]["L_DAY"][0]
        l_day_el = sec["points"]["L_DAY"][3]
        assert l_day_off == pytest.approx(l_hinge_off - 0.6)
        assert l_day_el == pytest.approx(l_hinge_el + 0.8)

    def test_bridge_excludes_earthwork(self, engine):
        """교량 구간은 절토/성토 면적 0"""
        engine.add_structure(StructureRegion("1교", "BRIDGE", 400.0, 520.0))
        sec = engine.sample_cross_section(450.0)
        assert sec["cut_area"] == 0.0
        assert sec["fill_area"] == 0.0


class TestTunnel:
    def test_tunnel_sets_both_modes(self, engine):
        engine.add_structure(StructureRegion("1터널", "TUNNEL", 760.0, 860.0))
        sec = engine.sample_cross_section(800.0)
        assert sec["left_mode"] == "TUNNEL"
        assert sec["right_mode"] == "TUNNEL"

    def test_tunnel_daylight_is_wall_plus_ceiling(self, engine):
        """터널: 측벽 0.8m, 상단 +4.5m"""
        engine.add_structure(StructureRegion("1터널", "TUNNEL", 760.0, 860.0))
        sec = engine.sample_cross_section(800.0)
        l_hinge_off = sec["points"]["L_EPS"][0]
        l_hinge_el = sec["points"]["L_EPS"][3]
        l_day_off = sec["points"]["L_DAY"][0]
        l_day_el = sec["points"]["L_DAY"][3]
        assert l_day_off == pytest.approx(l_hinge_off - 0.8)
        assert l_day_el == pytest.approx(l_hinge_el + 4.5)

    def test_tunnel_excludes_earthwork(self, engine):
        engine.add_structure(StructureRegion("1터널", "TUNNEL", 760.0, 860.0))
        sec = engine.sample_cross_section(800.0)
        assert sec["cut_area"] == 0.0
        assert sec["fill_area"] == 0.0


class TestRetainingWall:
    def test_right_wall_only(self, engine):
        engine.add_structure(StructureRegion(
            "옹벽A", "RETAINING_WALL", 1050.0, 1180.0, wall_side="RIGHT"
        ))
        sec = engine.sample_cross_section(1100.0)
        assert sec["right_mode"] == "WALL"
        assert sec["left_mode"] in ("CUT", "FILL")   # 좌측은 일반 토공

    def test_left_wall_only(self, engine):
        engine.add_structure(StructureRegion(
            "옹벽B", "RETAINING_WALL", 200.0, 300.0, wall_side="LEFT"
        ))
        sec = engine.sample_cross_section(250.0)
        assert sec["left_mode"] == "WALL"
        assert sec["right_mode"] in ("CUT", "FILL")

    def test_both_walls(self, engine):
        engine.add_structure(StructureRegion(
            "옹벽C", "RETAINING_WALL", 400.0, 500.0, wall_side="BOTH"
        ))
        sec = engine.sample_cross_section(450.0)
        assert sec["left_mode"] == "WALL"
        assert sec["right_mode"] == "WALL"

    def test_wall_narrow_offset(self, engine):
        """옹벽은 Hinge에서 0.4m만 바깥"""
        engine.add_structure(StructureRegion(
            "옹벽C", "RETAINING_WALL", 400.0, 500.0, wall_side="RIGHT"
        ))
        sec = engine.sample_cross_section(450.0)
        r_hinge = sec["points"]["R_EPS"][0]
        r_day = sec["points"]["R_DAY"][0]
        assert r_day == pytest.approx(r_hinge + 0.4)


class TestStructureRegistration:
    def test_add_structure_returns_self(self, engine):
        result = engine.add_structure(StructureRegion("1교", "BRIDGE", 0, 100))
        assert result is engine

    def test_get_active_structures_includes_boundaries(self, engine):
        engine.add_structure(StructureRegion("1교", "BRIDGE", 400.0, 520.0))
        assert len(engine.get_active_structures(400.0)) == 1   # 시작 경계
        assert len(engine.get_active_structures(520.0)) == 1   # 끝 경계
        assert len(engine.get_active_structures(399.99)) == 0
        assert len(engine.get_active_structures(520.01)) == 0

    def test_multiple_overlapping_structures(self, engine):
        engine.add_structure(StructureRegion("1교", "BRIDGE", 100.0, 500.0))
        engine.add_structure(StructureRegion("1터널", "TUNNEL", 200.0, 300.0))
        # 200~300 구간에서는 둘 다 활성
        structs = engine.get_active_structures(250.0)
        assert len(structs) == 2
        # BRIDGE 우선 (engine 로직상 "BRIDGE" in struct_types)
        sec = engine.sample_cross_section(250.0)
        assert sec["left_mode"] == "BRIDGE"