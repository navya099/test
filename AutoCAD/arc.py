from AutoCAD.geometry import GeoMetry
from AutoCAD.point2d import Point2d
import math

class Arc(GeoMetry):
    """
    2D호(Arc) 클래스
    Attributes:
        center: 원 중심(Point2d)
        radius: 반지름(float)
        start_angle: 시작각도(라디안)
        end_angle: 끝각도(라디안)
    """
    def __init__(self, center: Point2d, radius: float, start_angle: float, end_angle: float):
        self.center = center
        self.radius = radius
        self.start_angle = start_angle
        self.end_angle = end_angle

    @property
    def start_point(self) -> Point2d:
        """시작점 좌표"""
        return Point2d(
            self.center.x + self.radius * math.cos(self.start_angle),
            self.center.y + self.radius * math.sin(self.start_angle)
        )

    @property
    def end_point(self) -> Point2d:
        """끝점 좌표"""
        return Point2d(
            self.center.x + self.radius * math.cos(self.end_angle),
            self.center.y + self.radius * math.sin(self.end_angle)
        )

    @property
    def mid_point(self) -> Point2d:
        """호 중간점 좌표"""
        mid_angle = (self.start_angle + self.end_angle) / 2
        return Point2d(
            self.center.x + self.radius * math.cos(mid_angle),
            self.center.y + self.radius * math.sin(mid_angle)
        )
    @property
    def total_aangle(self):
        return self.start_angle + self.end_angle

    @property
    def length(self) -> float:
        """호 길이"""
        return abs(self.end_angle - self.start_angle) * self.radius

    @property
    def chord_length(self) -> float:
        """현 길이"""
        dx = self.end_point.x - self.start_point.x
        dy = self.end_point.y - self.start_point.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def move(self, angle: float, distance: float):
        """호 전체 이동"""
        self.center.move(angle, distance)

    def moved(self, angle: float, distance: float):
        """이동된 새로운 Arc 객체 반환"""
        new_center = self.center.moved(angle, distance)
        return Arc(new_center, self.radius, self.start_angle, self.end_angle)

    def distance_to(self, point: Point2d) -> float:
        """점과 호 사이 거리 (중심-점 거리 - 반지름)"""
        dist_to_center = self.center.distance_to(point)
        return abs(dist_to_center - self.radius)

    def angle_to(self, geoobject, option: str = 'rad') -> float:
        """호의 시작점에서 geoobject까지 각도 (라디안 또는 도)"""
        start_point = Point2d(
            self.center.x + self.radius * math.cos(self.start_angle),
            self.center.y + self.radius * math.sin(self.start_angle)
        )
        dx = geoobject.x - start_point.x
        dy = geoobject.y - start_point.y
        angle = math.atan2(dy, dx)
        if option == 'deg':
            return math.degrees(angle)
        return angle

    def copy(self):
        return Arc(self.center.copy(), self.radius, self.start_angle, self.end_angle)

    def rotate(self, angle: float, origin=None):
        """호 회전"""
        if origin is None:
            origin = self.center
        self.center.rotate(angle, origin)
        self.start_angle += angle
        self.end_angle += angle
