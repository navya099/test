import math

class Vector2:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def rotate(self, cosine_of_angle, sine_of_angle):
        x_new = cosine_of_angle * self.x - sine_of_angle * self.y
        y_new = sine_of_angle * self.x + cosine_of_angle * self.y
        self.x, self.y = x_new, y_new

    def __str__(self):
        return f"({self.x}, {self.y})"

class Vector3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"

class Transformation:
    def __init__(self, yaw, pitch, roll):
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll

    def rotate_vector(self, vector):
        """Rotate a 2D vector by the yaw angle."""
        cos_yaw = math.cos(self.yaw)
        sin_yaw = math.sin(self.yaw)
        vector.rotate(cos_yaw, sin_yaw)
        return vector

# Given data
class Data:
    BlockInterval = 450.0

class WorldTrackElement:
    CurveRadius = -250.0

Data.Blocks = [{'Pitch': 0}]
Direction = Vector2(0, 1)
Position = Vector3(0, 0, 350)

# Initialize values
a = 0.0
c = Data.BlockInterval
h = 0.0

# Conditions and calculations
if WorldTrackElement.CurveRadius != 0.0 and Data.Blocks[0]['Pitch'] != 0.0:
    d = Data.BlockInterval
    p = Data.Blocks[0]['Pitch']
    r = WorldTrackElement.CurveRadius
    s = d / math.sqrt(1.0 + p * p)
    h = s * p
    b = s / abs(r)
    c = math.sqrt(2.0 * r * r * (1.0 - math.cos(b)))
    a = 0.5 * math.copysign(1, r) * b
    direction_transformation = Transformation(-a, 0.0, 0.0)
    Direction = direction_transformation.rotate_vector(Direction)
elif WorldTrackElement.CurveRadius != 0.0:
    d = Data.BlockInterval
    r = WorldTrackElement.CurveRadius
    b = d / abs(r)
    c = math.sqrt(2.0 * r * r * (1.0 - math.cos(b)))
    a = 0.5 * math.copysign(1, r) * b
    direction_transformation = Transformation(-a, 0.0, 0.0)
    Direction = direction_transformation.rotate_vector(Direction)
elif Data.Blocks[0]['Pitch'] != 0.0:
    p = Data.Blocks[0]['Pitch']
    d = Data.BlockInterval
    c = d / math.sqrt(1.0 + p * p)
    h = c * p

# Calculate TrackYaw and TrackPitch
TrackYaw = math.atan2(Direction.x, Direction.y)
TrackPitch = math.atan(Data.Blocks[0]['Pitch'])

print(f'd = {d}')
print(f'r = {r}')
print(f'b = {b}')
print(f'c = {c}')
print(f'a = {a}')
print(f'Track Yaw: {TrackYaw}')
print(f'Track Pitch: {TrackPitch}')
print(f'Direction: {Direction}')

# Update Position
Position.x += Direction.x * c
Position.y += h
Position.z += Direction.y * c

if a != 0.0:
    direction_transformation = Transformation(-a, 0.0, 0.0)
    Direction = direction_transformation.rotate_vector(Direction)

print(f'Updated Position: {Position}')
