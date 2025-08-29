import math

from model.model import Curve, IPdata, CurveDirection, CurveSegment
from vector2 import Vector2

class Calculator:
    def __init__(self):
        self.bvedata = None
    def init_bvedata(self, bvedata):
        self.bvedata = bvedata

    def calculate_curve_type(self, curves: list[Curve]):
        curve_type = []
        for i in range(len(curves)):
            if i == 0:
                curve_type.append("BP")
            elif i == len(curves) - 1:
                curve_type.append("EP")
            elif curves[i].radius == 0:
                curve_type.append("EC")
            elif curves[i - 1].radius == 0 and curves[i].radius != 0:
                curve_type.append("BC")
            else:
                curve_type.append("PCC")

        return curve_type

    def calculate_curve_geometry(self):

        curves = self.bvedata.curves
        #call calculate_curve_type
        curvetype = self.calculate_curve_type(curves)
        IA = []
        O_XY = []
        BC_XY = []
        EC_XY = []
        EP_XY = []
        IP_XY = []
        BC_O_bearing = 0
        bearing = 0
        O_EC_bearing = 0  # O_EC_bearing 초기화

        O_XY_list = []
        BC_XY_list = []
        EC_XY_list = []
        bearing_list = []
        IP_XY_list = []

        IP_NUMBER = radius.count(0)
        interval_counter = 1  # Counter for interval numbering

        for i in range(len(stations)):

            if radius[i] == 0:  # 반지름이 0인 경우
                IA = 0
            else:
                IA = interval_distance[i + 1] / radius[i]

            if IA != 0:

                IA_DMS = math.degrees(IA)

                if curve_type[i] == 'PCC':  # 복심곡선
                    BC_XY = EC_XY
                elif i != 1:  # 초기 BC
                    BC_XY = EP_XY
                else:  # 그 외의경우
                    BC_XY = calculate_coordinates(BP_XY[0], BP_XY[1], BP_bearing, interval_distance[i])

                BC_O_bearing = bearing - 90 if i != 1 else BP_bearing - 90
                O_BC_bearing = BC_O_bearing + 180
                O_XY = calculate_coordinates(BC_XY[0], BC_XY[1], BC_O_bearing, radius[i])
                O_EC_bearing = O_BC_bearing - IA_DMS
                EC_XY = calculate_coordinates(O_XY[0], O_XY[1], O_EC_bearing, radius[i])
                bearing = O_EC_bearing - 90

                count = stations.count(0)
                count_radius = len(stations) - count
                if i >= len(stations) - 2 and len(stations) != count_radius * 2:  # 12
                    EP_XY = EC_XY
                else:

                    EP_XY = calculate_coordinates(EC_XY[0], EC_XY[1], bearing, interval_distance[i + 2])
                TL = radius[i] * math.tan(IA / 2)
                strate_bearing = bearing + IA_DMS  # bc점 방위각

                IP_XY = calculate_coordinates(BC_XY[0], BC_XY[1], strate_bearing, TL)

                # 여기에 출력
                print('--------------\n')
                print('IP NO ', interval_counter)  # Print the interval number
                interval_counter += 1  # Increment the interval counter
                print('IA= ', degrees_to_dms(IA_DMS))
                print('R= ', radius[i])
                print('TL= ', f"{TL:.2f}")
                print('CL= ', f"{interval_distance[i + 1]:.2f}")
                print('X= ', f"{IP_XY[1]:.4f}")
                print('Y=', f"{IP_XY[0]:.4f}")

                '''
                print('BC_XY', BC_XY)
                print('BC_O_bearing', BC_O_bearing)
                print('O_XY', O_XY)
                print('O_EC_bearing', O_EC_bearing)
                print('EC_XY', EC_XY)
                print('bearing', bearing)
                print('EP_XY', EP_XY)
                '''
                print('--------------\n')

                # 좌표를 리스트에 추가
                O_XY_list.append(O_XY)
                BC_XY_list.append(BC_XY)
                EC_XY_list.append(EC_XY)
                IP_XY_list.append(IP_XY)
                bearing_list.append(strate_bearing)

        return O_XY_list, BC_XY_list, EC_XY_list, EP_XY, IP_XY_list

    def calculate_interval_distance(self, stations, radius):

        CL = []

        for i in range(len(stations)):

            if i == 0:

                CL.append(0)

            else:

                CL.append(stations[i] - stations[i - 1])

        return CL

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

    def intersection_point(bc, theta1, ec, theta2):
        """
        bc: (x1, y1) 시작점
        theta1: 시작점 방향각 (라디안)
        ec: (x2, y2) 종점
        theta2: 종점 방향각 (라디안)
        """
        x1, y1 = bc
        x2, y2 = ec

        # 기울기

        m1 = math.tan(theta1)
        m2 = math.tan(theta2)

        # 두 직선이 평행한 경우
        if abs(m1 - m2) < 1e-9:
            return None

            # 직선 방정식: y = m*x + b
        b1 = y1 - m1 * x1
        b2 = y2 - m2 * x2

        # 교점 좌표 (x, y)
        x = (b2 - b1) / (m1 - m2)
        y = m1 * x + b1
        return (x, y)

    def split_by_curve_sections(self, curves: list[Curve]) -> list[list[Curve]]:
        """
        곡선 반경 리스트(curves)를 분석해,
        BC~EC 단위로 구간을 나눈다.
        """
        sections = []
        current_section = []

        for curve in curves:
            current_section.append(curve)

            # EC(=radius==0) 발견 → 구간 끊기
            if curve.radius == 0 and len(current_section) > 1:
                sections.append(current_section)
                current_section = []

        if current_section:  # 마지막 잔여 구간
            sections.append(current_section)

        return sections

    def build_ipdata_from_sections(self, sections: list[list[Curve]]) -> list[IPdata]:
        ipdata_list = []

        for ipno, section in enumerate(sections, 1):
            # 곡선 세그먼트 (BC ~ EC)
            bc_curve = section[0]
            ec_curve = section[-1]
            bc_sta = bc_curve.station #bc측점
            ec_sta = ec_curve.station #ec측점
            cl = ec_sta - bc_sta #곡선장
            # 곡선 방향 (반경 부호 or azimuth 비교로 결정 가능)
            curve_direction = CurveDirection.RIGHT if bc_curve.radius > 0 else CurveDirection.LEFT

            # 교각 ia
            r = abs(bc_curve.radius)
            ia = cl / r # 교각 계산함수(라디안)
            #클래스 생성
            curve_segment = CurveSegment(
                radius=r,
                bc_sta=bc_sta,
                ec_sta=ec_sta,
                bc_coord=bc_curve.coord,
                ec_coord=ec_curve.coord,
                center_coord=Vector2(0, 0),  # TODO: 원곡선 중심 좌표 계산 필요
                tl=0.0,
                cl=0.0,
                sl=0.0,
                m=0.0,
                start_azimuth=0.0,
                end_azimuth=0.0,
            )

            ipdata = IPdata(
                ipno=ipno,
                curvetype=CurveType.Simple,  # TODO: 조건에 따라 Simple / Compound
                curve_direction=curve_direction,
                radius=radius,
                ip_x_coord=ec_curve.coord.x,
                ip_y_coord=ec_curve.coord.y,
                ia=ia,
                curve_segment=curve_segment
            )

            ipdata_list.append(ipdata)

        return ipdata_list

