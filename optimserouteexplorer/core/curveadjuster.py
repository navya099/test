# core/curveadjuster.py
import logging
import math

from shapely.geometry import Point

from geometry.curvesegment import CurveSegment
from xref.utils.curvedirection import CurveDirection
from xref.utils.math_utils import (
    calculate_bearing,
    calculate_distance,
    calculate_destination_coordinates,
    find_curve_direction,
)

logger = logging.getLogger(__name__)


class CurveAdjuster:
    def __init__(self, linestring, angles, radius_list):
        self.linestring = linestring
        self.angles = list(angles)
        self.radius_list = list(radius_list)
        self.segments: list[CurveSegment] = []
        self.converged: bool = False

    def main_loop(self, min_arc_to_arc_distance: float = 100.0,
                  max_iterations: int = 200,
                  min_radius: float = 600) -> bool:
        self.converged = False

        expected = len(self.linestring.coords) - 2
        if len(self.angles) != expected or len(self.radius_list) != expected:
            raise ValueError(
                f"길이 불일치: angles={len(self.angles)}, "
                f"radius_list={len(self.radius_list)}, coords-2={expected}"
            )

        for j in range(max_iterations):
            self.segments = self._calculate_segments()
            ep_sta = self.cal_ep_sta()
            overlaps = self._check_overlaps(min_arc_to_arc_distance, ep_sta, min_radius)
            if not any(overlaps):
                self.converged = True
                logger.debug("곡선 조정 수렴: %d회", j + 1)
                return True

        logger.warning("곡선 조정 수렴 실패 (%d회)", max_iterations)
        return False

    def _calculate_segments(self):
        segments = []
        tl_list = []
        if not self.linestring or len(self.linestring.coords) < 3:
            return []

        coords = list(self.linestring.coords)
        n = len(self.angles)

        for i in range(n):
            angle = self.angles[i]
            radius = self.radius_list[i]

            # NaN/유효하지 않은 각도/반경 스킵
            if angle is None or math.isnan(angle) or angle <= 0:
                logger.debug("곡선 %d 스킵: angle=%s", i, angle)
                continue
            if radius is None or math.isnan(radius) or radius <= 0:
                logger.debug("곡선 %d 스킵: radius=%s", i, radius)
                continue

            ia = math.radians(angle)
            cl = radius * ia
            tl = radius * math.tan(ia / 2)
            tl_list.append(tl)

            bp_coord = Point(coords[i])
            ip_coord = Point(coords[i + 1])
            ep_coord = Point(coords[i + 2])

            bp_ip_bearing = calculate_bearing(bp_coord, ip_coord)
            ip_ep_bearing = calculate_bearing(ip_coord, ep_coord)
            bp_ip_distance = calculate_distance(bp_coord, ip_coord)

            ip_sta = (
                bp_ip_distance if not segments
                else segments[-1].ec_sta + bp_ip_distance - tl_list[-2] if len(tl_list) >= 2 else bp_ip_distance
            )

            try:
                bc_coord = Point(calculate_destination_coordinates(
                    ip_coord, bearing=bp_ip_bearing, distance=-tl
                ))
                ec_coord = Point(calculate_destination_coordinates(
                    ip_coord, bearing=ip_ep_bearing, distance=tl
                ))
            except Exception as e:
                logger.warning("곡선 %d BC/EC 계산 실패: %s", i, e)
                continue

            if bc_coord.is_empty or ec_coord.is_empty:
                logger.warning("곡선 %d BC/EC 빈 좌표", i)
                continue

            direction = find_curve_direction(bp_coord, ip_coord, ep_coord)

            try:
                center_coord = Point(self.calculate_curve_center(
                    bc_coord, ec_coord, radius, direction
                ))
            except ValueError as e:
                logger.warning("곡선 %d 중심 계산 실패: %s", i, e)
                continue

            segments.append(CurveSegment(
                bc_coord=bc_coord,
                ec_coord=ec_coord,
                center_coord=center_coord,
                direction=direction,
                bc_sta=ip_sta - tl,
                ec_sta=ip_sta - tl + cl,
                cl=cl, tl=tl, radius=radius,
            ))

        return segments

    def cal_ep_sta(self) -> float:
        if not self.segments or len(self.linestring.coords) < 2:
            return 0.0
        last = self.segments[-1]
        ep = self.linestring.coords[-1]
        ec_ep_dist = calculate_distance(last.ec_coord.x, last.ec_coord.y, *ep)
        return last.ec_sta + ec_ep_dist

    def _check_overlaps(self, min_distance: float, ep_sta: float,
                        min_radius: float) -> list[bool]:
        overlaps: list[bool] = []
        if not self.segments or len(self.linestring.coords) < 2:
            return [False]

        n = len(self.segments)
        for i, seg in enumerate(self.segments):
            if i < n - 1:
                bc_to_next_bc = self.segments[i + 1].bc_sta - seg.ec_sta
                if bc_to_next_bc < min_distance:
                    max_idx = self._find_max_radius_index(i)
                    self._adjust_radius_at(max_idx, min_radius=min_radius)
                    overlaps.append(True)
                    continue

            if i == 0 and seg.bc_sta < min_distance:
                self._adjust_radius_at(0, min_radius=min_radius)
                overlaps.append(True)
                continue

            if i == n - 1 and seg.ec_sta > ep_sta:
                self._adjust_radius_at(-1, min_radius=min_radius)
                overlaps.append(True)
                continue

            overlaps.append(False)

        return overlaps

    def _adjust_radius_at(self, index: int, decrement: float = 500,
                          min_radius: float = 600) -> float:
        self.radius_list[index] = max(self.radius_list[index] - decrement, min_radius)
        return self.radius_list[index]

    def _find_max_radius_index(self, i: int) -> int:
        n = len(self.radius_list)
        idx_list = [i]
        if i > 0:
            idx_list.append(i - 1)
        if i < n - 1:
            idx_list.append(i + 1)
        return max(idx_list, key=lambda idx: self.radius_list[idx])

    def calculate_curve_center(self, bc: Point, ec: Point, radius: float,
                               direction: CurveDirection) -> Point:
        dx = ec.x - bc.x
        dy = ec.y - bc.y
        d = math.hypot(dx, dy)
        if d == 0 or d > 2 * radius:
            raise ValueError(f"Invalid BC/EC: d={d}, 2r={2 * radius}")
        mx = (bc.x + ec.x) / 2
        my = (bc.y + ec.y) / 2
        h = math.sqrt(radius ** 2 - (d / 2) ** 2)
        ux = -dy / d
        uy = dx / d
        sign = -1 if direction == CurveDirection.RIGHT else 1
        return Point(mx + sign * ux * h, my + sign * uy * h)