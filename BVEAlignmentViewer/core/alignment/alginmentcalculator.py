import math
from math_utils import calculate_bearing, calculate_coordinates,calculate_distance
from model.bveroutedata import BVERouteData
from model.bvetrack import Curve
from curvetype import CurveType
from vector2 import Vector2
from curvedirection import CurveDirection

class AlignmentCalculator:
    """
    선형 계산용 stateless클래스
    """
    @staticmethod
    def calculate_intersection_point(bc: Vector2, ec: Vector2, theta1: float, theta2: float) -> Vector2 | None:
        """
        교점을 찾는 메소드 (방향 벡터 방식)

        Args:
            bc: 시작점 (Vector2)
            theta1: 시작점 방향각 (라디안)
            ec: 종점 (Vector2)
            theta2: 종점 방향각 (라디안)

        Returns:
            Vector2: 교점 좌표, 평행이면 None
        """
        x1, y1 = bc.x, bc.y
        x2, y2 = ec.x, ec.y

        # 방향 벡터
        dx1, dy1 = math.cos(theta1), math.sin(theta1)
        dx2, dy2 = math.cos(theta2), math.sin(theta2)

        # 행렬식(det) 계산 (평행 여부 확인)
        det = dx1 * (-dy2) - (-dx2) * dy1
        if math.isclose(det, 0.0):
            return None  # 평행 직선

        # 매개변수 t 계산
        t = ((x2 - x1) * (-dy2) - (y2 - y1) * (-dx2)) / det

        x = x1 + t * dx1
        y = y1 + t * dy1

        return Vector2(x, y)

    @staticmethod
    def split_by_curve_sections(curves: list[Curve]) -> list[list[Curve]]:
        """
        곡선 리스트를 분석해 구간을 나누는 새 구현.
        방식:
          1. 각 리스트 순회
          2. 리스트에 추가하면서 길이 검사
          3. 길이 및 조건으로로 판단
        """
        sections = []
        current_section = []
        for i, curve in enumerate(curves):
            station = curve.station
            radius = curve.radius
            if i == 0:  # 첫번째 경우로 BP
                current_section.append(curve)
                sections.append(current_section)
                current_section = []
            else:
                current_section.append(curve)
                if len(current_section) == 2:
                    first_radius = current_section[0].radius
                    second_radius = current_section[1].radius
                    if first_radius != 0 and second_radius == 0:
                        # 단곡선
                        curve_type = CurveType.Simple
                        sections.append(current_section)
                        current_section = []
                    else:
                        continue
                elif len(current_section) == 3:
                    first_radius = current_section[0].radius
                    second_radius = current_section[1].radius
                    third_radius = current_section[2].radius
                    if first_radius != 0 and second_radius != 0 and third_radius == 0:
                        # 복심곡선 판단[166,300,0]
                        if first_radius * second_radius > 0:
                            # 복심곡선
                            curve_type = CurveType.Compound
                            sections.append(current_section)
                            current_section = []
                        elif first_radius * second_radius < 0:
                            # 반향곡선[166,-166,0]
                            curve_type = CurveType.Reverse
                            sections.append(current_section[:2])
                            sections.append(current_section[1:])
                            current_section = []
                # 완화곡선
                elif len(current_section) > 3 and current_section[-1].radius == 0:
                    radii = [c.radius for c in current_section]
                    if all(r != 0 for r in radii[:-1]):
                        sections.append(current_section)
                        current_section = []

        return sections

    @staticmethod
    def define_iscurve(section: list[Curve]) -> CurveType:
        """
        단곡선(Simple) / 복심곡선(Compound) / 완화곡선(Spiral) 구분

        Args:
            section (list[Curve]): 구간 곡선 리스트 (BC~EC)

        Returns:
           CurveType
        """
        radii = [c.radius for c in section]

        # ✅ 단곡선 (ex: [600, 0])
        if len(section) == 2 and radii[-1] == 0:
            return CurveType.Simple

        # ✅ 복심곡선 (ex: [600, 500, 0] or [600, -500, 0])
        if len(section) == 3 and radii[-1] == 0:
            return CurveType.Compound

        # ✅ 완화곡선
        if len(section) > 3 and radii[-1] == 0 and all(r != 0 for r in radii[:-1]):
            return CurveType.Spiral

        # ✅ 반향곡선
        if len(section) == 2 and radii[-1] != 0:
            return CurveType.Reverse
        # 안전장치: 기본값

        return CurveType.NONE

    @staticmethod
    def define_section_radius(section: list[Curve], curvetype: CurveType = None) -> tuple[float, float]:
        """
        구간 내 곡선 반경(r1, r2) 찾기 (단곡선, 복곡선, 완화곡선 포함)

        Args:
            section (list[Curve]): Curve 객체 리스트
            curvetype (CurveType, optional): 곡선 타입 지정 (없으면 자동 판별)

        Returns:
            (r1, r2): 시작반경(r1), 끝반경(r2)
        """
        radius = 0.0
        radius2 = 0.0

        # 단곡선: 반경 1개만 존재
        if curvetype == CurveType.Simple:
            radius = section[0].radius

        # 복곡선: 반경 2개 존재
        elif curvetype == CurveType.Compound:
            radius = section[0].radius
            radius2 = section[1].radius

            # 완화곡선: r1, r2 및 PCC 여부 판단
        elif curvetype == CurveType.Spiral:
            # 첫번째 요소만 보고 판단
            isminus = (section[0].radius < 0)
            # 0 제외한 반경만 뽑기
            nonzero_radii = [sec.radius for sec in section if sec.radius != 0]

            if isminus:
                radius = max(nonzero_radii)
            else:
                radius = min(nonzero_radii)

        return radius, radius2

    def split_simplecurve_section(self, bc_curve: Curve, ec_curve: Curve ,r: float, direction: CurveDirection) -> Curve:
        """
        단곡선을 복심곡선으로 분할하는 메소드
        Returns:
            Curve(Curve): 분할된 중간 Curve객체
        """
        midstation = bc_curve.station + (ec_curve.station - bc_curve.station) / 2
        mid_point = self.calculate_point_by_station_for_simplecurve(bc_curve, ec_curve, r, direction, midstation)

        return mid_point

    def calculate_point_by_station_for_simplecurve(
            self, bc_curve: Curve, ec_curve: Curve,
            r: float,direction: CurveDirection, station: float
    ):
        """
        단곡선내 측점(station)으로 좌표를 찾고 해당 구간 Curve객체 생성 후 반환
        Args:
            station: 측점
            r: 곡선반경
            direction: CurveDirection
            bc_curve: bc Curve객체
            ec_curve: ec Curve객체

        Returns:
            Curve(Curve): Curve객체
        """
        #언팩
        bcxy = bc_curve.coord
        ecxy = ec_curve.coord
        #1 .bc점에서 떨어진 거리 구하기
        length = station - bc_curve.station
        #2 내각 ia
        ia = length / r
        #CENTER 구하기
        center = self.calculate_curve_center(bcxy, ecxy, r, direction)
        #3. 원점 O -> BC 까지의 방위각
        azimuth_o_bc = calculate_bearing(center.x, center.y, bcxy.x, bcxy.y)
        #4. 원점 O -> station 까지의 방위각
        # 4. 원점 O -> station 까지의 방위각
        if direction == CurveDirection.RIGHT:
            azimuth_o_station = azimuth_o_bc - ia
        else:
            azimuth_o_station = azimuth_o_bc + ia
        #5 station의 좌표
        stationxy = calculate_coordinates(center.x, center.y, azimuth_o_station, r)
        #6 stationxy 좌표에서 접선의 방위각
        azimuth_tangent = azimuth_o_station - (math.pi / 2) if direction == CurveDirection.RIGHT else azimuth_o_station + (math.pi / 2)
        #7. Curve객체 생성
        return Curve(station=station, radius=r, direction=azimuth_tangent,cant=0,coord=Vector2(x=stationxy[0], y=stationxy[1]))

    @staticmethod
    def calculate_curve_center(bc_xy: Vector2, ec_xy: Vector2,
                               radius: float, direction: CurveDirection) -> Vector2:
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
        if direction == CurveDirection.RIGHT:
            chosen_x, chosen_y = (c1x, c1y) if d1 < 0 else (c2x, c2y)
        else:  # LEFT
            chosen_x, chosen_y = (c1x, c1y) if d1 > 0 else (c2x, c2y)

        return Vector2(x=chosen_x, y=chosen_y)

    @staticmethod
    def calculate_curve_geometry(radius, cl) -> tuple:
        """
        Private메소드 단곡선 제원 계산
        Args:
            radius: 곡선반경
            cl: 곡선장
        Returns:
            tuple: r, ia, tl, m, sl
        """
        # 곡선 제원 계산
        r = abs(radius)  # 곡선반경
        ia = cl / r  # 교각
        tl = r * math.tan(ia / 2)  # 접선장
        m = r * (1 - math.cos(ia / 2))  # 중앙종거
        sl = r * (1 / math.cos(ia / 2) - 1)  # 외거

        return r, ia, tl, m, sl

    @staticmethod
    def calculate_spiralcurve_geometry(radius, length, ia) -> tuple:
        """
        완화곡선 제원 산출용 프라이베이트 메소드
        Returns:
            tuple
        """
        r = abs(radius)
        x1 = length
        theta_pc = math.atan(x1 / (2 * r))
        x2 = x1 - (r * math.sin(theta_pc))  # x2
        w13 = r  # -R
        y1 = (x1 ** 2) / (6 * r)  # Y1
        w15 = (x1 ** 2) / (6 * w13)  # W-Y
        f = y1 - r * (1 - math.cos(theta_pc))  # 이정량 F
        s = 1 / math.cos(ia / 2) * f  # S
        k = f * math.tan(ia / 2)  # 수평좌표차K
        w = (r + f) * math.tan(ia / 2)  # W
        tl = x2 + w  # TL
        lc = r * (ia - 2 * theta_pc)  # 원곡선 길이
        cl = lc + 2 * length  # 전체곡선길이
        sl = r * (1 / (math.cos(ia / 2)) - 1) + s
        ia2 = ia - (2 * theta_pc)  # 원곡선교각
        c = math.atan(y1 / x1)  # C
        xb = math.pi / 2 - theta_pc  # XB
        b = math.pi / 2 - c - xb

        return x1, x2, w13, y1, w15,f, s, k, w, tl,lc, cl, sl, ia2,c, xb, b

    @staticmethod
    def define_spiral_spec(section: list[Curve], direction: CurveDirection) -> \
            tuple[int, int]:
        """
        구간내에서 완화곡선 제원 인덱스 찾기
        Args:
            section: list[Curve]
            direction: CurveDirection

        Returns:
            PC, CP 인덱스
        """

        # 0 제외 반경 리스트
        nonzero_radii = [sec.radius for sec in section if sec.radius != 0]
        min_value = min(nonzero_radii)
        max_value = max(nonzero_radii)

        # 원래 section에서 해당 radius 값의 첫 인덱스 찾기
        min_index = next(i for i, curve in enumerate(section) if curve.radius == min_value)
        max_index = next(i for i, curve in enumerate(section) if curve.radius == max_value)

        #좌향곡선은 최댓값이 R
        if direction == CurveDirection.LEFT:
            pc_index = max_index
            cp_index = max_index + 1
            selected_radius = max_value
            selected_cant = section[pc_index].cant
            pc_sta = section[pc_index].station
            cp_sta = section[cp_index].station
        #우향곡선은 최솟값이 R
        else:
            pc_index = min_index
            cp_index = min_index + 1
            selected_radius = min_value
            selected_cant = section[pc_index].cant
            pc_sta = section[pc_index].station
            cp_sta = section[cp_index].station

        return pc_index, cp_index

    def calculate_stationinfo(self, bvedata: BVERouteData):
        curve_dict = {curve.station: curve for curve in bvedata.curves}
        for station in bvedata.stations:
            if station.station % bvedata.block_interval != 0:
                # block_interval이 아닌경우 선형에서 좌표와 각돌을 찾아야함
                curve = self.calculate_between_two_point(bvedata, station.station)
            else:
                curve = curve_dict.get(station.station)
            if curve:
                station.coord = curve.coord
                station.direction = curve.direction

    def calculate_between_two_point(self, bvedata: BVERouteData, target_station: float):
        curves = bvedata.curves
        last_station = bvedata.stations[-1].station
        last_coord = bvedata.stations[-1].coord

        # 중간 곡선/직선 구간 처리
        for j, curve in enumerate(curves):
            next_curve = curves[j + 1] if j + 1 < len(curves) else None
            if next_curve and curve.station <= target_station <= next_curve.station:
                r = curve.radius
                direction = CurveDirection.RIGHT if r > 0 else CurveDirection.LEFT
                if r != 0:
                    return self.calculate_point_by_station_for_simplecurve(curve, next_curve, r, direction,
                                                                           target_station)
                else:
                    return self.calculate_point_by_station_for_straight(curve, next_curve, curve.direction,
                                                                        target_station)

        # 마지막 곡선 이후 직선 구간 처리
        if curves and target_station > curves[-1].station:
            last_curve = curves[-1]
            r = last_curve.radius
            direction = CurveDirection.RIGHT if r > 0 else CurveDirection.LEFT
            if r != 0:  # 마지막 곡선 이후도 곡선일 경우
                return self.calculate_point_by_station_for_simplecurve(
                    last_curve,
                    Curve(coord=last_coord, station=last_station, radius=0, cant=0, direction=last_curve.direction),
                    r,
                    direction,
                    target_station
                )
            else:  # 마지막 직선 구간
                return self.calculate_point_by_station_for_straight(
                    last_curve,
                    Curve(coord=last_coord, station=last_station, radius=0, cant=0, direction=last_curve.direction),
                    last_curve.direction,
                    target_station
                )

        return None

    @staticmethod
    def calculate_point_by_station_for_straight(p1: Curve, p2: Curve, direction: float,
                                                target_station: float) -> Curve:
        """
        target_station 위치의 직선 좌표와 방향 계산
        Args:
            p1(Curve): 시작 곡선
            p2(Curve): 끝 곡선
            direction(float): 방향각(라디안)
            target_station(float): 찾을 측점
        Returns:
            Curve
        """
        total_len = calculate_distance(p1.coord, p2.coord)
        ratio = (target_station - p1.station) / total_len
        x = p1.coord.x + (p2.coord.x - p1.coord.x) * ratio
        y = p1.coord.y + (p2.coord.y - p1.coord.y) * ratio
        return Curve(coord=Vector2(x, y), direction=direction, station=target_station, radius=0,cant=0)
