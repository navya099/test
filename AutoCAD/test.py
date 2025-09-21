# test.py
from AutoCAD.point2d import Point2d
from AutoCAD.point3d import Point3d
from AutoCAD.geometry import GeoMetry
from AutoCAD.line import Line2d
from AutoCAD.arc import Arc
from AutoCAD.polyline import Polyline
import math

def test_point2d():
    print("=== Point2d 테스트 ===")
    p1 = Point2d(25.5079, -291.0697)
    p2 = Point2d(-115.1379, -425.3316)
    print("거리:", p1.distance_to(p2))  # 5
    print("각도(rad):", p1.angle_to(p2))
    print("각도(deg):", p1.angle_to(p2, 'deg'))

    p1.move(0.29636, 379.5597)
    print("이동 후 p1:", p1.x, p1.y)
    p3 = p1.moved(0, 5)
    print("새로운 이동 p3:", p3.x, p3.y)
    p1.rotate(math.pi/2, Point2d(0,0))
    print("회전 후 p1:", p1.x, p1.y)


def test_line2d():
    print("=== Line2d 테스트 ===")
    l = Line2d(Point2d(0,0), Point2d(4,0))
    print("길이:", l.length)
    print("방향(rad):", l.direction)

    print("점과 선 사이 거리:", l.distance_to_point(Point2d(2,3)))

    l.move(math.pi/2, 1)
    print("이동 후 시작점:", l.start.x, l.start.y, "끝점:", l.end.x, l.end.y)

    l2 = l.moved(0, 2)
    print("새로운 선 l2 시작점:", l2.start.x,  l2.start.y, "끝점:", l2.end.x, l2.end.y)

    l.rotate(math.pi/4)
    print("회전 후 시작점:", l.start.x , l.start.y, "끝점:", l.end.x,   l.end.y)


def test_arc():
    print("=== Arc 테스트 ===")
    center = Point2d(373.1645,-458.3618)
    arc = Arc(center, 385.8131, 1.1287, 2.693)
    print("호 길이:", arc.length)
    print("점과 호 사이 거리:", arc.distance_to(Point2d(212.6111,-262.0468)))

    arc.move(math.pi/2, 2)
    print("이동 후 중심:", arc.center)

    arc2 = arc.moved(0, 3)
    print("새 Arc 중심:", arc2.center)

    arc.rotate(math.pi/4)
    print("회전 후 시작각:", arc.start_angle, "끝각:", arc.end_angle)


def test_polyline():
    print("=== Polyline 테스트 ===")
    v1 = Point2d(0,0)
    v2 = Point2d(4,0)
    v3 = Point2d(4,3)
    line1 = Line2d(v1,v2)
    line2 = Line2d(v2,v3)
    pl = Polyline([line1, line2])

    print("현재 vertex:", pl.current_vertex)
    pl.next_vertex()
    print("다음 vertex:", pl.current_vertex)
    pl.previous_vertex()
    print("이전 vertex:", pl.current_vertex)

    new_vertex = Point2d(2,1)
    pl.add_vertex(new_vertex, 1)
    print("새 vertex 추가 후 current_vertex:", pl.current_vertex)
    print("모든 segments:")
    for seg in pl.segments:
        print(seg.start, "->", seg.end)


if __name__ == "__main__":
    test_point2d()
    print()
    test_line2d()
    print()
    test_arc()
    print()
    test_polyline()
