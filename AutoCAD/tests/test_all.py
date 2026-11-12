"""
myAutoCAD 기하학 계층 테스트.

기존 test.py의 수동 print 테스트를 pytest 기반으로 전환하고,
리팩토링에서 수정한 버그에 대한 회귀 테스트를 추가한다.

실행: pytest test_all.py -v
"""
import math

import pytest

from cadgeom import Point2d, AngleUnit, Point3d, Line2d, Line3d, Arc, BulgeSegment, Polyline


# ============================================================
# Point2d
# ============================================================

class TestPoint2d:
    def test_distance_and_angle(self):
        """기존 테스트의 기준값 유지."""
        p1 = Point2d(25.5079, -291.0697)
        p2 = Point2d(-115.1379, -425.3316)

        # 기존 주석의 "5"는 오기 — 실제 거리로 검증
        expected = math.hypot(p2.x - p1.x, p2.y - p1.y)
        assert p1.distance_to(p2) == pytest.approx(expected)

        rad = p1.angle_to(p2)
        deg = p1.angle_to(p2, AngleUnit.DEG)
        assert deg == pytest.approx(math.degrees(rad))
        # 3사분면 방향이므로 rad는 -π ~ -π/2 사이
        assert -math.pi < rad < -math.pi / 2

    def test_move_and_moved(self):
        p1 = Point2d(25.5079, -291.0697)
        original_x, original_y = p1.x, p1.y

        p1.move(0.29636, 379.5597)
        assert p1.x == pytest.approx(original_x + 379.5597 * math.cos(0.29636))
        assert p1.y == pytest.approx(original_y + 379.5597 * math.sin(0.29636))

        p3 = p1.moved(0, 5)
        assert p3.x == pytest.approx(p1.x + 5)
        assert p3.y == pytest.approx(p1.y)
        # moved는 원본을 변경하지 않음
        assert p1.x != p3.x

    def test_rotate_about_origin(self):
        p = Point2d(1, 0)
        p.rotate(math.pi / 2, Point2d(0, 0))
        assert p.x == pytest.approx(0, abs=1e-12)
        assert p.y == pytest.approx(1)

    def test_rotate_none_is_noop(self):
        """Point2d.rotate(origin=None)은 자기 자신 중심 = no-op."""
        p = Point2d(3, 4)
        p.rotate(math.pi / 3)
        assert p.x == pytest.approx(3)
        assert p.y == pytest.approx(4)

    def test_equality(self):
        """리팩토링에서 추가한 __eq__ 회귀 테스트."""
        assert Point2d(1, 2) == Point2d(1, 2)
        assert Point2d(1, 2) != Point2d(1, 3)
        # 부동소수점 허용 오차
        assert Point2d(1.0, 2.0) == Point2d(1.0 + 1e-12, 2.0)

    def test_hash(self):
        assert hash(Point2d(1, 2)) == hash(Point2d(1, 2))
        s = {Point2d(1, 2), Point2d(1, 2), Point2d(3, 4)}
        assert len(s) == 2

    def test_distance_to_tuple(self):
        """distance_to가 (x, y) 튜플도 허용."""
        assert Point2d(0, 0).distance_to((3, 4)) == pytest.approx(5)


# ============================================================
# Point3d
# ============================================================

class TestPoint3d:
    def test_distance_modes(self):
        p1 = Point3d(0, 0, 0)
        p2 = Point3d(3, 4, 12)
        assert p1.distance_to(p2, mode='3d') == pytest.approx(13)
        assert p1.distance_to(p2, mode='2d') == pytest.approx(5)

    def test_move_does_not_change_z(self):
        """리팩토링에서 분리한 계약: move는 XY만, translate는 z 포함."""
        p = Point3d(0, 0, 7)
        p.move(math.pi / 2, 2)
        assert p.z == pytest.approx(7)
        assert p.x == pytest.approx(0, abs=1e-12)
        assert p.y == pytest.approx(2)

        p.translate(0, 0, -3)
        assert p.z == pytest.approx(4)

    def test_azimuth_elevation(self):
        """angle_to('3d') 튜플 반환 계약 위반 해소 회귀 테스트."""
        p1 = Point3d(0, 0, 0)
        p2 = Point3d(1, 1, 1)
        az, el = p1.azimuth_elevation_to(p2)
        assert az == pytest.approx(math.pi / 4)
        assert el == pytest.approx(math.atan2(1, math.hypot(1, 1)))

        # angle_to는 float만 반환
        angle = p1.angle_to(p2)
        assert isinstance(angle, float)
        assert angle == pytest.approx(math.pi / 4)

    def test_rotate3d_axis(self):
        p = Point3d(1, 0, 0)
        p.rotate3d(math.pi / 2, Point3d(0, 0, 0), axis='z')
        assert p.x == pytest.approx(0, abs=1e-12)
        assert p.y == pytest.approx(1)

    def test_rotate3d_invalid_axis(self):
        with pytest.raises(ValueError):
            Point3d(1, 0, 0).rotate3d(0.1, axis='w')


