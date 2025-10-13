from shapely.geometry import LineString, Point
import numpy as np
from optimserouteexplorer.util import draw_arc

class LineStringProcessor:
    """
    LineString객체 처리용 클래스
    Attributes:
        linestring: LineString
        angles: LineString 내부 각도 리스트
    """
    def __init__(self, linestring: LineString):
        self.linestring = linestring
        self.angles: list[float] = []

    def process_linestring(self):
        """
        LineString객체 처리용 메소드
        각도 산출 후 조정 후 변경 LineString로 수정
        """
        self._calculate_angles()
        self._adjust_linestring()
        self._calculate_angles()
    def _adjust_linestring(self, tolerance: float = 60):
        """
        private 메소드
        LineString객체를 각도 조정
        Args:
            tolerance: 임계각도
        """
        new_points = [self.linestring.coords[0]]  # Start with the first point
        for i in range(1, len(self.linestring.coords) - 1):
            if self.angles[i - 1] <= tolerance: #tolerance 임계값보다 작으면
                new_points.append(self.linestring.coords[i])
        new_points.append(self.linestring.coords[-1])  # End with the last point
        self.linestring = LineString(new_points)

    def _calculate_angles(self):
        """
        LineString 객체 내부 각도 계산 (간결한 버전, numpy 사용)
        """
        coords = np.array(self.linestring.coords)
        # 이전 벡터와 다음 벡터 계산
        vectors_prev = coords[1:-1] - coords[:-2]  # P[i] - P[i-1]
        vectors_next = coords[2:] - coords[1:-1]  # P[i+1] - P[i]

        # 벡터 길이 계산 (0인 경우 방지)

        norms_prev = np.linalg.norm(vectors_prev, axis=1)
        norms_next = np.linalg.norm(vectors_next, axis=1)
        valid = (norms_prev > 0) & (norms_next > 0)

        # 내적을 통한 각도 계산
        dot_products = np.einsum('ij,ij->i', vectors_prev[valid], vectors_next[valid])
        cos_angles = dot_products / (norms_prev[valid] * norms_next[valid])
        cos_angles = np.clip(cos_angles, -1.0, 1.0)  # 부동소수점 오차 방지
        angles = np.degrees(np.arccos(cos_angles))

        self.angles = angles.tolist()

    def create_joined_line_and_arc_linestirng(self,
                                 start_points: list[Point],
                                 end_points: list[Point],
                                 center_points: list[Point],
                                 direction_list: list[int]):
        """
        public 메소드
        선과 호를 이어서 새로운 linestring생성
        Args:
            start_points: 호의 시작 좌표 리스트
            end_points: 호의 끝 좌표 리스트
            center_points: 호의 중심 좌표 리스트
            direction_list: 각 호의 방향 리스트(1,0, -1)
        """
        # 호 리스트 생성
        acr1, acr2 = [], []
        for i in range(len(start_points)):

            x_arc, y_arc = draw_arc(direction_list[i], start_points[i], end_points[i], center_points[i])
            acr1.append(x_arc)
            acr2.append(y_arc)

        acr1 = [item for sublist in acr1 for item in sublist]
        acr2 = [item for sublist in acr2 for item in sublist]
        curve_coords = list(zip(acr1, acr2))
        combined_coords = [self.linestring.coords[0]] + curve_coords + [self.linestring.coords[-1]]
        new_linestring = LineString(combined_coords)

        self.linestring = new_linestring

    def resample_linestring(self, interval: float = 40):
        """
        linestring을 일정 간격으로 재생성
        Args:
            interval: 재샘플링 간격
        Returns:
            새로운 LineString
        """
        if self.linestring is None or len(self.linestring.coords) < 2:
            return

        new_points = [Point(self.linestring.coords[0])]
        total_length = 0

        for i in range(1, len(self.linestring.coords)):
            p0 = Point(self.linestring.coords[i-1])
            p1 = Point(self.linestring.coords[i])
            segment_length = p0.distance(p1)
            direction = ((p1.x - p0.x) / segment_length, (p1.y - p0.y) / segment_length)

            d = interval - total_length
            while d < segment_length:
                new_x = p0.x + direction[0] * d
                new_y = p0.y + direction[1] * d
                new_points.append(Point(new_x, new_y))
                d += interval
            total_length = segment_length + total_length - interval * int((segment_length + total_length) / interval)

        new_points.append(Point(self.linestring.coords[-1]))
        self.linestring = LineString(new_points)