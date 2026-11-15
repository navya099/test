import math
from abc import ABC, abstractmethod


# ==============================================================================
# 1. 기하 요소 공통 추상 클래스 (Base Interface)
# ==============================================================================
class AlignmentEntity(ABC):
    def __init__(self, start_e: float, start_n: float, start_angle: float, start_sta: float, length: float):
        self.start_e = float(start_e)
        self.start_n = float(start_n)
        self.start_angle = float(start_angle)  # 동쪽=0, 반시계 방향 라디안
        self.start_sta = float(start_sta)
        self.length = float(length)
        self.end_sta = self.start_sta + self.length

    @property
    @abstractmethod
    def end_pose(self):
        """요소 끝점의 (end_easting, end_northing, end_angle_rad, end_station) 반환"""
        pass

    @abstractmethod
    def point_location(self, station: float, offset: float = 0.0):
        """글로벌 측점(station)과 이격거리(offset) -> 글로벌 (Easting, Northing)"""
        pass

    @abstractmethod
    def station_offset(self, easting: float, northing: float):
        """글로벌 (Easting, Northing) -> (station, signed_offset, proj_e, proj_n) 또는 None"""
        pass