# ============================================================
# Line2d
# ============================================================

class TestLine2d:
    def test_length_and_direction(self):
        l = Line2d(Point2d(0, 0), Point2d(4, 0))
        assert l.length == pytest.approx(4)
        assert l.direction == pytest.approx(0)

    def test_distance_to_point(self):
        l = Line2d(Point2d(0, 0), Point2d(4, 0))
        assert l.distance_to_point(Point2d(2, 3)) == pytest.approx(3)
        # 선분 밖의 점
        assert l.distance_to_point(Point2d(-3, 0)) == pytest.approx(3)
        assert l.distance_to_point(Point2d(7, 0)) == pytest.approx(3)

    def test_distance_to_point_via_distance_to(self):
        """리팩토링에서 고친 버그: distance_to가 점도 받아야 함."""
        l = Line2d(Point2d(0, 0), Point2d(4, 0))
        assert l.distance_to(Point2d(2, 3)) == pytest.approx(3)

    def test_distance_to_line(self):
        a = Line2d(Point2d(0, 0), Point2d(4, 0))
        b = Line2d(Point2d(0, 2), Point2d(4, 2))
        assert a.distance_to(b) == pytest.approx(2)

    def test_move_and_moved(self):
        l = Line2d(Point2d(0, 0), Point2d(4, 0))
        l.move(math.pi / 2, 1)
        assert l.start.y == pytest.approx(1)
        assert l.end.y == pytest.approx(1)

        l2 = l.moved(0, 2)
        assert l2.start.x == pytest.approx(l.start.x + 2)
        # moved는 원본 불변
        assert l.start.x == pytest.approx(0, abs=1e-12)

    def test_rotate_about_center(self):
        l = Line2d(Point2d(0, 0), Point2d(4, 0))
        l.rotate(math.pi / 4)
        # 중점 (2,0) 기준 회전이므로 중점은 불변
        mid = Point2d((l.start.x + l.end.x) / 2, (l.start.y + l.end.y) / 2)
        assert mid.x == pytest.approx(2)
        assert mid.y == pytest.approx(0, abs=1e-12)

    def test_get_y_from_vertical(self):
        """수직선에서 get_y_from_x는 None."""
        l = Line2d(Point2d(1, 0), Point2d(1, 5))
        assert l.get_y_from_x(3) is None
        assert l.get_x_from_y(3) is None


# ============================================================
# Line3d — 리팩토링에서 재작성한 부분
# ============================================================

class TestLine3d:
    def test_copy_returns_line3d(self):
        """회귀 테스트: 이전엔 Line2d를 반환했음."""
        l = Line3d(Point3d(0, 0, 0), Point3d(1, 1, 1))
        c = l.copy()
        assert isinstance(c, Line3d)
        assert c == l

    def test_moved_returns_line3d_and_preserves_z(self):
        l = Line3d(Point3d(0, 0, 5), Point3d(2, 0, 5))
        m = l.moved(math.pi / 2, 1)
        assert isinstance(m, Line3d)
        assert m.start.z == pytest.approx(5)
        assert m.end.z == pytest.approx(5)

    def test_translate_z(self):
        l = Line3d(Point3d(0, 0, 0), Point3d(1, 0, 0))
        l.translate(0, 0, 3)
        assert l.start.z == pytest.approx(3)
        assert l.end.z == pytest.approx(3)

    def test_distance_to_point_3d(self):
        """이전엔 XY만 계산했음."""
        l = Line3d(Point3d(0, 0, 0), Point3d(4, 0, 0))
        # (2, 3, 4)까지 최단 거리 = sqrt(3^2 + 4^2) = 5
        assert l.distance_to_point(Point3d(2, 3, 4)) == pytest.approx(5)

    def test_length_3d(self):
        l = Line3d(Point3d(0, 0, 0), Point3d(1, 2, 2))
        assert l.length == pytest.approx(3)


# ============================================================
# Arc — 호 범위 거리 회귀 테스트
# ============================================================

