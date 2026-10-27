import math
from .geometry import GeoMetry
from .point2d import Point2d

class BulgeSegment(GeoMetry):
    def __init__(self, start: Point2d, end: Point2d, bulge: float = 0.0):
        self.start = start
        self.end = end
        self.bulge = bulge

    @property
    def radius(self):
        if self.bulge == 0:
            return None
        else:
            # 반지름
            return self.chord / (2 * math.sin(abs(self.theta) / 2))

    @property
    def center(self):
        if self.bulge == 0:
            return None
        # chord 중점
        mid = Point2d((self.start.x + self.end.x) / 2,
                      (self.start.y + self.end.y) / 2)
        # chord 방향
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        chord_angle = math.atan2(dy, dx)
        # bulge 부호에 따라 수직 방향 결정
        perp_angle = chord_angle + (math.pi / 2 if self.bulge > 0 else -math.pi / 2)
        # 중심 좌표
        offset = math.sqrt(self.radius ** 2 - (self.chord / 2) ** 2)
        return mid.moved(perp_angle, offset)

    @property
    def start_angle(self):
        if self.center is None:
            return None
        return math.atan2(self.start.y - self.center.y,
                          self.start.x - self.center.x)

    @property
    def end_angle(self):
        if self.center is None:
            return None
        return math.atan2(self.end.y - self.center.y,
                          self.end.x - self.center.x)

    # chord 길이와 중심각
    @property
    def chord(self):
        return self.start.distance_to(self.end)

    @property
    def theta(self):
        return 4 * math.atan(self.bulge)

    @property
    def length(self):
        if self.bulge == 0:
            return self.chord
        else:
            return abs(self.radius * self.theta)

    def move(self, angle: float, distance: float):
        self.start.move(angle, distance)
        self.end.move(angle, distance)

    def moved(self, angle: float, distance: float):
        new_start = self.start.moved(angle, distance)
        new_end = self.end.moved(angle, distance)
        return BulgeSegment(new_start, new_end, self.bulge)

    def copy(self):
        return BulgeSegment(self.start.copy(), self.end.copy(), self.bulge)

    def distance_to(self, point: Point2d) -> float:
        if self.bulge == 0:
            # 직선 거리
            dx = self.end.x - self.start.x
            dy = self.end.y - self.start.y
            if dx == dy == 0:
                return self.start.distance_to(point)
            t = ((point.x - self.start.x) * dx + (point.y - self.start.y) * dy) / (dx * dx + dy * dy)
            t = max(0, min(1, t))
            proj_x = self.start.x + t * dx
            proj_y = self.start.y + t * dy
            return math.hypot(point.x - proj_x, point.y - proj_y)
        else:
            # 호 거리
            dist_to_center = self.center.distance_to(point)
            angle_p = math.atan2(point.y - self.center.y, point.x - self.center.x)

            # 호 범위 안에 있는지 확인
            def angle_in_range(a, start, end):
                a = (a + 2 * math.pi) % (2 * math.pi)
                start = (start + 2 * math.pi) % (2 * math.pi)
                end = (end + 2 * math.pi) % (2 * math.pi)
                if start < end:
                    return start <= a <= end
                else:
                    return a >= start or a <= end

            if angle_in_range(angle_p, self.start_angle, self.end_angle):
                return abs(dist_to_center - self.radius)
            else:
                return min(self.start.distance_to(point), self.end.distance_to(point))

    def angle_to(self, point: Point2d, option: str = 'rad') -> float:
        dx = point.x - self.start.x
        dy = point.y - self.start.y
        angle = math.atan2(dy, dx)
        if option == 'deg':
            return math.degrees(angle)
        return angle

    def rotate(self, angle: float, origin=None):
        if origin is None:
            origin = self.center if self.center else Point2d(0, 0)
        self.start.rotate(angle, origin)
        self.end.rotate(angle, origin)