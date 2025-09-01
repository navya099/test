import math
import numpy as np
from math_utils import get_station_by_block_index, get_block_index
from model.model import Curve, IPdata, CurveDirection, CurveSegment, BVERouteData, CurveType
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

    def calculate_curve_type(self, curves: list[Curve])-> list[str]:
        """
        curve 리스트에서 곡선 타입을 계산하는 메소드
        Args:
            curves (list[Curve]): curves 리스트 [Curve.station, Curve.radius, Curve.cant]
        Returns:
            curve_type (list[str]): 곡선 타입 문자열 리스트 'BP','EP','BC','EC','PCC'
        """
        #리스트 초기화
        curve_type = []

        for i, curve in enumerate(curves):
            if i == 0:
                curve_type.append("BP")  # 시작점
            elif i == len(curves) - 1:
                curve_type.append("EP")  # 끝점
            elif curve.radius == 0:
                curve_type.append("EC")  # 곡선 종점
            elif curves[i - 1].radius == 0 and curve.radius != 0:
                curve_type.append("BC")  # 곡선 시작점
            else:
                curve_type.append("PCC")  # 복심곡선

        return curve_type

    def define_dirction(self, radius):
        result = []
        for a in radius:
            if a < 0:
                result.append(-1)
            elif a > 0:
                result.append(1)
            else:
                pass
        return result

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
        곡선 리스트(curves)를 분석해,
        BP + BC~EC 단위로 구간을 나눈다.

        Args:
            curves (list[Curve]): Curve 리스트

        Returns:
            sections (list[list[Curve]]): 구간이 분할된 리스트
                [BP, SEC1[BC~EC], SEC2[BC~EC], ...]
        """
        sections = []
        current_section = []

        for i, curve in enumerate(curves):
            current_section.append(curve)

            # BP 처리: 첫 요소가 radius==0이면 BP 섹션으로 바로 추가
            if i == 0:
                sections.append([curve])
                current_section = []
                continue

            # EC(=radius==0) 발견 → 구간 끊기
            if curve.radius == 0:
                if len(current_section) > 1:
                    sections.append(current_section)
                current_section = []

        # 마지막 남은 구간이 있다면 추가
        if current_section:
            sections.append(current_section)

        return sections

    def build_ipdata_from_sections(self) -> list[IPdata]:
        """
        BVERouteData객체의 속성을 이용해서 선형 객체를 만드는 메소드
        Returns:
            list(IPdata): IPdata객체 리스트
        """
        ipdata_list = []
        #구간 분할
        sections = self.split_by_curve_sections(self.bvedata.curves)

        coords = self.bvedata.coords
        directions = self.bvedata.directions

        #ip번호만큼 반복
        for i, section in enumerate(sections):
            if i == 0:
                continue
            ipno = i
            # 곡선 세그먼트 (BC ~ EC)
            bc_curve = section[0]
            ec_curve = section[-1]
            bc_sta = bc_curve.station #bc측점
            ec_sta = ec_curve.station #ec측점
            cl = ec_sta - bc_sta #곡선장
            radius = bc_curve.radius

            # 곡선 방향 (반경 부호 or azimuth 비교로 결정 가능)
            curve_direction = CurveDirection.RIGHT if radius > 0 else CurveDirection.LEFT

            #곡선 제원 계산
            r, ia, tl, m, sl = self._calculate_curve_geometry(radius, cl)

            #좌표 및 방위각 계산
            bc_coord, ec_coord, bc_azimuth, ec_azimuth = self._extract_coords_and_azimuth(bc_sta, ec_sta)

            #원곡선 중심 계산
            center_coord = self.calculate_curve_center(bc_coord, ec_coord, r, curve_direction)

            #ip좌표 계산
            ip_coord = self._calculate_ip_coord(bc_coord, ec_coord, bc_azimuth, ec_azimuth)

            #curve_segment 생성
            curve_segment = self._create_curve_segment(
                r, bc_sta, ec_sta, bc_coord, ec_coord, center_coord,
                tl, cl, sl, m, bc_azimuth, ec_azimuth
            )

            #ipdata 생성
            ipdata = IPdata(
                ipno=ipno,
                curvetype=CurveType.Simple,  # TODO: 조건에 따라 Simple / Compound
                curve_direction=curve_direction,
                radius=r,
                ip_coord=ip_coord,
                ia=ia,
                curve_segment=curve_segment
            )

            ipdata_list.append(ipdata)

        return ipdata_list

    def calculate_curve_center(self, bc_xy: Vector3, ec_xy: Vector3, radius: float, direction: CurveDirection) -> Vector2:
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
        Private메소드 단곡선 좌표 및 방위각 추출
        Args:
            bc_sta(float): bc측점
            ec_sta(float): ec측점
        Returns:
            bc_coord(Vector3):
            ec_coord(Vector3):
            bc_azimuth(Vector3):
            ec_azimuth(Vector3):
        """
        #중복 제거후 매핑데이터 생성
        station_to_data = {
            curve.station: (coord, dir)
            for curve, coord, dir in zip(self.bvedata.curves, self.bvedata.coords, self.bvedata.directions)
        }

        # 좌표와 방위각 추출
        bc_coord, bc_azimuth = station_to_data[bc_sta]
        ec_coord, ec_azimuth = station_to_data[ec_sta]

        return bc_coord, ec_coord, bc_azimuth, ec_azimuth

    def _calculate_ip_coord(self, bc_xy, ec_xy, bc_azimuth, ec_azimuth) -> Vector2:
        """
        Private 메소드: IP 좌표 계산
        Args:
            bc_xy (Vector3): BC 좌표
            ec_xy (Vector3): EC 좌표
            bc_azimuth (Vector3): BC 방위각 벡터
            ec_azimuth (Vector3): EC 방위각 벡터
        Returns:
            Vector2: IP 좌표
        """
        #Vector2로 변환 수행
        bc_azimuth = to2d(bc_azimuth)
        ec_azimuth = to2d(ec_azimuth)
        #라디안 변환 수행
        bc_azimuth = bc_azimuth.toradian()
        ec_azimuth = ec_azimuth.toradian()
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
            bc_azimuth (float): 시작 방위각
            ec_azimuth (float): 종료 방위각
        Returns:
            CurveSegment
        """
        return CurveSegment(
            radius=r,
            bc_sta=bc_sta,
            ec_sta=ec_sta,
            bc_coord=bc_coord,
            ec_coord=ec_coord,
            center_coord=center_coord,
            tl=tl,
            cl=cl,
            sl=sl,
            m=m,
            start_azimuth=bc_azimuth,
            end_azimuth=ec_azimuth,
        )
