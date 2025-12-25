
import math
from dataclasses import dataclass, field

from AutoCAD.point2d import Point2d
from data.alignment.geometry.segmentgeometry import SegmentGeometry
from math_utils import calculate_bearing, calculate_distance

@dataclass
class StraightGeometry(SegmentGeometry):
    """직선 지오메트리 엔진
    Attributes:
        start_coord:시작 좌표
        end_coord:끝 좌표
    """
    start_coord: Point2d = field(default_factory=lambda: Point2d(0, 0))
    end_coord: Point2d = field(default_factory=lambda: Point2d(0, 0))

    @property
    def length(self) -> float:
        """길이"""
        return calculate_distance(self.start_coord, self.end_coord)

    def tangent_at(self, s: float) -> float:
        return calculate_bearing(self.start_coord, self.end_coord)

    def point_at(self, s: float, offset: float = 0.0) -> Point2d:
        az = self.tangent_at(s)
        pt = self.start_coord.moved(az, s)
        if offset < 0:
            pt.move(az + math.pi / 2, offset)
        else:
            pt.move(az - math.pi / 2, offset)
        return pt

    def distance_at(self, p: Point2d) -> float:
        _ ,off = self.project_at(p)
        return abs(off)

    def project_at(self,p: Point2d) -> tuple[Point2d, float]:
        ax, ay = self.start_coord.x, self.start_coord.y
        bx, by = self.end_coord.x, self.end_coord.y
        px, py = p.x, p.y

        dx, dy = bx - ax, by - ay
        seg_len_sq = dx * dx + dy * dy

        if seg_len_sq == 0:
            # degenerate
            return p, 0.0

        seg_len = math.sqrt(seg_len_sq)

        # 투영 비율 t (무제한, 클램프 ❌)
        t = ((px - ax) * dx + (py - ay) * dy) / seg_len_sq

        # 투영점
        proj_x = ax + t * dx
        proj_y = ay + t * dy

        # 좌/우 offset (외적 부호 사용)
        cross = dx * (py - ay) - dy * (px - ax)
        offset = -cross / seg_len

        return Point2d(proj_x, proj_y), offset

    def reversed(self):
        copy_s = self.start_coord.copy()
        copy_e = self.end_coord.copy()
        self.start_coord = copy_e
        self.end_coord = copy_s

    def get_offset(self, offset: float):
        copy_s = self.start_coord.copy()
        copy_e = self.end_coord.copy()
        if offset < 0:
            angle = self.tangent_at(0) + math.pi / 2
        else:
            angle = self.tangent_at(0) - math.pi / 2
        copy_s.move(angle,offset)
        copy_e.move(angle,offset)
        self.start_coord = copy_s
        self.end_coord = copy_e

