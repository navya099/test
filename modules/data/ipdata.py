from dataclasses import field, dataclass
from typing import Self

from point2d import Point2d

@dataclass
class PIData:
    """PI데이터 클래스
    Attributes:
        index: pi인덱스
        coord: pi좌표
        radius: R
        group_id: pi가 참조하는 그룹 id
        prev_pi_index: 이전 pi인덱스
        next_pi_index: 다음 pi인덱스
    """
    index: int | None = None
    coord: Point2d = field(default_factory=lambda: Point2d(0, 0))
    radius: float = 0.0
    group_id: str | None = None
    prev_pi_index: int | None = None
    next_pi_index: int | None = None

    def has_prev(self) -> bool:
        return self.prev_pi_index is not None

    def has_next(self) -> bool:
        return self.next_pi_index is not None

    def distance_to(self, point: Point2d) -> float:
        """해당 PI 좌표와 주어진 좌표 간 거리"""
        return self.coord.distance_to(point)

    def link_prev_next(self, prev_index: int | None, next_index: int | None):
        """이전/다음 PI 인덱스 갱신"""
        self.prev_pi_index = prev_index
        self.next_pi_index = next_index

    def assign_group(self, group_id: str | None):
        """PI가 속한 그룹 ID 지정"""
        self.group_id = group_id

    def is_linked(self) -> bool:
        """PI가 이전 또는 다음과 연결되어 있는지 여부"""
        return self.has_prev() or self.has_next()

    def closer_to(self, point: Point2d, other: Self) -> bool:
        """주어진 포인트에 더 가까운 PI 비교"""
        return self.distance_to(point) < other.distance_to(point)

