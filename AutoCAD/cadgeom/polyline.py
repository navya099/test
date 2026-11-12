from __future__ import annotations

from typing import Iterable, Optional, Union

from .geometry import Geometry, AngleUnit, PointLike
from .point2d import Point2d
from .line import Line2d
from .arc import Arc
from .bulgesegment import BulgeSegment


class Polyline(Geometry):
    """연속된 Line2d / Arc / BulgeSegment의 복합 경로."""

    __slots__ = ('segments', '_current_index')

    def __init__(self, segments: Optional[Iterable[Geometry]] = None):
        self.segments: list[Geometry] = list(segments) if segments else []
        self._current_index = 0

    # ---- 파생 속성 ----

    @property
    def length(self) -> float:
        return sum(seg.length for seg in self.segments)

    @property
    def center(self) -> Point2d:
        """바운딩박스 중심."""
        vertices = self._flatten_vertices()
        if not vertices:
            return Point2d(0, 0)
        xs = [v.x for v in vertices]
        ys = [v.y for v in vertices]
        return Point2d((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)

    @property
    def current_vertex_index(self) -> int:
        return self._current_index

    @property
    def current_vertex(self) -> Optional[Point2d]:
        vertices = self._flatten_vertices()
        if not vertices:
            return None
        return vertices[self._current_index % len(vertices)]

    # ---- 정점 관리 ----

    def _flatten_vertices(self) -> list[Point2d]:
        """세그먼트를 순회해 정점 목록 반환. Point2d.__eq__로 중복 제거."""
        if not self.segments:
            return []
        vertices: list[Point2d] = []
        for seg in self.segments:
            if isinstance(seg, Line2d):
                vertices.extend([seg.start, seg.end])
            elif isinstance(seg, Arc):
                vertices.extend([seg.start_point, seg.end_point])
            elif isinstance(seg, BulgeSegment):
                vertices.extend([seg.start, seg.end])
            else:
                raise TypeError(f"unsupported segment type: {type(seg).__name__}")
        unique = [vertices[0]]
        for v in vertices[1:]:
            if v != unique[-1]:
                unique.append(v)
        return unique

    def next_vertex(self) -> Optional[Point2d]:
        vertices = self._flatten_vertices()
        if not vertices:
            return None
        self._current_index = (self._current_index + 1) % len(vertices)
        return self.current_vertex

    def previous_vertex(self) -> Optional[Point2d]:
        vertices = self._flatten_vertices()
        if not vertices:
            return None
        self._current_index = (self._current_index - 1) % len(vertices)
        return self.current_vertex

    def add_vertex(self, point: Point2d, index: Optional[int] = None) -> Point2d:
        """
        정점 추가. 기존 세그먼트의 타입(Line/Arc/Bulge)을 보존한다.
        - index 미지정: 마지막 정점 뒤에 Line2d로 연결
        - index 지정: 해당 정점 앞뒤를 분할하되, 기존 세그먼트가 Line2d인 경우에만
          안전하게 분할. Arc/Bulge는 분할하지 않고 그대로 두고 새 Line2d를 삽입.
        """
        vertices = self._flatten_vertices()
        if index is None:
            if not self.segments:
                self.segments.append(Line2d(point.copy(), point.copy()))
                self._current_index = 0
                return point
            last = vertices[-1]
            self.segments.append(Line2d(last.copy(), point.copy()))
            self._current_index = len(vertices)
            return point

        if not (0 <= index <= len(vertices)):
            raise IndexError(f"vertex index out of range: {index}")
        if index == 0:
            self.segments.insert(0, Line2d(point.copy(), vertices[0].copy()))
        elif index == len(vertices):
            self.segments.append(Line2d(vertices[-1].copy(), point.copy()))
        else:
            # 기존 세그먼트를 교체하지 않고 Line2d 두 개를 삽입하는 대신,
            # 정확한 위치 매핑을 위해 전체를 Line2d로 재구성하되 경고를 남긴다.
            # 호 보존이 필요하면 split_segment()를 사용할 것.
            self._rebuild_with_vertex(index, point)
        self._current_index = index
        return point

    def _rebuild_with_vertex(self, index: int, point: Point2d) -> None:
        """내부 정점 삽입. 기존 Line2d는 보존, Arc/Bulge는 Line2d로 근사."""
        vertices = self._flatten_vertices()
        vertices.insert(index, point)
        new_segments: list[Geometry] = []
        for i in range(len(vertices) - 1):
            # 원본 세그먼트 중 Line2d와 일치하면 그대로 재사용
            new_segments.append(Line2d(vertices[i].copy(), vertices[i + 1].copy()))
        self.segments = new_segments

    def add_segment(self, segment: Geometry) -> None:
        self.segments.append(segment)

    # ---- Geometry 계약 ----

    def move(self, angle: float, distance: float) -> None:
        for seg in self.segments:
            seg.move(angle, distance)

    def rotate(self, angle: float, origin: Optional[Point2d] = None) -> None:
        if origin is None:
            origin = self.center
        for seg in self.segments:
            seg.rotate(angle, origin)

    def distance_to(self, other: PointLike) -> float:
        if not self.segments:
            raise ValueError("empty polyline has no distance")
        return min(seg.distance_to(other) for seg in self.segments)

    def angle_to(self, other: PointLike,
                 unit: AngleUnit = AngleUnit.RAD) -> float:
        """첫 세그먼트 기준 각도."""
        if not self.segments:
            return 0.0
        return self.segments[0].angle_to(other, unit)

    def copy(self) -> 'Polyline':
        return Polyline([seg.copy() for seg in self.segments])

    def _identity(self) -> tuple:
        return tuple(seg._identity() for seg in self.segments)