from enum import Enum

class CoordinateSystem(Enum):
    """좌표계 정의
    Attributes:
        OPENBVE: x,y,z(y=높이)
        WORLD: x,y,z(z=높이)
    """
    OPENBVE = "OPENBVE"
    WORLD = "world"