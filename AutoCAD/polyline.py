from geometry import GeoMetry
from line import Line2d
from point2d import Point2d
from arc import Arc

class Polyline(GeoMetry):
    """
    연속된 점, 선, 호(Arc)를 연결한 복합 경로
    """
    def __init__(self, segments: list[GeoMetry] = None):
        self.segments = segments if segments else []
        self._current_index = 0  # 현재 vertex 인덱스

    @property
    def length(self):
        return sum(seg.length for seg in self.segments)

    @property
    def current_vertex_index(self) -> int:
        return self._current_index

    @property
    def current_vertex(self) -> Point2d:
        vertices = self._flatten_vertices()
        if not vertices:
            return None
        return vertices[self._current_index]

    def next_vertex(self):
        """다음 vertex로 이동"""
        vertices = self._flatten_vertices()
        if not vertices:
            return None
        self._current_index = (self._current_index + 1) % len(vertices)
        return self.current_vertex

    def previous_vertex(self):
        """이전 vertex로 이동"""
        vertices = self._flatten_vertices()
        if not vertices:
            return None
        self._current_index = (self._current_index - 1) % len(vertices)
        return self.current_vertex

    def _flatten_vertices(self) -> list[Point2d]:
        """Polyline의 모든 segment를 순회해서 점 리스트로 반환"""
        vertices = []
        for seg in self.segments:
            if isinstance(seg, Line2d):
                vertices.append(seg.start)
                vertices.append(seg.end)
            elif isinstance(seg, Arc):
                vertices.append(seg.start_point)
                vertices.append(seg.end_point)
        # 연속 중복 제거
        unique_vertices = [vertices[0]] if vertices else []
        for v in vertices[1:]:
            if v != unique_vertices[-1]:
                unique_vertices.append(v)
        return unique_vertices

    def add_vertex(self, point: Point2d, index: int = None):
        """
        새 vertex 추가
        1. index 지정 시 해당 위치에 삽입
        2. index 미지정 시 마지막에 추가
        기존 segment는 Line2d 기준으로 갱신
        """
        vertices = self._flatten_vertices()
        if index is None:
            vertices.append(point)
        else:
            if 0 <= index <= len(vertices):
                vertices.insert(index, point)
            else:
                raise IndexError("vertex index out of range")

        # vertices로 segments 재생성 (Line2d만)
        new_segments = []
        for i in range(len(vertices) - 1):
            new_segments.append(Line2d(vertices[i].copy(), vertices[i + 1].copy()))
        self.segments = new_segments
        # 새 vertex 선택
        self._current_index = index if index is not None else len(vertices) - 1
        return self.current_vertex

    def move(self, angle: float, distance: float):
        for seg in self.segments:
            seg.move(angle, distance)

    def moved(self, angle: float, distance: float):
        return Polyline([seg.moved(angle, distance) for seg in self.segments])

    def distance_to(self, point: Point2d) -> float:
        return min(seg.distance_to(point) for seg in self.segments)

    def angle_to(self, geoobject, option='rad') -> float:
        if self.segments:
            return self.segments[0].angle_to(geoobject, option)
        return 0.0

    def copy(self):
        return Polyline([seg.copy() for seg in self.segments])

    def rotate(self, angle: float, origin=None):
        for seg in self.segments:
            seg.rotate(angle, origin)

    def add_segment(self, segment: GeoMetry):
        self.segments.append(segment)
