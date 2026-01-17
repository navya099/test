from dataclasses import dataclass

from shapely.geometry import Point

from curvedirection import CurveDirection


@dataclass
class CurveSegment:
    bc_coord: Point
    ec_coord: Point
    center_coord: Point
    direction: CurveDirection.NULL
    bc_sta: float
    ec_sta: float
    cl: float
    tl: float
    radius: float
