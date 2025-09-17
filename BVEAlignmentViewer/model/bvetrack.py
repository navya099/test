from dataclasses import dataclass, field
from vector2 import Vector2

@dataclass
class BVETrack:
    """
    BVE 정보 저장용 데이터 클래스.
    Attributes:
        station (float): 블록 시점 측점
    """
    station: float

@dataclass
class Curve(BVETrack):
    """
    BVE 곡선 저장용 데이터 클래스.
        radius (float): 블록 곡선반경 R
        cant (float): 블록 캔트
        direction(flaot): 블록 방향각
    """
    radius: float
    cant: float
    coord: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    direction: float = 0

@dataclass
class Pitch(BVETrack):
    """
    BVE 구배 정보 저장용 데이터 클래스.
    Attributes:
        pitch (float): 블록 pitch
    """
    pitch: float

@dataclass
class Station(BVETrack):
    """
    BVE 정거장 정보 저장용 데이터 클래스.

    Attributes:
        name (str): 정거장 이름
        direction(flaot): 블록 방향각
    """
    name: str
    coord: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    direction: float = 0