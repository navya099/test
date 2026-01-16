
import math
from point2d import Point2d
from point3d import Point3d
from geometry import GeoMetry  # 기존 추상 클래스

class Line3d(GeoMetry):
    """
    3d선 클래스: 시작점과 끝점을 갖는 객체
    """
    def __init__(self, start: Point3d, end: Point3d):
        self.start = start
        self.end = end
    @property
    def length(self):
        return self.start.distance_to(self.end,option='3d')
    @property
    def direction(self):
        return math.atan2(self.end.y - self.start.y, self.end.x - self.start.x)


    # GeoMetry 추상 메소드 구현
    def move(self, angle: float, distance: float):
        self.start.move(angle, distance)
        self.end.move(angle, distance)

    def moved(self, angle: float, distance: float):
        return Line3d(self.start.moved(angle, distance), self.end.moved(angle, distance))

    def distance_to(self, line: 'Line3d') -> float:
        # self와 line 사이 최소 거리 계산
        d1 = self.distance_to_point(line.start)
        d2 = self.distance_to_point(line.end)
        d3 = line.distance_to_point(self.start)
        d4 = line.distance_to_point(self.end)
        return min(d1, d2, d3, d4)

    def distance_to_point(self, point: Point2d) -> float:
        # 점과 선 사이 거리 (2D 평면 기준)
        # 벡터 수학 활용
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        if dx == dy == 0:
            return self.start.distance_to(point)
        t = ((point.x - self.start.x) * dx + (point.y - self.start.y) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        proj_x = self.start.x + t * dx
        proj_y = self.start.y + t * dy
        return ((point.x - proj_x) ** 2 + (point.y - proj_y) ** 2) ** 0.5

    def angle_to(self, geoobject, option: str = 'rad') -> float:
        # 선의 방향 각도
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        angle = math.atan2(dy, dx)
        if option == 'deg':
            return math.degrees(angle)
        return angle

    def copy(self):
        return Line3d(self.start.copy(), self.end.copy())

    def rotate(self, angle: float, origin=None):
        if origin is None:
            # 중심점: 선의 중점
            origin = Point2d(
                (self.start.x + self.end.x) / 2,
                (self.start.y + self.end.y) / 2,
            )
        self.start.rotate(angle, origin)
        self.end.rotate(angle, origin)