import math
import numpy as np
from math_utils import get_station_by_block_index, get_block_index
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

    def _process_curve_section(self, section: list[Curve], ipno: int) -> IPdata:
        """곡선 구간 처리 메인"""
        curvetype = self.define_iscurve(section)

        if curvetype == CurveType.Simple or curvetype == CurveType.Reverse:
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

    def _create_spiral_curve_segment(self):
        """
        완화곡선 세그먼트 생성 메소드
        Returns:
            SpiralSegment
        """
        return SpiralSegment()
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