class TestArc:
    def test_length(self):
        arc = Arc(Point2d(0, 0), 2, 0, math.pi / 2)
        assert arc.theta == pytest.approx(math.pi / 2)
        assert arc.length == pytest.approx(math.pi)

    def test_distance_to_point_on_arc(self):
        """호 범위 안의 점: |중심거리 - 반지름|."""

        arc = Arc(Point2d(0, 0), 1, 0, math.pi / 2)
        # 45° 방향, 반지름 2 → 거리 1
        p = Point2d(math.sqrt(2), math.sqrt(2))
        assert arc.distance_to(p) == pytest.approx(1)

    def test_distance_to_point_outside_arc_range(self):
        """회귀 테스트: 이전엔 호 범위 무시하고 원 전체 거리 반환."""
        arc = Arc(Point2d(0, 0), 1, 0, math.pi / 2)
        # 180° 방향(호 범위 밖). 최단 거리는 끝점(0,1) 또는 시작점(1,0)까지
        p = Point2d(-1, 0)
        expected = min(Point2d(1, 0).distance_to(p),
                       Point2d(0, 1).distance_to(p))
        assert arc.distance_to(p) == pytest.approx(expected)
        # 원 전체 거리(|1 - 1| = 0)가 아님을 확인
        assert arc.distance_to(p) != pytest.approx(0)

    def test_theta_wraps_counterclockwise(self):
        arc = Arc(Point2d(0, 0), 1, 350 * math.pi / 180, 10 * math.pi / 180)
        assert arc.theta == pytest.approx(20 * math.pi / 180)

    def test_start_end_mid(self):
        arc = Arc(Point2d(0, 0), 1, 0, math.pi / 2)
        assert arc.start_point == Point2d(1, 0)
        assert arc.end_point == Point2d(0, 1)
        assert arc.mid_point == Point2d(math.sqrt(2) / 2, math.sqrt(2) / 2)

    def test_invalid_radius(self):
        with pytest.raises(ValueError):
            Arc(Point2d(0, 0), 0, 0, 1)

    def test_move_moved_rotate(self):
        arc = Arc(Point2d(373.1645, -458.3618), 385.8131, 1.1287, 2.693)
        old_center = arc.center.copy()
        arc.move(math.pi / 2, 2)
        assert arc.center.x == pytest.approx(old_center.x)
        assert arc.center.y == pytest.approx(old_center.y + 2)

        arc2 = arc.moved(0, 3)
        assert arc2.center.x == pytest.approx(arc.center.x + 3)
        # moved는 원본 불변
        assert arc.center.x == pytest.approx(old_center.x)

        old_start, old_end = arc.start_angle, arc.end_angle
        arc.rotate(math.pi / 4)
        assert arc.start_angle == pytest.approx(old_start + math.pi / 4)
        assert arc.end_angle == pytest.approx(old_end + math.pi / 4)


# ============================================================
# BulgeSegment
# ============================================================

class TestBulgeSegment:
    def test_zero_bulge_is_line(self):
        seg = BulgeSegment(Point2d(0, 0), Point2d(4, 0), bulge=0)
        assert seg.is_line
        assert seg.length == pytest.approx(4)
        assert seg.radius is None
        assert seg.center == Point2d(2, 0)  # None이 아님

    def test_zero_bulge_distance(self):
        seg = BulgeSegment(Point2d(0, 0), Point2d(4, 0), bulge=0)
        assert seg.distance_to(Point2d(2, 3)) == pytest.approx(3)

    def test_semicircle(self):
        """bulge=1 → 반원(180°)."""
        seg = BulgeSegment(Point2d(0, 0), Point2d(2, 0), bulge=1)
        assert seg.theta == pytest.approx(math.pi)
        assert seg.radius == pytest.approx(1)
        assert seg.center.y == pytest.approx(0, abs=1e-12)

    def test_negative_bulge_clockwise(self):
        seg = BulgeSegment(Point2d(0, 0), Point2d(2, 0), bulge=-1)
        assert seg.theta == pytest.approx(-math.pi)
        # as_arc는 시계 방향을 반시계로 변환
        arc = seg.as_arc
        assert arc is not None
        assert arc.start_point == seg.end
        assert arc.end_point == seg.start

    def test_distance_matches_arc(self):
        """회귀 테스트: distance_to가 as_arc를 통해 호 범위 처리."""
        seg = BulgeSegment(Point2d(0, 0), Point2d(2, 0), bulge=1)
        arc = seg.as_arc
        for p in [Point2d(1, 1), Point2d(3, 3), Point2d(-1, 0)]:
            assert seg.distance_to(p) == pytest.approx(arc.distance_to(p))


# ============================================================
# Polyline
# ============================================================

