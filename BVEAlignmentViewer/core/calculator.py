import math
import numpy as np
from math_utils import get_station_by_block_index, get_block_index, calculate_bearing, calculate_coordinates
from model.model import Curve, IPdata, CurveDirection, CurveSegment, BVERouteData, CurveType, EndPoint, SpiralSegment
from vector2 import Vector2
from vector3 import Vector3, to2d


class Calculator:
    """
    선형 계산용 클래스
    Attributes:
        bvedata (BVERouteData): BVERouteData 객체
    """
    def __init__(self):
        self.bvedata = None

    def init_bvedata(self, bvedata: BVERouteData):
        self.bvedata = bvedata

    def calculate_intersection_point(self, bc: Vector2, ec: Vector2, theta1: float, theta2: float) -> Vector2 | None:
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

    def split_by_curve_sections(self, curves: list[Curve]) -> list[list[Curve]]:
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
                            curve_type = CurveType.Complex
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

    def build_ipdata_from_sections(self) -> list[IPdata]:
        """
        BVERouteData 속성으로 IPdata 리스트 생성.
        BP -> 곡선 -> EP 순서 처리
        """
        ipdata_list = []
        curvesection_ipdata_list = []
        sections = self.split_by_curve_sections(self.bvedata.curves)

        for i, section in enumerate(sections):
            if i == 0:
                # BP
                ipdata_list.append(self._process_endpoint(bp=True))
            else:  # 곡선구간 처리
                curvesection_ipdata_list = self._process_curve_section(section, ipno=i)
                ipdata_list.extend(curvesection_ipdata_list)

        # EP 추가
        ipdata_list.append(self._process_endpoint(bp=False))

        return ipdata_list

    # --------------------- Private methods ---------------------
    def _process_endpoint(self, bp: bool) -> EndPoint:
        """BP 또는 EP 처리"""
        coord3d = self.bvedata.coords[0] if bp else self.bvedata.coords[-1]
        dir3d = self.bvedata.directions[0] if bp else self.bvedata.directions[-1]
        coord2d = to2d(coord3d)
        azimuth = to2d(dir3d).toradian()

        return EndPoint(
            coord=coord2d,
            direction=azimuth,
        )

    def define_iscurve(self, section: list[Curve]) -> CurveType:
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
            return CurveType.Complex

        # ✅ 완화곡선
        if len(section) > 3 and radii[-1] == 0 and all(r != 0 for r in radii[:-1]):
            return CurveType.Spiral

        # ✅ 반향곡선
        if len(section) == 2 and radii[-1] != 0:
            return CurveType.Reverse
        # 안전장치: 기본값

        return CurveType.NONE

    def define_section_radius(self, section: list[Curve], curvetype: CurveType = None) -> tuple[float, float]:
        """
        구간내 곡선반경 찾기
        Args:
            section:  Curve객체 리스트

        Returns:
            radius (tuple[float, float]): 찾은 반경 리스트(복심곡선용)
        """

        radius2 = 0.0
        # 곡선 타입 호출
        if curvetype is None:
            curvetype = self.define_iscurve(section)
        if curvetype == CurveType.Simple:
            radius = section[0].radius
        elif curvetype == CurveType.Complex:
            radius = section[0].radius
            radius2 = section[1].radius
        else:
            # 첫번째 요소만 보고 판단
            isminus = (section[0].radius < 0)
            # 0 제외한 반경만 뽑기
            nonzero_radii = [sec.radius for sec in section if sec.radius != 0]

            if isminus:
                radius = max(nonzero_radii)
            else:
                radius = min(nonzero_radii)
        return radius, radius2

    def _process_curve_section(self, section: list[Curve], ipno: int) -> list[IPdata]:
        """곡선 구간 처리 메인"""
        curvetype = self.define_iscurve(section)

        if curvetype in (CurveType.Simple, CurveType.Reverse):
            return self._process_simple_curve(section, ipno)
        elif curvetype == CurveType.Complex:
            return self._process_complex_curve(section, ipno)
        elif curvetype == CurveType.Spiral:
            return self._process_spiral_curve(section, ipno)
        else:
            raise ValueError(f"Unknown CurveType: {curvetype}")

    # ---------------------
    # 단곡선 처리
    def _process_simple_curve(self, section: list[Curve], ipno: int | str) -> list[IPdata]:
        bc_curve, ec_curve = section[0], section[-1]
        bc_sta, ec_sta = bc_curve.station, ec_curve.station
        cl = ec_sta - bc_sta
        r, _ = self.define_section_radius(section, CurveType.Simple)
        curve_direction = CurveDirection.RIGHT if r > 0 else CurveDirection.LEFT

        r, ia, tl, m, sl = self._calculate_curve_geometry(r, cl)

        # ia가 180° 이상이면 분할메소드 처리
        if ia > math.pi:
            # 재귀호출
            pcc_curve = self.split_simplecurve_section(bc_curve, ec_curve, r, curve_direction)
            section1 = [bc_curve, pcc_curve]
            section2 = [pcc_curve, ec_curve]
            ipdata_list = []
            ipdata_list.extend(self._process_simple_curve(section1, f"{ipno}-1"))
            ipdata_list.extend(self._process_simple_curve(section2, f"{ipno}-2"))
            return ipdata_list

        bc_coord, ec_coord = bc_curve.coord, ec_curve.coord
        bc_azimuth, ec_azimuth = bc_curve.direction, ec_curve.direction
        center_coord = self.calculate_curve_center(bc_coord, ec_coord, r, curve_direction)
        ip_coord = self._calculate_ip_coord(bc_coord, ec_coord, bc_azimuth, ec_azimuth)

        curve_segment = self._create_curve_segment(r, bc_sta, ec_sta,
                                                   bc_coord, ec_coord, center_coord,
                                                   tl, cl, sl, m,
                                                   bc_azimuth, ec_azimuth)
        ipdata = IPdata(ipno=ipno,
                        curvetype=CurveType.Simple,
                        curve_direction=curve_direction,
                        radius=r,
                        ia=ia,
                        coord=ip_coord,
                        segment=[curve_segment])

        return [ipdata]

    # ---------------------
    # 복심곡선 처리
    def _process_complex_curve(self, section: list[Curve], ipno: int) -> list[IPdata]:
        """
        복심곡선 처리 메소드
        Args:
            section: 구간
            ipno: ip번호

        Returns:
            IPdata
        """
        # BC,PCC,EC 언팩
        bc_curve, pcc_curve, ec_curve = section[0], section[1], section[-1]
        bc_sta, pcc_sta, ec_sta = bc_curve.station, pcc_curve.station, ec_curve.station
        # 전체 cl
        cl = ec_sta - bc_sta
        # 개별 cl
        cl1, cl2 = pcc_sta - bc_sta, ec_sta - pcc_sta
        cl_list = cl1, cl2
        radii = self.define_section_radius(section)
        # 복심곡선 반경1, 반경2
        r1, r2 = radii
        curve_direction = CurveDirection.RIGHT if r1 > 0 else CurveDirection.LEFT
        curve_segment_list = []

        # ----- 1) total IA 빠른 계산 -----
        ia_list = []
        for r, cl in zip(radii, cl_list):
            _, ia, _, _, _ = self._calculate_curve_geometry(r, cl)
            ia_list.append(ia)

        total_ia = sum(ia_list)

        # ----- 2) IA > 180° 이면 즉시 분할 후 SimpleCurve로 위임 -----
        if total_ia > math.pi:
            ipdata_list = []
            for (r, cl, bc_seg, ec_seg, ia) in [
                (r1, cl1, bc_curve, pcc_curve, ia_list[0]),
                (r2, cl2, pcc_curve, ec_curve, ia_list[1]),
            ]:
                # IA가 90° 넘는 반경만 분할
                if ia > math.pi / 2:
                    pcc_curve2 = self.split_simplecurve_section(bc_seg, ec_seg, r, curve_direction)
                    section1 = [bc_seg, pcc_curve2]
                    section2 = [pcc_curve2, ec_seg]
                    for i, sec in enumerate([section1, section2], start=1):
                        ipdata_list.extend(self._process_simple_curve(sec, f'{ipno}-{i + 1}'))
                else:
                    ipdata_list.extend(self._process_simple_curve([bc_seg, ec_seg], f'{ipno}-{1}'))
            return ipdata_list

        # 정상로직
        ia_list = []
        for i, (r, cl) in enumerate(zip(radii, cl_list)):
            # 각 구간 BC, EC 설정
            if i == 0:
                bc_curve_seg, ec_curve_seg = bc_curve, pcc_curve
            else:
                bc_curve_seg, ec_curve_seg = pcc_curve, ec_curve
            r, ia, tl, m, sl = self._calculate_curve_geometry(r, cl)
            ia_list.append(ia)
            bc_coord, ec_coord = bc_curve_seg.coord, ec_curve_seg.coord
            bc_azimuth, ec_azimuth = bc_curve_seg.direction, ec_curve_seg.direction
            center_coord = self.calculate_curve_center(bc_coord, ec_coord, r, curve_direction)
            curve_segment_list.append(
                self._create_curve_segment(r, bc_sta, ec_sta,
                                           bc_coord, ec_coord, center_coord,
                                           tl, cl, sl, m,
                                           bc_azimuth, ec_azimuth)
            )
        # 대표 IP제원 다시계산
        ia = sum(ia_list)
        ip_coord = self._calculate_ip_coord(bc_curve.coord, ec_curve.coord, bc_curve.direction, ec_curve.direction)
        return [IPdata(ipno=ipno,
                       curvetype=CurveType.Complex,
                       curve_direction=curve_direction,
                       radius=radii,
                       ia=ia,
                       coord=ip_coord,
                       segment=curve_segment_list)]

    # ---------------------
    # 완화곡선 처리
    def _process_spiral_curve(self, section: list[Curve], ipno: int) -> IPdata:
        #원곡선 반경
        r, _ = self.define_section_radius(section)
        curve_direction = CurveDirection.RIGHT if r > 0 else CurveDirection.LEFT

        # 완화곡선 인덱스 찾기
        pc_idx, cp_idx = self.define_spiral_spec(section, direction=curve_direction)
        sp_curve, ps_curve = section[0], section[-1]
        pc_curve, cp_curve = section[pc_idx], section[cp_idx]

        #언팩
        sp_sta, pc_sta, cp_sta, ps_sta = sp_curve.station, pc_curve.station, cp_curve.station, ps_curve.station
        sp_coord, pc_coord, cp_coord, ps_coord = sp_curve.coord, pc_curve.coord, cp_curve.coord, ps_curve.coord
        sp_direction, pc_direction, cp_direction, ps_direction = sp_curve.direction, pc_curve.direction, cp_curve.direction, ps_curve.direction

        cl = ps_sta - sp_sta #전체 cl
        l1 = pc_sta - sp_sta #시점 완화곡선 길이
        l2 = ps_sta - cp_sta #종점 완화곡선 길이
        lc = cp_sta - pc_sta #원곡선 길이
        ia = ps_curve.direction - sp_curve.direction #교각
        #ip좌표
        ip_coord = self._calculate_ip_coord(sp_curve.coord, ps_curve.coord, sp_curve.direction, ps_curve.direction)

        #세그먼트 계산
        #유형별로 객체 생성
        #case1 완화곡선-원곡선-완화곡선
        #case2 완화곡선-원곡선
        #case3 원곡선 -완화곡선
        #case4 완화곡선-완화곡선

        #객체 초기화
        segment_list = []
        segment = None

        # 세그먼트 계산
        segment_list = []

        # 시점 완화곡선 여부
        if l1 > 0:
            segment_list.append(
                self._calculate_spiralcurve_geometry(r, l1, ia)
            )

        # 원곡선
        if lc > 0:
            r, ia2, tl, m, sl = self._calculate_curve_geometry(r, lc)
            center_coord = self.calculate_curve_center(pc_coord, cp_coord, r, curve_direction)
            segment_list.append(
                self._create_curve_segment(
                    r, pc_sta, cp_sta,
                    pc_coord, cp_coord, center_coord,
                    tl, lc, sl, m,
                    pc_direction, cp_direction
                )
            )

        # 종점 완화곡선 여부
        if l2 > 0:
            segment_list.append(
                self._calculate_spiralcurve_geometry(r, l2, ia)
            )

        return IPdata(ipno=ipno,
                      curvetype=CurveType.Spiral,
                      curve_direction=curve_direction,
                      radius=r,
                      ia=ia,
                      coord=ip_coord,
                      segment=segment_list
                      )

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

    def calculate_curve_center(self, bc_xy: Vector2, ec_xy: Vector2,
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

    def _calculate_curve_geometry(self, radius, cl) -> tuple:
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

    def _calculate_spiralcurve_geometry(self, radius, length, ia) -> SpiralSegment:
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

        return SpiralSegment(
            x1=x1,
            x2=x2,
            w13=w13,
            y1=y1,
            w15=w15,
            f=f,
            s=s,
            k=k,
            w=w,
            tl=tl,
            lc=lc,
            total_length=cl,
            sl=sl,
            ria=ia2,
            c=c,
            xb=xb,
            b=b
        )

    def _calculate_ip_coord(self, bc_xy, ec_xy, bc_azimuth, ec_azimuth) -> Vector2:
        """
        Private 메소드: IP 좌표 계산 래퍼
        Args:
            bc_xy (Vector2): BC 좌표
            ec_xy (Vector2): EC 좌표
            bc_azimuth (float): BC 각도 라디안
            ec_azimuth (float): EC 각도 라디안
        Returns:
            Vector2: IP 좌표
        """
        return  self.calculate_intersection_point(bc_xy, ec_xy, bc_azimuth, ec_azimuth)

    def _create_curve_segment(self, r, bc_sta, ec_sta, bc_coord, ec_coord, center_coord,
                              tl,cl,sl,m, bc_azimuth, ec_azimuth) -> CurveSegment:
        """
        Private 메소드: CurveSegment객체 생성
        Args:
            r (float): 곡선 반경
            bc_sta (float): BC 측점
            ec_sta (float): EC 측점
            bc_coord (Vector2): BC 좌표
            ec_coord (Vector2): EC 좌표
            center_coord (Vector2): 곡선 중심 좌표
            tl (float): 접선장
            cl (float): 곡선장
            sl (float): 외할장
            m (float): 중앙종거
            bc_azimuth (float): 시작 방위각 라디안
            ec_azimuth (float): 종료 방위각 라디안
        Returns:
            CurveSegment
        """
        return CurveSegment(
            radius=r,
            start_sta=bc_sta,
            end_sta=ec_sta,
            start_coord=bc_coord,
            end_coord=ec_coord,
            center_coord=center_coord,
            tl=tl,
            length=cl,
            sl=sl,
            m=m,
            start_azimuth=bc_azimuth,
            end_azimuth=ec_azimuth,
        )

    def define_spiral_spec(self, section: list[Curve], direction: CurveDirection) -> \
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