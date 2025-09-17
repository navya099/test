from dataclasses import dataclass

from math_utils import get_block_index
from model.bvetrack import Curve, Pitch, Station
from vector3 import Vector3


@dataclass
class BVERouteData:
    """
    BVE 루트 정보 저장용 데이터 클래스.

    Attributes:
        name (str): 루트 이름
        curves (list[Curve]): 곡선 저장 리스트
        pitchs (list[Pitch]): 구배 저장 리스트
        stations (list[Station]): 정거장 저장 리스트
        coords (list(Vector3): 좌표 리스트
        directions (list(Vector3): 방향벡터 3차원 리스트
        firstblock(float): 처음 블록 측점
        lastblock(float): 마지막 블록 측점
        block_interval(float): 블록 간격 default 25
        firstindex(int): 처음 블록 인덱스
        lastindex(int): 마지막 블록 인덱스
    """
    name: str
    curves: list[Curve] = None
    pitchs: list[Pitch] = None
    stations: list[Station] = None
    coords: list[Vector3] = None
    directions: list[Vector3] = None
    firstblock: float = 0.0
    lastblock: float = 0.0
    block_interval: float = 25.0
    firstindex: int = 0
    lastindex: int = 0

    def __post_init__(self):
        self.curves = self.curves or []
        self.pitchs = self.pitchs or []
        self.stations = self.stations or []
        self.coords = self.coords or []
        self.directions = self.directions or []

        # lastblock = 가장 큰 station 값
        if self.stations:
            self.firstblock = self.curves[0].station
            self.lastblock = max(s.station for s in self.curves)
        else:
            self.firstblock = 0.0
            self.lastblock = 0.0

        self.firstindex = get_block_index(self.firstblock, self.block_interval)
        self.lastindex = get_block_index(self.lastblock, self.block_interval)