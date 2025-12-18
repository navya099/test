from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from typing import Self

from AutoCAD.point2d import Point2d
from curvetype import CurveType

@dataclass
class Segment(ABC):
    """
    공통 추상 세그멘트 객체
    Attributes:
        prev_index(int): 이전 세그먼트 인덱스
        current_index(int): 현재 세그먼트 인덱스
        next_index(int): 다음 세그먼트 인덱스
        start_sta (float): 시작 측점
        end_sta (float): 끝 측점
        type(CurveType): 세그먼트 타입(직선 ,곡선 ,완화곡선)
    """
    prev_index: int = 0
    current_index: int = 0
    next_index: int = 0
    start_sta: float = 0.0
    end_sta: float = 0.0
    type: CurveType = CurveType.NONE

    @abstractmethod
    def distance_to_point(self, point: Point2d) -> float:
        """세그먼트와 점의 거리 계산"""
        pass

    @abstractmethod
    def point_at_station(self, station: float, offset: float) -> tuple[Point2d, float]:
        """지정한 측점의 좌표와 방위각 반환"""
        pass

    @abstractmethod
    def station_at_point(self, coord: Point2d) -> tuple[float, float]:
        """지정한 좌표의 측점 및 거리 반환"""
        pass

    @abstractmethod
    def is_contains_station(self, station: float) -> bool:
        """지정한 측점이 세그먼트에 포함되는지 여부"""
        pass

    @abstractmethod
    def is_contains_point(self, point: Point2d) -> bool:
        """지정한 점이 세그먼트에 포함되는지 여부"""
        pass

    @abstractmethod
    def reverse(self):
        """세그먼트 뒤집기"""
        pass

    @abstractmethod
    def create_offset(self, offset_distance: float) -> Self:
        """세그먼트 객체의 평행(오프셋) 복제본을 생성"""
        pass

    @abstractmethod
    def split_to_segment(self, coord: Point2d) -> Self:
        """지점한 점으로 세그먼트 객체 분할"""
        pass