from curvedirection import CurveDirection
from geometry.curvesegment import CurveSegment
import math
from core.util import is_approximately_equal
from shapely.geometry import Point

from math_utils import calculate_bearing, calculate_distance, calculate_destination_coordinates, find_curve_direction


class CurveAdjuster:
    """
    LineString 기반 곡선(IP, BC, EC, EP) 반경 조정 및 배치 관리 클래스
    """
    def __init__(self, linestring, angles: list[float], radius_list: list[float]):
        self.linestring = linestring
        self.angles = angles
        self.radius_list = radius_list

        self.segments: list[CurveSegment] = []

    def main_loop(self, min_arc_to_arc_distance: float=2000, max_iterations: int = 200, min_radius: float = 600):
        """
        곡선 반경 반복 조정
        """
        for j in range(max_iterations):
            self.segments = self._calculate_segments()
            ep_sta = self.cal_ep_sta()

            overlaps = self._check_overlaps(min_arc_to_arc_distance, ep_sta, min_radius)

            if not any(overlaps):
                #print(f'루프 {j}회차 종료: 곡선 조정 완료')
                break
        else:
            pass
            #print(f'루프 {max_iterations}회차 종료: 곡선반경 조정 실패')

    def _calculate_segments(self) -> list[CurveSegment]:
        """
        각 IP 단위로 CurveSegment 계산
        """
        segments: list[CurveSegment] = []
        tl_list, cl_list = [], []

        if not self.linestring or len(self.linestring.coords) < 3:
            return []

        n = min(len(self.angles), len(self.radius_list), len(self.linestring.coords) - 2)

        for i in range(n):
            ia = math.radians(self.angles[i])
            cl = self.radius_list[i] * ia
            tl = self.radius_list[i] * math.tan(ia / 2)
            tl_list.append(tl)
            cl_list.append(cl)

            bp_coord = Point(self.linestring.coords[i])
            ip_coord = Point(self.linestring.coords[i + 1])
            ep_coord = Point(self.linestring.coords[i + 2])

            bp_ip_bearing = calculate_bearing(bp_coord, ip_coord)
            ip_ep_bearing = calculate_bearing(ip_coord, ep_coord)
            bp_ip_distance = calculate_distance(bp_coord, ip_coord)

            ip_sta = bp_ip_distance if i == 0 else segments[i - 1].ec_sta + bp_ip_distance - tl_list[i - 1]

            bc_coord = Point(calculate_destination_coordinates(ip_coord, bearing=bp_ip_bearing, distance=-tl))
            ec_coord = Point(calculate_destination_coordinates(ip_coord, bearing=ip_ep_bearing, distance=tl))
            direction = find_curve_direction(bp_coord, ip_coord, ep_coord)

            center_coord = Point(self.calculate_curve_center(bc_coord, ec_coord, self.radius_list[i], direction))

            segments.append(CurveSegment(
                bc_coord=bc_coord,
                ec_coord=ec_coord,
                center_coord=center_coord,
                direction=direction,
                bc_sta=ip_sta - tl,
                ec_sta=ip_sta - tl + cl,
                cl=cl,
                tl=tl,
                radius=self.radius_list[i]
            ))

        return segments

    def cal_ep_sta(self) -> float:
        """
        마지막 EP_STA 계산
        """
        if not self.segments or len(self.linestring.coords) < 2:
            return 0
        last_segment = self.segments[-1]
        ep_coord = self.linestring.coords[-1]
        ec_ep_dist = calculate_distance(last_segment.ec_coord.x,last_segment.ec_coord.y, *ep_coord)
        return last_segment.ec_sta + ec_ep_dist

    def _check_overlaps(self, min_distance: float, ep_sta: float, min_radius: float) -> list[bool]:
        """
        각 segment의 BC-EC 거리 및 마지막 EP 체크, 필요시 radius 조정
        """
        overlaps = []
        n = len(self.segments)

        if not self.segments or len(self.linestring.coords) < 2:
            return [False]

        for i, seg in enumerate(self.segments):
            # 다음 BC까지 거리 계산
            if i < n - 1:
                bc_to_next_bc = self.segments[i + 1].bc_sta - seg.ec_sta
            else:
                bc_to_next_bc = ep_sta - seg.ec_sta

            # 거리 미만이면 radius 조정
            if i == 0 and seg.bc_sta < min_distance:
                self.radius_list[0] = self.adjust_radius(0, min_radius=min_radius)
                overlaps.append(True)
            elif bc_to_next_bc < min_distance:
                max_idx = self._find_max_radius_index(i)
                self.radius_list[max_idx] = self.adjust_radius(max_idx, min_radius=min_radius)
                overlaps.append(True)
            else:
                overlaps.append(False)

        # 마지막 IP-EP 체크
        if not is_approximately_equal(
            calculate_bearing(self.segments[-1].ec_coord.x,self.segments[-1].ec_coord.y, *self.linestring.coords[-1]),
            calculate_bearing(self.segments[-1].ec_coord.x,self.segments[-1].ec_coord.y, *self.linestring.coords[-1])
        ):
            self.radius_list[-1] = self.adjust_radius(-1, min_radius=min_radius)
            overlaps[-1] = True

        return overlaps

    def adjust_radius(self, index: int, decrement: int = 500, min_radius: float = 600) -> float:
        """
        radius 조정
        """
        self.radius_list[index] = max(self.radius_list[index] - decrement, min_radius)
        return self.radius_list[index]

    def _find_max_radius_index(self, i: int) -> int:
        """
        현재와 주변 segment 중 최대 radius index 반환
        """
        n = len(self.radius_list)
        idx_list = [i]
        if i > 0:
            idx_list.append(i - 1)
        if i < n - 1:
            idx_list.append(i + 1)
        max_idx = max(idx_list, key=lambda idx: self.radius_list[idx])
        return max_idx

    def calculate_curve_center(self, bc: Point, ec: Point, radius: float, direction: CurveDirection) -> Point:
        """
        두 점(BC, EC)과 반지름, 방향(1=RIGHT, 0=LEFT)으로 원의 중심 좌표 계산.
        """
        dx = ec.x - bc.x
        dy = ec.y - bc.y
        d = math.hypot(dx, dy)

        if d == 0 or d > 2 * radius:
            raise ValueError("Invalid BC/EC distance for given radius")

        # 중점
        mx = (bc.x + ec.x) / 2
        my = (bc.y + ec.y) / 2

        # chord의 수직거리 h
        h = math.sqrt(radius ** 2 - (d / 2) ** 2)

        # 단위 수직벡터
        ux = -dy / d
        uy = dx / d

        # 방향 선택 (1=RIGHT, 0=LEFT)
        sign = -1 if direction == CurveDirection.RIGHT else 1

        # 중심 좌표 계산
        cx = mx + sign * ux * h
        cy = my + sign * uy * h

        return Point(cx, cy)