class TestPolyline:
    def _sample(self):
        v1, v2, v3 = Point2d(0, 0), Point2d(4, 0), Point2d(4, 3)
        return Polyline([Line2d(v1, v2), Line2d(v2, v3)])

    def test_vertex_navigation(self):
        pl = self._sample()
        assert pl.current_vertex == Point2d(0, 0)
        pl.next_vertex()
        assert pl.current_vertex == Point2d(4, 0)
        pl.previous_vertex()
        assert pl.current_vertex == Point2d(0, 0)

    def test_flatten_vertices_dedup(self):
        """리팩토링에서 __eq__ 추가로 실제 중복 제거가 동작."""
        pl = self._sample()
        verts = pl._flatten_vertices()
        assert verts == [Point2d(0, 0), Point2d(4, 0), Point2d(4, 3)]
        assert len(verts) == 3  # (4,0) 중복 제거됨

    def test_add_vertex_appends_line(self):
        pl = self._sample()
        pl.add_vertex(Point2d(8, 3))
        assert len(pl.segments) == 3
        assert isinstance(pl.segments[-1], Line2d)
        assert pl.segments[-1].end == Point2d(8, 3)

    def test_add_vertex_does_not_corrupt_arc(self):
        """회귀 테스트: 이전엔 add_vertex가 모든 세그먼트를 Line2d로 변환."""
        arc = Arc(Point2d(2, 0), 1, 0, math.pi)
        pl = Polyline([arc])
        pl.add_vertex(Point2d(5, 5))  # 끝에 추가 → 기존 Arc 보존
        assert isinstance(pl.segments[0], Arc)
        assert len(pl.segments) == 2

    def test_add_vertex_index_out_of_range(self):
        pl = self._sample()
        with pytest.raises(IndexError):
            pl.add_vertex(Point2d(9, 9), index=99)

    def test_length(self):
        pl = self._sample()
        assert pl.length == pytest.approx(7)  # 4 + 3

    def test_distance_to_point(self):
        pl = self._sample()
        # 점 (2, 2)에서 가장 가까운 세그먼트는 line2(x=4, y=0..3)까지 거리 2
        assert pl.distance_to(Point2d(2, 2)) == pytest.approx(2)

    def test_move_and_copy_independence(self):
        pl = self._sample()
        moved = pl.moved(0, 1)  # 각도 0 = +X 방향
        assert isinstance(moved, Polyline)
        assert pl.current_vertex == Point2d(0, 0)  # 원본 불변
        assert moved.segments[0].start == Point2d(1, 0)  # ← (1, 0)이 맞음

    def test_copy_equality(self):
        pl = self._sample()
        assert pl.copy() == pl

    def test_empty_polyline(self):
        pl = Polyline()
        assert pl.length == 0
        assert pl.current_vertex is None
        assert pl.next_vertex() is None


# ============================================================
# 교차 클래스 계약 테스트
# ============================================================

class TestGeometryContract:
    """모든 Geometry 하위 클래스가 공통 계약을 지키는지."""

    @pytest.mark.parametrize("obj", [
        Point2d(1, 2),
        Point3d(1, 2, 3),
        Line2d(Point2d(0, 0), Point2d(1, 1)),
        Line3d(Point3d(0, 0, 0), Point3d(1, 1, 1)),
        Arc(Point2d(0, 0), 1, 0, 1),
        BulgeSegment(Point2d(0, 0), Point2d(1, 0), 0.5),
        Polyline([Line2d(Point2d(0, 0), Point2d(1, 0))]),
    ])
    def test_copy_returns_same_type(self, obj):
        c = obj.copy()
        assert type(c) is type(obj)
        assert c == obj

    @pytest.mark.parametrize("obj", [
        Point2d(1, 2),
        Point3d(1, 2, 3),
        Line2d(Point2d(0, 0), Point2d(1, 1)),
        Line3d(Point3d(0, 0, 0), Point3d(1, 1, 1)),
        Arc(Point2d(0, 0), 1, 0, 1),
        BulgeSegment(Point2d(0, 0), Point2d(1, 0), 0.5),
        Polyline([Line2d(Point2d(0, 0), Point2d(1, 0))]),
    ])
    def test_moved_returns_same_type_and_preserves_original(self, obj):
        before = obj.copy()
        m = obj.moved(0, 1)
        assert type(m) is type(obj)
        assert obj == before  # 원본 불변

    @pytest.mark.parametrize("obj", [
        Point2d(1, 2),
        Line2d(Point2d(0, 0), Point2d(1, 1)),
        Arc(Point2d(0, 0), 1, 0, 1),
    ])
    def test_center_is_point2d(self, obj):
        assert isinstance(obj.center, Point2d)

    def test_angle_unit_enum(self):
        p1, p2 = Point2d(0, 0), Point2d(1, 1)
        assert p1.angle_to(p2, AngleUnit.RAD) == pytest.approx(math.pi / 4)
        assert p1.angle_to(p2, AngleUnit.DEG) == pytest.approx(45)