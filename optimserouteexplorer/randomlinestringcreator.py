from shapely.geometry import Point, LineString
from optimserouteexplorer.util import calculate_angle
import random
import math

class RandomLineStringCreator:
    """
    랜덤 LineString객체 생성 클래스
    Attributes:
        linestring: LineString
    """
    def __init__(self):
        self.linestring = None

    def generate_random_linestring(self, start: Point, end: Point, num_max_point: int= 100,
                                   min_distance: float= 3000, max_distance: float =5000,min_end_distance: float=2000):
        """
        랜덤 LineString객체 생성 메소드
        Arguments:
            start: 시작 점 Point
            end: 끝점 Point
            num_max_point: 생성할 점 갯수
            min_distance: 점 사이의 최소 거리
            max_distance: 점 사이의 최대 거리
            min_end_distance: 끝점과 마지막점의 최소거리
        """
        points = [start]
        while True:
            if len(points) >= num_max_point:#최댓수를 넘으면 종료
                break
            new_point = self._generate_random_point_near(points[-1], end, min_distance, max_distance)
            if new_point.distance(points[-1]) <= max_distance: #점과 마지막점의 거리가 점 사이의 최대 거리보다 작은경우
                points.append(new_point)
            if new_point.distance(end) <= min_end_distance: #점과 끝점의 거리가 끝점과 마지막점의 최소거리보다 작은경우
                break
        points.append(end)

        self.linestring = LineString(points)

    def _generate_random_point_near(self, point: Point, end: Point,
                                    min_distance: float,
                                    max_distance: float
                                    ):
        """
        private  메소드
        기준점에서 랜덤 점 생성 메소드
        Arguments:
            point: 기준 점 Point
            end: 끝점 Point
            min_distance: 점 사이의 최소 거리
            max_distance: 점 사이의 최대 거리
        Returns:
            Point
        """
        #끝점 각도 계산

        angle_to_end = calculate_angle(point, end)
        while True:


            angle = random.uniform(angle_to_end - math.radians(90), angle_to_end + math.radians(90))
            distance = random.uniform(min_distance, max_distance)
            x = point.x + distance * math.cos(angle)
            y = point.y + distance * math.sin(angle)

            new_point = Point(x, y)

            # Check if the new point is in the direction of the end point
            if new_point.distance(end) < point.distance(end):
                return new_point