from dataclasses import dataclass, field
from enum import Enum
import math
from vector3 import Vector3
from math_utils import get_block_index
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
    """
    name: str
    coord: Vector2 = field(default_factory=lambda: Vector2(0, 0))

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
        lastblock(float): 마지막 블록 측점
        block_interval(float): 블록 간격 default 25
        lastindex(float): 마지막 블록 인덱스
    """
    name: str
    curves: list[Curve] = None
    pitchs: list[Pitch] = None
    stations: list[Station] = None
    coords: list[Vector3] = None
    directions: list[Vector3] = None
    lastblock: float = 0.0
    block_interval: float = 25.0
    lastindex: float = 0.0

    def __post_init__(self):
        self.curves = self.curves or []
        self.pitchs = self.pitchs or []
        self.stations = self.stations or []
        self.coords = self.coords or []
        self.directions = self.directions or []
        # lastblock = 가장 큰 station 값
        if self.stations:
            self.lastblock = max(s.station for s in self.curves)
        else:
            self.lastblock = 0.0

        self.lastindex = get_block_index(self.lastblock, self.block_interval)

class CurveDirection(Enum):
    """
    곡선 방향 클래스.

    Attributes:
        LEFT (str): 좌향
        RIGHT (str): 우향
    """
    LEFT = '좌향'
    RIGHT = '우향'

class CurveType(Enum):
    """
    곡선 종류 클래스.

    Attributes:
        Simple (str): 원곡선
        Spiral (str): 완화곡선
        Complex (str): 복심곡선
    """
    Simple = '원곡선'
    Spiral = '완화곡선'
    Complex = '복심곡선'
    NONE = 'None'
@dataclass
class Segment:
    """
    공통 세그멘트 객체
    Attributes:
        start_sta (float): 시작 측점
        end_sta (float): 끝 측점
        start_coord (Vector2): 시작 좌표
        end_coord (Vector2): 끝 좌표
        start_azimuth (float): 시작 각도(라디안)
        end_azimuth (float): 종점 각도(라디안)
        length(float): 길이
    """
    start_sta: float = 0.0
    end_sta: float = 0.0
    start_coord: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    end_coord: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    start_azimuth: float = 0.0
    end_azimuth: float = 0.0
    length: float = 0.0

@dataclass
class StraightSegment(Segment):
    pass

@dataclass
class CurveSegment(Segment):
    """
    구간별 곡선 세그먼트 저장용 클래스 (단곡선).
    Attributes:
        radius(float): 원곡선 반경 R
        center_coord (Vector2): 원곡선 중심 좌표
        tl (float): 접선장(Tangent Length, TL)
        sl (float): 외할장(Chord Length, SL)
        m (float): 중앙종거(Middle Ordinate)

    """
    radius: float = 0.0
    center_coord: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    tl: float = 0.0
    sl: float = 0.0
    m: float = 0.0

@dataclass
class BasePoint:
    """
    공통 좌표정보 클래스
    Attributes:
        coord(Vector2): 좌표
    """
    coord: Vector2 = Vector2(x=0, y= 0)

@dataclass
class EndPoint(BasePoint):
    """
    BP/EP용 클래스 (BasePoint 상속)
    Attributes:
        direction(float): 방향각도(라디안)
    """
    direction: float = 0.0

@dataclass
class IPdata(BasePoint):
    """
    IP 정보 저장용 데이터 클래스(BasePoint) 상속.

    Attributes:
        ipno (int): IP 번호
        curvetype (CurveType): 곡선 종류
        curve_direction (CurveDirection): 곡선 방향
        radius (float): 곡선 반지름
        ia (float): 교각
        segment (CurveSegment): 세그먼트 정보 리스트
    """
    ipno: int = 0
    curvetype: CurveType = CurveType.Simple
    curve_direction: CurveDirection = CurveDirection.RIGHT
    radius: float | tuple[float,...] = 0.0
    ia: float = 0.0
    segment: list[CurveSegment] = field(default_factory=list)  # ⚡ 빈 리스트로 초기화