from point3d import Point3d
from Electric.Overhead.Pole.poletype import PoleType
from Electric.Overhead.Structure.beam import Beam
from curvedirection import CurveDirection

class Pole:
    """
    전주 정의 클래스
    Attributes:
        name: 전주이름
        station: 측점
        position: 전주 좌표
        poletype: 전주타입
        beam: 빔 객체
        gauge: 건식게이지
        direction: 전주 방향
    """
    def __init__(self):
        self.name = ''
        self.station = 0.0

        self.position: Point3d = Point3d(0.0, 0.0, 0.0)
        self.poletype: PoleType = PoleType.PIPE
        self.beam: Beam | None = None
        self.gauge: float = 0.0

        self.direction: CurveDirection = CurveDirection.RIGHT