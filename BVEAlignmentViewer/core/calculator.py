import math
import numpy as np
from math_utils import get_station_by_block_index, get_block_index
from model.model import Curve, IPdata, CurveDirection, CurveSegment, BVERouteData, CurveType, EndPoint
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

    def calculate_intersection_point(self, bc, ec, theta1, theta2)-> Vector2 | None:
        """
        교점을 찾는 메소드
        bc: (x1, y1) 곡선시작점
        theta1: 시작점 방향각 (라디안)
        ec: (x2, y2) 곡선종점
        theta2: 종점 방향각 (라디안)
        Returns:
            ip: (Vector2): IP좌표
        """
        x1, y1 = bc.x, bc.y
        x2, y2 = ec.x, ec.y

        # 수직선 처리
        if math.isclose(math.cos(theta1), 0.0):
            if math.isclose(math.cos(theta2), 0.0):
                return None
            return Vector2(x1, math.tan(theta2) * x1 + y2 - math.tan(theta2) * x2)
        elif math.isclose(math.cos(theta2), 0.0):
            return Vector2(x2, math.tan(theta1) * x2 + y1 - math.tan(theta1) * x1)

        m1 = math.tan(theta1)
        m2 = math.tan(theta2)

        if math.isclose(m1, m2):
            return None

        b1 = y1 - m1 * x1
        b2 = y2 - m2 * x2

        x = (b2 - b1) / (m1 - m2)
        y = m1 * x + b1

        return Vector2(x,y)

    def split_by_curve_sections(self, curves: list[Curve]) -> list[list[Curve]]:
        """
        곡선 리스트를 분석해 구간을 나누되,
        복심곡선이면 PCC 기준으로 2개 구간으로 분할.
        방향 전환 시에는 경계 곡선을 양쪽 구간에 포함.
        """
        sections = []
        current_section = []
        prev_radius = None

        for i, curve in enumerate(curves):
            # BP 처리
            if i == 0:
                sections.append([curve])
                prev_radius = curve.radius
                continue

            current_section.append(curve)

            # 방향 전환 감지
            if prev_radius is not None and prev_radius * curve.radius < 0:
                sections.append(current_section[:])
                current_section = [curve]

            # 곡선 타입 판단
            curvetype = self.define_iscurve(current_section)
            if curvetype == CurveType.Complex:
                # PCC 곡선(중간) 분할
                pcc_curve = current_section[1]
                sections.append(current_section[:2])  # BC~PCC
                sections.append(current_section[1:])  # PCC~EC
                current_section = []

            # EC 처리
            if curve.radius == 0:
                if current_section:
                    sections.append(current_section)
                current_section = []

            prev_radius = curve.radius

        # 남은 구간 처리
        if current_section:
            sections.append(current_section)

        return sections

    def build_ipdata_from_sections(self) -> list[IPdata]:
        """
        BVERouteData 속성으로 IPdata 리스트 생성.
        BP -> 곡선 -> EP 순서 처리
        """
        ipdata_list = []
        sections = self.split_by_curve_sections(self.bvedata.curves)

        for i, section in enumerate(sections):
            if i ==0:
                # BP
                ipdata_list.append(self._process_endpoint(bp=True))
            else:#곡선구간 처리
                ipdata_list.append(self._process_curve_section(section, ipno=i))

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


        # 안전장치: 기본값
        return CurveType.NONE

    def define_section_radius(self, section: list[Curve]) -> tuple[float, float]:
        """
        구간내 곡선반경 찾기
        Args:
            section:  Curve객체 리스트

        Returns:
            radius (tuple[float, float]): 찾은 반경 리스트(복심곡선용)
        """
        radius2 = 0.0
        #곡선 타입 호출
        curvetype = self.define_iscurve(section)
        if curvetype == CurveType.Simple:
            radius = section[0].radius
        elif curvetype == CurveType.Complex:
            radius = section[0].radius
            radius2 = section[1].radius
        else:
            #첫번째 요소만 보고 판단
            isminus = (section[0].radius < 0)
            # 0 제외한 반경만 뽑기
            nonzero_radii = [sec.radius for sec in section if sec.radius != 0]

            if isminus:
                radius = max(nonzero_radii)
            else:
                radius = min(nonzero_radii)
        return radius, radius2

    def _process_curve_section(self, section: list[Curve], ipno: int) -> IPdata:
        """곡선 구간 처리 메인"""
        curvetype = self.define_iscurve(section)

        if curvetype == CurveType.Simple:
            return self._process_simple_curve(section, ipno)
        elif curvetype == CurveType.Complex:
            return self._process_complex_curve(section, ipno)
        elif curvetype == CurveType.Spiral:
            return self._process_spiral_curve(section, ipno)
        else:
            raise ValueError(f"Unknown CurveType: {curvetype}")

    # ---------------------
    # 단곡선 처리
    def _process_simple_curve(self, section: list[Curve], ipno: int) -> IPdata:
        bc_curve, ec_curve = section[0], section[-1]
        bc_sta, ec_sta = bc_curve.station, ec_curve.station
        cl = ec_sta - bc_sta
        r, _ = self.define_section_radius(section)
        curve_direction = CurveDirection.RIGHT if r > 0 else CurveDirection.LEFT

        r, ia, tl, m, sl = self._calculate_curve_geometry(r, cl)
        bc_coord, ec_coord = bc_curve.coord, ec_curve.coord
        bc_azimuth, ec_azimuth = bc_curve.direction, ec_curve.direction
        center_coord = self.calculate_curve_center(bc_coord, ec_coord, r, curve_direction)
        ip_coord = self._calculate_ip_coord(bc_coord, ec_coord, bc_azimuth, ec_azimuth)

        curve_segment = self._create_curve_segment(r, bc_sta, ec_sta,
                                                   bc_coord, ec_coord, center_coord,
                                                   tl, cl, sl, m,
                                                   bc_azimuth, ec_azimuth)
        return IPdata(ipno=ipno,
                      curvetype=CurveType.Simple,
                      curve_direction=curve_direction,
                      radius=r,
                      ia=ia,
                      coord=ip_coord,
                      segment=[curve_segment])

    # ---------------------
    # 복심곡선 처리
    def _process_complex_curve(self, section: list[Curve], ipno: int) -> IPdata:
        """
        복심곡선 처리 메소드
        Args:
            section: 구간
            ipno: ip번호

        Returns:
            IPdata
        """
        #BC,PCC,EC 언팩
        bc_curve, pcc_curve, ec_curve = section[0], section[1], section[-1]
        bc_sta, pcc_sta, ec_sta = bc_curve.station, pcc_curve.station, ec_curve.station
        # 전체 cl
        cl = ec_sta - bc_sta
        #개별 cl
        cl1, cl2 = pcc_sta - bc_sta, ec_sta - pcc_sta
        cl_list = cl1 , cl2
        radii = self.define_section_radius(section)
        #복심곡선 반경1, 반경2
        r1,r2 = radii
        curve_direction = CurveDirection.RIGHT if r1 > 0 else CurveDirection.LEFT
        curve_segment_list = []

        #개별 R별 처리
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
                self._create_curve_segment(r,bc_sta, ec_sta,
                                           bc_coord, ec_coord, center_coord,
                                           tl, cl, sl, m,
                                           bc_azimuth, ec_azimuth)
            )
        #대표 IP제원 다시계산
        ia = sum(ia_list)
        ip_coord = self._calculate_ip_coord(bc_curve.coord, ec_curve.coord, bc_curve.direction, ec_curve.direction)
        return IPdata(ipno=ipno,
                      curvetype=CurveType.Complex,
                      curve_direction=curve_direction,
                      radius=radii,
                      ia=ia,
                      coord=ip_coord,
                      segment=curve_segment_list)

    # ---------------------
    # 완화곡선 처리
    def _process_spiral_curve(self, section: list[Curve], ipno: int) -> IPdata:
        bc_curve, ec_curve = section[0], section[-1]
        bc_sta, ec_sta = bc_curve.station, ec_curve.station
        cl = ec_sta - bc_sta
        r, _ = self.define_section_radius(section)
        curve_direction = CurveDirection.RIGHT if r > 0 else CurveDirection.LEFT

        r, ia, tl, m, sl = self._calculate_curve_geometry(r, cl)
        bc_coord, ec_coord = bc_curve.coord, ec_curve.coord
        bc_azimuth, ec_azimuth = bc_curve.direction, ec_curve.direction
        center_coord = self.calculate_curve_center(bc_coord, ec_coord, r, curve_direction)
        ip_coord = self._calculate_ip_coord(bc_coord, ec_coord, bc_azimuth, ec_azimuth)

        curve_segment = self._create_curve_segment(r, bc_sta, ec_sta,
                                                   bc_coord, ec_coord, center_coord,
                                                   tl, cl, sl, m,
                                                   bc_azimuth, ec_azimuth)
        return IPdata(ipno=ipno,
                      curvetype=CurveType.Simple,
                      curve_direction=curve_direction,
                      radius=r,
                      ia=ia,
                      coord=ip_coord,
                      segment=[curve_segment])
    def calculate_curve_center(self, bc_xy: Vector2, ec_xy: Vector2, radius: float, direction: CurveDirection) -> Vector2:
        """
        bc좌표와 ec좌표 r 방향으로 원곡선 중심 계산하는 메소드
        Args:
            bc_xy:
            ec_xy:
            radius:
            direction:

        Returns:
            Vector2:  원곡선 중심 좌표
        """
        # BC → EC 방위각
        dx = ec_xy.x - bc_xy.x
        dy = ec_xy.y - bc_xy.y
        theta = math.atan2(dy, dx)  # 라디안

        # 곡선 방향에 따른 수직 방위각
        if direction == direction.RIGHT:
            theta_perp = theta - math.pi / 2
        else:  # LEFT
            theta_perp = theta + math.pi / 2

        # 중심 좌표 계산
        cx = bc_xy.x + radius * math.cos(theta_perp)
        cy = bc_xy.y + radius * math.sin(theta_perp)

        return Vector2(cx, cy)

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

    def _extract_coords_and_azimuth(self, bc_sta, ec_sta):
        """
        Private메소드 단곡선 좌표 및 방위각 각도 추출
        Args:
            bc_sta(float): bc측점
            ec_sta(float): ec측점
        Returns:
            bc_coord(Vector2):
            ec_coord(Vector2):
            bc_azimuth(float): 시작 각도 라디안
            ec_azimuth(float): 끝 각도 라디안
        """
        #중복 제거후 매핑데이터 생성
        station_to_data = {
            curve.station: (coord, dir)
            for curve, coord, dir in zip(self.bvedata.curves, self.bvedata.coords, self.bvedata.directions)
        }

        # 좌표와 방위각 추출
        bc_coord, bc_azimuth = station_to_data[bc_sta]
        ec_coord, ec_azimuth = station_to_data[ec_sta]

        #3d벡터를 2d벡터로 변환
        bc_coord = to2d(bc_coord)
        bc_azimuth = to2d(bc_azimuth)
        ec_coord = to2d(ec_coord)
        ec_azimuth = to2d(ec_azimuth)

        #라디안 변환 수행
        bc_azimuth = bc_azimuth.toradian()
        ec_azimuth = ec_azimuth.toradian()

        return bc_coord, ec_coord, bc_azimuth, ec_azimuth

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