import math

class Vector2:
    """
    2d 벡터 클래스.
    Attributes:
        x (flaot): x
        y (float): y
    """
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def rotate(self, cosine_of_angle, sine_of_angle):
        x_new = cosine_of_angle * self.x - sine_of_angle * self.y
        y_new = sine_of_angle * self.x + cosine_of_angle * self.y
        self.x, self.y = x_new, y_new

    def copy(self):
        return Vector2(self.x, self.y)

    def todegree(self) -> float:
        """벡터의 방향을 degree 단위로 반환 (0°=+X, 반시계 증가)."""
        return math.degrees(math.atan2(self.y, self.x))

    def toradian(self) -> float:
        """벡터의 방향을 라디안 단위로 반환 (0°=+X, 반시계 증가)."""
        return math.atan2(self.y, self.x)