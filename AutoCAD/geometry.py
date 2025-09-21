from abc import ABC, abstractmethod

class GeoMetry(ABC):
    """
    지오메트리 추상클래스
    """
    @abstractmethod
    def move(self, angle: float, distance: float):
        """객체를 이동"""
        pass

    @abstractmethod
    def moved(self, angle: float, distance: float):
        """이동된 새로운 객체 반환"""
        pass

    @abstractmethod
    def distance_to(self, geoobject) -> float:
        """두 객체 사이 거리"""
        pass

    @abstractmethod
    def angle_to(self, geoobject, option: str = 'rad') -> float:
        """객체 사이 각도"""
        pass

    @abstractmethod
    def copy(self):
        """객체 복사"""
        pass

    @abstractmethod
    def rotate(self, angle: float, origin=None):
        """객체 회전 (origin=None이면 자기 중심)"""
        pass
