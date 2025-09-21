from geometry import GeoMetry
import math

class Point3d(GeoMetry):
    def __init__(self, x, y, z):
        self.x: float = 0.0
        self.y: float = 0.0
        self.z: float = 0.0

    def move(self, angle: float, distance: float, new_z: float = None):

        self.x += distance * math.cos(angle)
        self.y += distance * math.sin(angle)
        if new_z is not None:
            self.z = new_z

    def moved(self, angle: float, distance: float, new_z: float = None):
        z = new_z if new_z is not None else self.z
        return Point3d(self.x + distance * math.cos(angle),
                       self.y + distance * math.sin(angle),
                       z)

    def distance_to(self, geoobject, option: str = '3d') -> float:
        dx = geoobject.x - self.x
        dy = geoobject.y - self.y
        dz = geoobject.z - self.z
        if option == '2d':
            return math.hypot(dx, dy)
        elif option == '3d':
            return math.sqrt(dx**2 + dy**2 + dz**2)
        else:
            raise ValueError("option must be '2d' or '3d'")

    def angle_to(self, geoobject, option: str = '2d'):
        dx = geoobject.x - self.x
        dy = geoobject.y - self.y
        dz = geoobject.z - self.z
        if option == '2d':
            return math.atan2(dy, dx)
        elif option == '3d':
            azimuth = math.atan2(dy, dx)
            horizontal_dist = math.hypot(dx, dy)
            elevation = math.atan2(dz, horizontal_dist)
            return azimuth, elevation
        else:
            raise ValueError("option must be '2d' or '3d'")

    def copy(self):
        return Point3d(self.x, self.y, self.z)

    def rotate(self, angle: float, origin=None):
        if origin is None:
            origin = self
        dx = self.x - origin.x
        dy = self.y - origin.y
        self.x = dx * math.cos(angle) - dy * math.sin(angle) + origin.x
        self.y = dx * math.sin(angle) + dy * math.cos(angle) + origin.y
        # z는 회전하지 않음 (XY 평면 기준)

    def rotate3d(self, angle: float, origin=None, axle='z'):
        if origin is None:
            origin = self

        dx = self.x - origin.x
        dy = self.y - origin.y
        dz = self.z - origin.z

        if axle == 'x':
            y_new = dy * math.cos(angle) - dz * math.sin(angle)
            z_new = dy * math.sin(angle) + dz * math.cos(angle)
            self.y = y_new + origin.y
            self.z = z_new + origin.z
        elif axle == 'y':
            x_new = dx * math.cos(angle) + dz * math.sin(angle)
            z_new = -dx * math.sin(angle) + dz * math.cos(angle)
            self.x = x_new + origin.x
            self.z = z_new + origin.z
        elif axle == 'z':
            x_new = dx * math.cos(angle) - dy * math.sin(angle)
            y_new = dx * math.sin(angle) + dy * math.cos(angle)
            self.x = x_new + origin.x
            self.y = y_new + origin.y
        else:
            raise ValueError("axle must be 'x', 'y', or 'z'")