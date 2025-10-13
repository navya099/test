from optimserouteexplorer.curvesegment import CurveSegment
import math
from optimserouteexplorer.util import calculate_bearing, calculate_destination_coordinates, find_direction, \
    calculate_distance, is_approximately_equal
from shapely.geometry import Point

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

        for i in range(len(self.linestring.coords) - 2):

            ia = math.radians(self.angles[i])
            cl = self.radius_list[i] * ia
            tl = self.radius_list[i] * math.tan(ia / 2)
            tl_list.append(tl)
            cl_list.append(cl)

            bp_coord = self.linestring.coords[i]
            ip_coord = self.linestring.coords[i + 1]
            ep_coord = self.linestring.coords[i + 2]


            bp_ip_bearing = calculate_bearing(*bp_coord, *ip_coord)
            ip_ep_bearing = calculate_bearing(*ip_coord, *ep_coord)
            bp_ip_distance = calculate_distance(*bp_coord, *ip_coord)

            # IP_STA 계산
            ip_sta = bp_ip_distance if i == 0 else segments[i - 1].ec_sta + bp_ip_distance - tl_list[i - 1]

            bc_coord = calculate_destination_coordinates(*ip_coord, bp_ip_bearing, -tl)
            ec_coord = calculate_destination_coordinates(*ip_coord, ip_ep_bearing, tl)
            direction = find_direction(bp_coord, ip_coord, ep_coord)


            center_coord = self.calculate_curve_center(Point(bc_coord), Point(ec_coord), self.radius_list[i], direction)

            segments.append(CurveSegment(
                bc_coord=Point(bc_coord),
                ec_coord=Point(ec_coord),
                center_coord=Point(center_coord),
                direction=direction,
                bc_sta=ip_sta - tl,
                ec_sta=ip_sta - tl + cl,
                cl=cl,
                tl=tl
            ))

        return segments

    def cal_ep_sta(self) -> float:
        """
        마지막 EP_STA 계산
        """
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

    def calculate_curve_center(self, bc_xy: Point, ec_xy: Point,
                               radius: float, direction) -> Point:
        """
        BC, EC와 반지름 R이 주어졌을 때 원의 중심을 계산.
        (즉, BC와 EC에서 거리 R인 점들(두 교점) 중 direction에 맞는 쪽을 선택)
        """
        dx = ec_xy.x - bc_xy.x
        dy = ec_xy.y - bc_xy.y
        d = math.hypot(dx, dy)

        if d == 0:
            raise ValueError("BC and EC are identical points")
        # 두 점 사이 거리가 2R보다 크면 반지름 R로 두 점을 지나는 원이 없음
        if d > 2.0 * radius + 1e-9:
            raise ValueError("No circle with given radius passes through both BC and EC")

        # 중점
        mx = (bc_xy.x + ec_xy.x) / 2.0
        my = (bc_xy.y + ec_xy.y) / 2.0

        # 반(현) 길이와 높이(h)
        a = d / 2.0
        h = math.sqrt(max(0.0, radius * radius - a * a))

        # chord의 단위 수직벡터 (두 교점은 중점 ± h * (ux,uy))
        ux = -dy / d
        uy = dx / d

        c1x = mx + ux * h
        c1y = my + uy * h
        c2x = mx - ux * h
        c2y = my - uy * h

        # 각 후보에 대해 BC→EC의 중심각(끝-시작)을 계산하여 부호로 좌/우 판별
        def signed_delta_theta(cx, cy):
            phi0 = math.atan2(bc_xy.y - cy, bc_xy.x - cx)
            phi1 = math.atan2(ec_xy.y - cy, ec_xy.x - cx)
            # 정상화된 중심각 (-pi..pi)
            return math.atan2(math.sin(phi1 - phi0), math.cos(phi1 - phi0))

        d1 = signed_delta_theta(c1x, c1y)
        d2 = signed_delta_theta(c2x, c2y)

        # 방향에 맞게 선택: RIGHT -> 중심각이 음수(시계, 우회전)인 후보 선택
        if direction == 1:
            chosen_x, chosen_y = (c1x, c1y) if d1 < 0 else (c2x, c2y)
        else:  # LEFT
            chosen_x, chosen_y = (c1x, c1y) if d1 > 0 else (c2x, c2y)

        return Point(chosen_x, chosen_y)