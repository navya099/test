from dataclasses import dataclass, field

from shapely import LineString

from core.util import route_length, haversine


@dataclass
class Alignment:
    """
    노선 후보 표현체.

    NOTE: 현재 미사용. 추후 GA 결과 표현을 dict → Alignment 로 통합 예정.
          (core/generate_routes.py 레거시 파이프라인 제거로 현재 참조 없음)
    """
    linestring: LineString = LineString()
    coords: list = field(default_factory=list)
    elevations: list = field(default_factory=list)
    grounds: list = field(default_factory=list)
    fls: list = field(default_factory=list)
    bridges: dict = field(default_factory=dict)  # key: segment idx, value: 튜플(start,end)
    tunnels: dict = field(default_factory=dict)
    cost: float = 0.0
    radius: list = field(default_factory=list)
    grades: list = field(default_factory=list)
    score: float = 0.0
    fitness: float = 0.0

    @property
    def length(self):
        return self.linestring.length

    @property
    def bridge_count(self):
        return len(self.bridges)
    @property
    def tunnel_count(self):
        return len(self.tunnels)

    @property
    def total_bridge_length(self):
        return sum([sum(haversine(self.coords[i], self.coords[i + 1]) for i in range(s, e))
                    for s, e in self.bridges.values()])

    @property
    def total_tunnel_length(self):
        return sum([sum(haversine(self.coords[i], self.coords[i + 1]) for i in range(s, e))
                    for s, e in self.tunnels.values()])
    @property
    def radius_count(self):
        return len(self.radius)
    @property
    def grades_count(self):
        return len(self.fls)
    @property
    def max_grade(self):
        return max(self.grades)
    @property
    def min_radius(self):
        return min(self.radius)