from geometry import GeoMetry
import math

class Point2d(GeoMetry):
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def move(self, angle, distance):

        self.x += distance * math.cos(angle)
        self.y += distance * math.sin(angle)

    def moved(self, angle, distance):
        return Point2d(self.x + distance * math.cos(angle),
                       self.y + distance * math.sin(angle))

    def distance_to(self, geoobject):
        return math.hypot(geoobject.x - self.x, geoobject.y - self.y)

    def angle_to(self, geoobject, option='rad'):
        angle = math.atan2(geoobject.y - self.y, geoobject.x - self.x)
        if option == 'deg':
            return math.degrees(angle)
        return angle

    def copy(self):
        return Point2d(self.x, self.y)

    def rotate(self, angle, origin=None):
        if origin is None:
            origin = self
        dx = self.x - origin.x
        dy = self.y - origin.y
        self.x = dx * math.cos(angle) - dy * math.sin(angle) + origin.x
        self.y = dx * math.sin(angle) + dy * math.cos(angle) + origin.y
