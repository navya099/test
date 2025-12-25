from abc import ABC, abstractmethod
from AutoCAD.point2d import Point2d


class SegmentGeometry(ABC):
    """공통 지오메트리 엔진 추상 클래스(직선,단곡선,완화곡선 지원)"""

    @abstractmethod
    def tangent_at(self, s: float) -> float:
        """s에서의 방위각"""
        pass

    @abstractmethod
    def point_at(self, s: float, offset: float = 0.0) -> Point2d:
        """s에서의 좌표"""
        pass

    @abstractmethod
    def distance_at(self, p: Point2d) -> float:
        """p에서의 거리"""
        pass

    @abstractmethod
    def project_at(self, p: Point2d) -> tuple[Point2d, float]:
        """p에서의 투영점"""
        pass

    @abstractmethod
    def reversed(self):
        """지오메트리 뒤집기"""
        pass

    @abstractmethod
    def get_offset(self, offset: float):
        """지오메트리 오프셋"""
        pass


