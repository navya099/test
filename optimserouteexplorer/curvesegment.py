from dataclasses import dataclass

from shapely.geometry import Point


@dataclass
class CurveSegment:
    bc_coord: Point
    ec_coord: Point
    center_coord: Point
    direction: int
    bc_sta: float
    ec_sta: float
    cl: float
    tl: float