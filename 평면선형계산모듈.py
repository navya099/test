# 평면선형 계산 테스트
import math
from dataclasses import dataclass
from enum import Enum

'''
hor_option = [
            '시작측점 누가거리',
            '시작 IP번호',
            '측점 표시방법(STA)',
            '측점 표시방법(NO)',
            '측점 계산 간격'
            ]
'''

class VisibleType(Enum):
    """
    출력/표시 유형을 나타내는 Enum 클래스.

    Attributes:
        STA (int): STA형식 출력
        NO (int): NO형식 출력
    """
    STA = 0
    NO = 1

@dataclass
class HorOption:
    """
    HorOption은 평면선형 계산 옵션을 저장하는 데이터 클래스입니다.

    Attributes:
        start_sta (float): 계산 시작 위치(STA)
        start_ip_number (float): 시작 IP 번호
        visible_type (VisibleType): 출력/표시 유형 (예: STA, NO 등)
        calculation_distance (float): 계산 간격
    """
    start_sta: float = 0.0
    start_ip_number: float = 0.0
    visible_type: VisibleType = VisibleType.STA  # 실제 VisibleType Enum 참조
    calculation_distance: float = 0.0


@dataclass
class HorizonInputData:
    """
    HorizonInputData는 평면선형 계산을 위한 입력 데이터를 저장하는 데이터 클래스입니다.

    Attributes:
        ipnumber (int): 해당 IP (Intersection Point) 번호
        ip_x_coord (float): IP의 X 좌표
        ip_y_coord (float): IP의 Y 좌표
        radius (float): 곡선 반경
        A1 (float): 시작 클로소이드 파라미터 A1
        A2 (float): 종료 클로소이드 파라미터 A2
    """
    ipnumber: int = 0
    ip_x_coord: float = 0.0
    ip_y_coord: float = 0.0
    radius: float = 0.0
    A1: float = 0.0
    A2: float = 0.0


@dataclass
class SimpleCurve:
    """
    SimpleCurve는 평면 곡선 요소 계산 결과를 저장하는 데이터 클래스입니다.

    Attributes:
        tangent_len (float): 접선 거리(T)
        arc_len (float): 곡선 길이(L)
        external (float): 곡선 편심(E)
        mid_ord (float): 곡선 높이 변화(M)
        chord_len (float): 곡선 현 길이(C)
        direction (int): 곡선 진행 방향 플래그 (0: 정상, 1: 역방향)
    """
    tangent_len: float = 0.0
    arc_len: float = 0.0
    external: float = 0.0
    mid_ord: float = 0.0
    chord_len: float = 0.0
    direction: int = 0

@dataclass
class ClothoidCurve:
    """
    ClothoidCurve는 클로소이드 곡선 계산 결과를 저장하는 데이터 클래스입니다.

    Attributes:
        T (float): 타우
        shift (float): 이정량
        dist (float): 이정거리
        delta (float): 곡선 변화각
        arc_len (float): 곡선 아크 길이
        length (float): 클로소이드 길이
        X (float): 클로소이드 횡거 X
        Y (float): 클로소이드 횡거 Y
        theta (float): 클로소이드 각도
        Yc (float): 보정된 Y 좌표
        Xc (float): 보정된 X 좌표
        TL (float): 접선 길이 보정
        tan_off (float): 접선 오프셋
        phi (float): 클로소이드 회전각
        R_eff (float): 유효 반경
    """
    T: float = 0.0
    shift: float = 0.0
    dist: float = 0.0
    delta: float = 0.0
    arc_len: float = 0.0
    length: float = 0.0
    X: float = 0.0
    Y: float = 0.0
    theta: float = 0.0
    Yc: float = 0.0
    Xc: float = 0.0
    TL: float = 0.0
    tan_off: float = 0.0
    phi: float = 0.0
    R_eff: float = 0.0

@dataclass
class HorResult:
    ip_va: list       # VIP 정보 리스트
    gou: list         # 곡선 각 리스트
    ip_list: list     # 단순 곡선 리스트
    bang: list        # 방위각 리스트
    clothoid_list: list  # 클로소이드 리스트

@dataclass
class IPVA:
    """
    VIP(Virtual Intersection Point) 정보를 나타내는 데이터 클래스입니다.

    Attributes:
        curvetype (int): 곡선 구분 (예: 단곡선, 복곡선 등).
        iptype (int): VIP의 종류 구분 (예: 시작점, 종점 등).
        sta (float): 측점, 노선 상의 위치.
        x (float): X 좌표 (평면상 좌표).
        y (float): Y 좌표 (평면상 좌표).
        r (float): 곡선 반경.
        a1 (float): 클로소이드 시점 파라미터 A1.
        a2 (float): 클로소이드 종점 파라미터 A2.
        bang (float): 방위각 (라디안 단위).
    """
    curvetype: int       # 곡선 구분
    iptype: int          # 종류 구분
    sta: float           # 측점
    x: float             # X좌표
    y: float             # Y좌표
    r: float             # 반경
    a1: float            # 클로소이드 A1
    a2: float            # 클로소이드 A2
    bang: float          # 방위각


@dataclass
class BCDATA:
    """
    곡선 시작점(BC, Begin of Curve) 좌표를 저장하는 데이터 클래스.

    Attributes:
        bc_x (float): BC의 X 좌표
        bc_y (float): BC의 Y 좌표
    """
    bc_x: float = 0.0
    bc_y: float = 0.0

@dataclass
class ECDATA:
    """
    곡선 종료점(EC, End of Curve) 좌표를 저장하는 데이터 클래스.

    Attributes:
        ec_x (float): EC의 X 좌표
        ec_y (float): EC의 Y 좌표
    """
    ec_x: float = 0.0
    ec_y: float = 0.0

@dataclass
class BTCDATA:
    """
    곡선 전 클로소이드 종료점(BTC, Begin of Transition Curve) 좌표를 저장하는 데이터 클래스.

    Attributes:
        btc_x (float): BTC의 X 좌표
        btc_y (float): BTC의 Y 좌표
    """
    btc_x: float = 0.0
    btc_y: float = 0.0

@dataclass
class ETCDATA:
    """
    곡선 후 클로소이드 시작점(ETC, End of Transition Curve) 좌표를 저장하는 데이터 클래스.

    Attributes:
        etc_x (float): ETC의 X 좌표
        etc_y (float): ETC의 Y 좌표
    """
    etc_x: float = 0.0
    etc_y: float = 0.0



class HorCalqu:
    """HorCalqu"""

    def __init__(self):
        self.rows = []
        self.sta = 0.0

    def print_dxf(self, hor_option):
        pass

    def print_xlsx(self, hor_option):
        pass


    def basic_calqu(self, hor_option: HorOption, rows: list[HorizonInputData]):
        self.rows = rows
        ip_count = len(self.rows)
        self.sta = hor_option.start_sta #시작 측점 누가거리
        gan = hor_option.calculation_distance #계산 간격 DEFAULT 20.00
        ip_va = []  # 최종 VIP/곡선 점 계산값 저장
        lo = []  # 구간 길이
        gou = []  # 각도 변화량
        ip_list = []  # IP 관련 계산값
        bc_list = []  # 시작점 좌표 (Begin Coordinate)
        ec_list = []  # 종료점 좌표 (End Coordinate)
        btc_list = []  # BTC 좌표 (보조)
        etc_list = []  # ETC 좌표 (보조)
        bang = []  # 방위각 각도(방향)
        clothoid_list = []  # 클로소이드 계산용 배열
        for i in range(0, ip_count - 1):
            #초기에 각 ip별 빈 리스트 생성
            lo.append(0)
            gou.append(0)
            ip_list.append(SimpleCurve())
            bc_list.append(BCDATA())
            ec_list.append(ECDATA())
            btc_list.append(BTCDATA())
            etc_list.append(ETCDATA())
            bang.append(0)
            clothoid_list.append([ClothoidCurve(),ClothoidCurve()]) #시점측 종점측 두개 생성
        back = 0

        try:
            for i in range(0, ip_count - 1):
                # ----- 2. 곡선 요소 계산 -----
                ipnumber = self.rows[i].ipnumber
                ip_x_coord = self.rows[i].ip_x_coord
                next_ip_x_coord = self.rows[i + 1].ip_x_coord
                ip_y_coord = self.rows[i].ip_y_coord
                next_ip_y_coord = self.rows[i + 1].ip_y_coord
                radius = self.rows[i].radius
                clothoid_a1 = self.rows[i].A1
                clothoid_a2 = self.rows[i].A2

                # 두 점 사이의 직선 거리 계산 (유클리드 거리)
                temp_ip_dist = math.hypot(
                    next_ip_x_coord - ip_x_coord,  # ΔX
                    next_ip_y_coord - ip_y_coord # ΔY
                )

                # 두 점의 X 좌표가 같으면 수직선 처리
                if next_ip_x_coord == ip_x_coord:
                    if ip_y_coord > next_ip_y_coord:
                        temp_bang_yui = math.pi * -1 / 2  # -90도 (아래 방향)
                    else:
                        temp_bang_yui = math.pi / 2  # 90도 (위 방향)
                else:
                    # 일반적인 두 점의 방향 각도 계산 (atan2 대신 atan 사용)
                    temp_bang_yui = math.atan(
                        (next_ip_y_coord - ip_y_coord) /
                        (next_ip_x_coord - ip_x_coord)
                    )

                # 추가 보정: X 좌표 증가 방향에 따라 각도 조정
                if ip_x_coord <= next_ip_x_coord:
                    if ip_y_coord > next_ip_y_coord:
                        temp_bang_yui = temp_bang_yui + math.pi * 2  # 아래쪽 이동 시 보정
                    else:
                        temp_bang_yui = temp_bang_yui + math.pi  # 위쪽 이동 시 보정

                # 계산된 거리와 각도를 리스트에 저장
                lo[i] = temp_ip_dist  # 점 i~i+1 사이 거리
                bang[i] = temp_bang_yui  # 점 i~i+1 사이 방향 각도

            # 첫 번째 곡선 각도 초기화
            gou[0] = 0  # 첫 점에서는 곡선 각도 0으로 초기화
            for i in range(1, ip_count - 1):
                # 1. 각 점에서의 방향 변화(gou) 계산
                if bang[i] >= bang[i - 1]:
                    gou[i] = bang[i] - bang[i - 1]  # 이전 방향보다 증가
                else:
                    gou[i] = bang[i - 1] - bang[i]  # 이전 방향보다 감소

                # 각도가 180도 이상이면 보정
                if gou[i] > math.pi:
                    gou[i] = 2 * math.pi - gou[i]

                # back 방향 계산: 이전 점의 반대 방향
                if bang[i - 1] >= math.pi:
                    back = bang[i - 1] - math.pi
                else:
                    back = bang[i - 1] + math.pi

                # ----- 2. 곡선 요소 계산 -----
                ipnumber = self.rows[i].ipnumber
                ip_x_coord = self.rows[i].ip_x_coord
                ip_y_coord = self.rows[i].ip_y_coord
                radius = self.rows[i].radius
                clothoid_a1 = self.rows[i].A1
                clothoid_a2 = self.rows[i].A2

                tangent_len = radius * math.tan(gou[i] / 2)  # 접선 거리 T
                arc_len = radius * gou[i]  # 곡선 길이 L
                external = radius * (1 / math.cos(gou[i] / 2) - 1)  # 편심 E
                mid_ord = radius * (1 - math.cos(gou[i] / 2))  # 높이 변화 M
                chord_len = 2 * radius * math.sin(gou[i] / 2)  # 현 길이 C
                direction = 0 if bang[i] > bang[i - 1] else 1  # 방향 플래그 # 0 = 정방향, 1 = 역방향

                # 배열에 저장
                ip_list[i].tangent_len = tangent_len
                ip_list[i].arc_len = arc_len
                ip_list[i].external = external
                ip_list[i].mid_ord = mid_ord
                ip_list[i].chord_len = chord_len
                ip_list[i].direction = direction

                # 3. 각도 예외 처리: 반시계/시계 방향 보정
                if math.pi * 2 > bang[i - 1] > math.pi:
                    if bang[i - 1] - math.pi >= bang[i] >= 0:
                        ip[i][5] = 0
                    elif bang[i - 1] + math.pi <= bang[i] <= 2 * math.pi:
                        ip[i][5] = 1

                # 4. 클로소이드 시점 우측  제원 계산
                '''
                for k in range(0, 2): # 0=시점쪽, 1=종점쪽 
                    if self.rows[i][4 + k] == 0: # 클로소이드 A2값이 0이면 초기화(단곡선) 
                        for j in range(5, 15): 
                            clothoid_list[i][k][j] = 0 
                        continue
                '''
                for k in range(0, 2):  # 0=시점쪽, 1=종점쪽
                    if self.rows[i].A1 == 0 and self.rows[i].A2 == 0:
                        c = clothoid_list[i][k]
                        c.length = c.X = c.Y = 0.0
                        c.theta = c.Yc = c.Xc = c.TL = 0.0
                        c.tan_off = c.phi = c.R_eff = 0.0

                    # 곡선 요소 기반 계산
                    if k == 0:
                        L = self.rows[i].A1 ** 2 / radius  # 클로소이드 길이
                    elif k == 1:
                        L = self.rows[i].A2 ** 2 / radius
                    X = self.jclox(L, radius)  # 클로소이드 횡거 X
                    Y = self.jcloy(L, radius)  # 클로소이드 종거 Y
                    theta = (L / 2) * radius  # 진행각(가정)

                    Xc = X - (radius * math.sin(theta))  # 접합 X좌표
                    Yc = Y + ((radius * math.cos(theta)) - radius)  # 접합 Y좌표
                    tan_len = Y / math.sin(theta)  # 보정값1
                    tan_off = X - Y / math.tan(theta)  # 보정값2
                    phi = math.atan(Y / X)  # 진행각(라디안)
                    R_eff = Y / math.sin(phi)  # 환산 반경

                    # 배열에 넣기
                    clothoid_list[i][k].length = L
                    clothoid_list[i][k].X = X
                    clothoid_list[i][k].Y = Y
                    clothoid_list[i][k].theta = theta
                    clothoid_list[i][k].Yc = Yc
                    clothoid_list[i][k].Xc = Xc
                    clothoid_list[i][k].TL = tan_len
                    clothoid_list[i][k].tan_off = tan_off
                    clothoid_list[i][k].phi = phi
                    clothoid_list[i][k].R_eff = R_eff

                # ----- 5. clo[i] 좌표 기반 최종 위치 계산 -----
                T = (radius + Yc) * math.tan(gou[i] / 2)  # 접선 길이
                start_Yc = clothoid_list[i][0].Yc
                end_Yc = clothoid_list[i][1].Yc
                shift_tan = (start_Yc - end_Yc) / math.tan(gou[i])  # 보정값 (tan)
                shift_sin = (start_Yc - end_Yc) / math.sin(gou[i])  # 보정값 (sin)

                start_Xc = clothoid_list[i][0].Xc
                end_Xc = clothoid_list[i][1].Xc

                dist_start = start_Xc + T - shift_tan  # 시작점 보정거리
                dist_end = end_Xc + T + shift_sin  # 종료점 보정거리

                start_theta = clothoid_list[i][0].theta
                end_theta = clothoid_list[i][1].theta
                delta = gou[i] - start_theta + end_theta  # 중심각 Δ
                arc_len = radius * delta  # 원호 길이 = R * Δ

                # ----- 6. 곡선 시작/종료 좌표 계산 -----
                btc_x = ip_x_coord + dist_start * math.cos(back)
                btc_y = ip_y_coord + dist_start * math.sin(back)
                etc_x = ip_x_coord + dist_end * math.cos(bang[i])
                etc_y = ip_x_coord + dist_end * math.sin(bang[i])

                # ----- 배열에 저장 -----
                clothoid_list[i][0].T = clothoid_list[i][1].T = T
                clothoid_list[i][0].shift = shift_tan
                clothoid_list[i][1].shift = shift_sin
                clothoid_list[i][0].dist = dist_start
                clothoid_list[i][1].dist = dist_end
                clothoid_list[i][0].delta = clothoid_list[i][1].delta = delta
                clothoid_list[i][0].arc_len = clothoid_list[i][1].arc_len = arc_len

                btc_list[i].btc_x, btc_list[i].btc_y = btc_x, btc_y
                etc_list[i].etc_x, etc_list[i].etc_y = etc_x, etc_y

                # 7. 곡선 진행 각도 계산 (s1, s2)
                if ip_list[i].direction == 0:
                    s1 = self.j_hab(bang[i - 1], clothoid_list[i][0].phi)
                    if bang[i] >= math.pi:
                        back = bang[i] - math.pi
                    else:
                        back = bang[i] + math.pi
                    s2 = self.j_cha(back, clothoid_list[i][1].phi)
                else:
                    s1 = self.j_cha(bang[i - 1], clothoid_list[i][0].phi)
                    if bang[i] >= math.pi:
                        back = bang[i] - math.pi
                    else:
                        back = bang[i] + math.pi
                    s2 = self.j_hab(back, clothoid_list[i][1].phi)

                # ----- 8. 최종 곡선 좌표 계산 -----

                # 곡선 시작점 BC
                bc_x = btc_list[i].btc_x + clothoid_list[i][0].R_eff * math.cos(s1)
                bc_y = btc_list[i].btc_y + clothoid_list[i][0].R_eff * math.sin(s1)

                # 곡선 끝점 EC
                ec_x = etc_list[i].etc_x + clothoid_list[i][1].R_eff * math.cos(s2)
                ec_y = etc_list[i].etc_y + clothoid_list[i][1].R_eff * math.sin(s2)

                # 배열에 저장
                bc_list[i].bc_x = bc_x
                bc_list[i].bc_y = bc_y
                ec_list[i].ec_x = ec_x
                ec_list[i].ec_y = ec_y

        finally:
            pass
        print('계산이 완료되었습니다.')

        j_g = 0
        j_what = ip_list[1].direction
        j_sta = 0
        j_x = self.rows[0].ip_x_coord #시작 x좌표
        j_y = self.rows[0].ip_y_coord #끝 y좌표
        j_r = 0
        j_a1 = 0
        j_a2 = 0
        j_bang = bang[0]
        ip_va.append(IPVA(j_g, j_what, j_sta, j_x, j_y, j_r, j_a1, j_a2, j_bang))
        # VIP(Intersection Point)별로 좌표와 곡선 정보 계산
        for i in range(1, ip_count - 1):

            direction = ip_list[1].direction


            arc_len = clothoid_list[i][0].arc_len # 호 길이
            start_L = clothoid_list[i][0].length  # 시점측 클로소이드길이
            end_L = clothoid_list[i][1].length
            start_theta = clothoid_list[i][0].theta
            end_theta = clothoid_list[i][1].theta

            # 곡선 시작점 정보 추가
            btc_x, btc_y = btc_list[i].btc_x, btc_list[i].btc_y
            bc_x, bc_y = bc_list[i].bc_x, bc_list[i].bc_y
            ec_x, ec_y = ec_list[i].ec_x, ec_list[i].ec_y
            etc_x, etc_y = etc_list[i].etc_x, etc_list[i].etc_y

            # ----- 2. 곡선 요소 계산 -----
            ipnumber = self.rows[i].ipnumber
            ip_x_coord = self.rows[i].ip_x_coord
            ip_y_coord = self.rows[i].ip_y_coord
            radius = self.rows[i].radius
            clothoid_a1 = self.rows[i].A1
            clothoid_a2 = self.rows[i].A2

            if start_L != 0: #클로소이드 곡선 길이가 0이 아닌경우


                j_g = 5  # 구간 타입 코드 (5 = 곡선 시작점)
                j_what = direction  # 좌우 방향 정보
                j_sta = self.jround(j_sta + math.hypot(j_x - btc_x, j_y - btc_y), 5)  # 거리 누적
                j_x = self.jround(btc_x, 5)  # x좌표
                j_y = self.jround(btc_y, 5)  # y좌표
                j_r = radius  # 곡선 반경
                j_a1 = clothoid_a1  # 시점측 클로소이드 매개변수 A1
                j_a2 = clothoid_a2  # 종점측 클로소이드 매개변수 A2
                j_bang = bang[i - 1]  # 이전 방위각
                ip_va.append(IPVA(j_g, j_what, j_sta, j_x, j_y, j_r, j_a1, j_a2, j_bang))

                # 곡선 중간점 정보 추가
                j_g = 1  # 구간 타입 코드 (1 = 곡선 중간점)
                j_what = direction
                j_sta = self.jround(j_sta + L, 5)  # 좌측 곡선 거리
                j_x = self.jround(bc_x, 5)  # 중간 x
                j_y = self.jround(bc_y, 5)  # 중간 y
                j_r = radius
                j_a1 = clothoid_a1
                j_a2 = clothoid_a2

                # 곡선 진행 방향에 따라 방위각 계산
                if j_what == 0:
                    j_bang = self.j_hab(bang[i - 1],start_theta)
                else:
                    j_bang = self.j_cha(bang[i - 1], start_theta)
                ip_va.append(IPVA(j_g, j_what, j_sta, j_x, j_y, j_r, j_a1, j_a2, j_bang))

            # 좌측 곡선이 없으면 곡선 중간점만 추가
            else:
                j_g = 1
                j_what = direction
                j_sta = self.jround(j_sta + math.hypot(j_x - bc_x, j_y - bc_y), 5)
                j_x = self.jround(bc_x, 5)
                j_y = self.jround(bc_y, 5)
                j_r = radius
                j_a1 = clothoid_a1
                j_a2 = clothoid_a1
                j_bang = bang[i - 1]
                ip_va.append(IPVA(j_g, j_what, j_sta, j_x, j_y, j_r, j_a1, j_a2, j_bang))

            # 우측 곡선(clo[i][1])이 존재하면
            if end_L != 0:
                # 곡선 중간점
                j_g = 2
                j_what = direction
                j_sta = self.jround(j_sta + arc_len, 5)
                j_x = self.jround(ec_x, 5)
                j_y = self.jround(ec_y, 5)
                j_r = radius
                j_a1 = clothoid_a1
                j_a2 = clothoid_a2

                if j_what == 0:
                    j_bang = self.j_cha(bang[i], end_theta)
                else:
                    j_bang = self.j_hab(bang[i], end_theta)
                ip_va.append(IPVA(j_g, j_what, j_sta, j_x, j_y, j_r, j_a1, j_a2, j_bang))

                # 곡선 끝점
                j_g = 6
                j_what = direction
                j_sta = self.jround(j_sta + end_L, 5)
                j_x = self.jround(etc_x, 5)
                j_y = self.jround(etc_y, 5)
                j_r = radius
                j_a1 = clothoid_a1
                j_a2 = clothoid_a2
                j_bang = bang[i]
                ip_va.append(IPVA(j_g, j_what, j_sta, j_x, j_y, j_r, j_a1, j_a2, j_bang))
                continue

            # 우측 곡선이 없으면 중간점만 추가
            j_g = 2
            j_what = direction
            j_sta = self.jround(j_sta + arc_len, 5)
            j_x = self.jround(ec_x, 5)
            j_y = self.jround(ec_y, 5)
            j_r = radius
            j_a1 = clothoid_a1
            j_a2 = clothoid_a2
            j_bang = bang[i]
            ip_va.append(IPVA(j_g, j_what, j_sta, j_x, j_y, j_r, j_a1, j_a2, j_bang))

        # 마지막 VIP(종점) 추가
        j_g = 3
        j_what = ip_list[ip_count - 2].direction
        j_sta = self.jround(j_sta + math.hypot(j_x - self.rows[ip_count - 1].ip_x_coord, j_y - self.rows[ip_count - 1].ip_y_coord), 5)
        j_x = self.rows[ip_count - 1].ip_x_coord
        j_y = self.rows[ip_count - 1].ip_y_coord
        j_r = self.rows[ip_count - 1].radius
        j_a1 = self.rows[ip_count - 1].A1
        j_a2 = self.rows[ip_count - 1].A2
        j_bang = bang[ip_count - 2]
        ip_va.append(IPVA(j_g, j_what, j_sta, j_x, j_y, j_r, j_a1, j_a2, j_bang))

        # 최종 반환: VIP 좌표와 곡선 정보
        return HorResult(ip_va=ip_va, gou=gou, ip_list=ip_list, bang=bang, clothoid_list=clothoid_list)


    def jround(self, val_01, val_02):
        """
        지정한 자릿수로 반올림 처리하는 함수

        Parameters:
            val_01 (float) : 반올림할 값
            val_02 (float) : 반올림 자릿수

        Returns:
            temp (float) : 반올림된 값
        """
        # 매우 작은 값은 0으로 처리
        if val_01 < float(1 / 10 ** val_02):
            temp = 0
            return temp

        # 지정된 자릿수로 반올림
        temp = round(val_01 * 10 ** val_02) / 10 ** val_02
        return temp

    def jclox(self, jclo, jr):
        clox = jclo * (
                1
                - ((jclo ** 2) / (40 * (jr ** 2))
                   + (jclo ** 4) / (3456 * (jr ** 4))
                   - (jclo ** 6) / (599040 * (jr ** 6))
                   + (jclo ** 8) / (1.75473e+08 * (jr ** 8)))
        )
        return clox

    def jcloy(self, jclo, jr):
        cloy = ((jclo ** 2) / (6 * jr)) * (
                1
                - ((jclo ** 2) / (56 * (jr ** 2))
                   + (jclo ** 4) / (7040 * (jr ** 4))
                   - (jclo ** 6) / (1.6128e+06 * (jr ** 6))
                   + (jclo ** 8) / (5.88349e+08 * (jr ** 8)))
        )
        return cloy

    def j_hab(self, a, b):
        """
        각도 합 계산 및 2π 범위 보정
        a : 기준 각도 (라디안)
        b : 추가 각도 (라디안)
        """
        j_hab = a + b  # 단순 합산

        # 2π(360도)를 초과하면 다시 0~2π 범위로 보정
        if j_hab > 2 * math.pi:
            j_hab = j_hab - 2 * math.pi

        return j_hab

    def j_cha(self, a, b):
        """
        각도 차 계산 및 0~2π 범위 보정
        a : 기준 각도 (라디안)
        b : 빼는 각도 (라디안)
        """
        j_cha = a - b  # 각도 차 계산

        # 음수가 되면 0~2π 범위로 보정
        if j_cha < 0:
            j_cha = j_cha + 2 * math.pi

        return j_cha

    def j_degree(self, radian):
        """
        라디안(radian)을 도-분-초(Degree-Minute-Second) 문자열로 변환
        """
        # 1. 라디안을 도 단위로 변환
        temp_00 = radian * 180 / math.pi

        # 2. 정수 도(Degree) 부분
        temp_01 = int(temp_00)

        # 3. 분(Minute) 부분 계산
        temp_02 = int((temp_00 - temp_01) * 60)

        # 4. 초(Second) 부분 계산, 소수점 3자리까지 반올림
        temp_03 = self.jround(
            ((temp_00 - temp_01) * 60 - temp_02) * 60, 3
        )

        # 5. 문자열로 합치기: "도 - 분 - 초"
        temp_04 = str(temp_01) + ' - ' + str(temp_02) + ' - ' + str(temp_03)

        return temp_04

    def j_gaesan(self, q, acount, subjks):
        """
        acount(위치)에 따라 적절한 구간(subjks)을 찾아,
        해당 구간 타입에 맞는 계산 함수를 호출하고 결과(subgae)를 반환.

        Parameters:
            q (int)       : 구간 수
            acount (float): 현재 위치
            subjks (list) : 각 구간 정보 리스트, 각 원소는 [type, ..., end_sta, ...] 형식

        Returns:
            subgae (list): 계산된 결과 (x, y, r, angle 등)
        """
        for k in range(0, q, 1):
            # 현재 위치가 k 구간과 k+1 구간 사이에 있는지 확인
            if acount >= subjks[k][2] and acount < subjks[k + 1][2]:

                # 구간 타입에 따라 다른 함수 호출
                if subjks[k][0] == 0:
                    subgae = self.nosea(subjks[k][1], acount, subjks[k])
                elif subjks[k][0] == 1:
                    subgae = self.nosec(subjks[k][1], acount, subjks[k])
                elif subjks[k][0] == 2:
                    subgae = self.nosed(subjks[k + 1][1], acount, subjks[k + 1])
                elif subjks[k][0] == 5:
                    subgae = self.noseb(subjks[k][1], acount, subjks[k])
                elif subjks[k][0] == 6:
                    subgae = self.nosea(subjks[k][1], acount, subjks[k])

        return subgae

    def nosea(self, what, xydog, subjks):
        """
        직선 구간 계산 함수 (type 0 또는 6)

        Parameters:
            what (int)     : 구간 조건 (0 또는 1 등)
            xydog (float)  : 현재 위치(sta)
            subjks (list)  : 구간 정보 [type, ..., start_sta, x_start, y_start, ..., angle, ...]

        Returns:
            subgae (list)  : 계산 결과 [x, y, sta, angle]
        """
        subgae = []

        # 현재 위치를 구간 기준(start sta)으로 변환
        xydog = xydog - subjks[2]

        # x 좌표 계산: 구간 시작 x + 이동 거리 * cos(구간 각도)
        subgae.append(subjks[3] + xydog * math.cos(subjks[8]))
        # y 좌표 계산: 구간 시작 y + 이동 거리 * sin(구간 각도)
        subgae.append(subjks[4] + xydog * math.sin(subjks[8]))
        # sta 계산: 기준 sta + 이동 거리
        subgae.append(subjks[2] + xydog)
        # 각도 그대로 반환
        subgae.append(subjks[8])

        return subgae

    def noseb(self, what, xydog, subjks):
        """
        곡선 구간 계산 함수 (type 5)

        Parameters:
            what (int)     : 구간 조건 (0 또는 1)
            xydog (float)  : 현재 위치(sta)
            subjks (list)  : 구간 정보
                             [type, ..., start_sta, x_start, y_start, ..., radius, angle, ...]

        Returns:
            subgae (list)  : 계산 결과 [x, y, sta, angle]
        """
        subgae = []

        # 현재 위치를 구간 기준(sta)으로 변환
        xydog = xydog - subjks[2]
        if xydog == 0:
            xydog = 1e-6  # 0일 경우 작은 값으로 대체 (0으로 나누기 방지)

        # 곡선의 x, y 방향 변위 계산
        clox = self.jclox(xydog, subjks[6] * subjks[6] / xydog)
        cloy = self.jcloy(xydog, subjks[6] * subjks[6] / xydog)

        # 곡선 각도 계산
        cloceta = math.atan(cloy / clox)
        clolo = clox / math.cos(cloceta)

        # 최종 각도 계산
        if what == 0:
            jks = self.j_hab(subjks[8], cloceta)  # 이전 각도 + 곡선 각도
            taw = self.j_hab(subjks[8], xydog * xydog / 2 * subjks[6] * subjks[6])
        else:
            jks = self.j_cha(subjks[8], cloceta)  # 이전 각도 - 곡선 각도
            taw = self.j_cha(subjks[8], xydog * xydog / 2 * subjks[6] * subjks[6])

        # x, y 좌표 계산
        subgae.append(subjks[3] + clolo * math.cos(jks))
        subgae.append(subjks[4] + clolo * math.sin(jks))
        # sta 계산
        subgae.append(subjks[2] + xydog)
        # 최종 각도 저장
        subgae.append(taw)

        return subgae

    def nosec(self, what, xydog, subjks):
        """
        원호 곡선 구간 계산 함수 (type 1)

        Parameters:
            what (int)     : 구간 방향 (0: 정방향, 1: 역방향)
            xydog (float)  : 현재 위치(sta)
            subjks (list)  : 구간 정보
                             [type, ..., start_sta, x_start, y_start, radius, angle, ...]

        Returns:
            subgae (list)  : 계산 결과 [x, y, sta, angle]
        """
        subgae = []

        # 현재 위치를 구간 기준(sta)으로 변환
        xydog = xydog - subjks[2]

        # 원호 구간 각도 변화
        xyceta = xydog / subjks[5]  # arc_length / radius → 회전 각도

        if what == 0:
            # 정방향
            jks = self.j_hab(subjks[8], math.pi / 2)  # 시작 각도 + 90도
            jkss = self.j_hab(jks, math.pi)  # 시작 각도 + 270도

            # x, y 좌표 계산
            subgae.append(subjks[3] + subjks[5] * math.cos(jks) + subjks[5] * math.cos(self.j_hab(jkss, xyceta)))
            subgae.append(subjks[4] + subjks[5] * math.sin(jks) + subjks[5] * math.sin(self.j_hab(jkss, xyceta)))

            # sta 계산
            subgae.append(subjks[2] + xydog)

            # 최종 각도
            subgae.append(self.j_hab(self.j_hab(jkss, xyceta), math.pi / 2))
            return subgae

        # 역방향
        jks = self.j_cha(subjks[8], math.pi / 2)  # 시작 각도 - 90도
        jkss = self.j_cha(jks, math.pi)  # 시작 각도 - 270도

        # x, y 좌표 계산
        subgae.append(subjks[3] + subjks[5] * math.cos(jks) + subjks[5] * math.cos(self.j_cha(jkss, xyceta)))
        subgae.append(subjks[4] + subjks[5] * math.sin(jks) + subjks[5] * math.sin(self.j_cha(jkss, xyceta)))

        # sta 계산
        subgae.append(subjks[2] + xydog)

        # 최종 각도
        subgae.append(self.j_cha(self.j_cha(jkss, xyceta), math.pi / 2))
        return subgae

    def nosed(self, what, xydog, subjks):
        """
        역방향 또는 감속 원호 구간 계산 함수 (type 2)

        Parameters:
            what (int)     : 구간 방향 (0: 정방향, 1: 역방향)
            xydog (float)  : 현재 위치(sta)
            subjks (list)  : 구간 정보
                             [type, ..., start_sta, x_start, y_start, radius, angle, ...]

        Returns:
            subgae (list)  : 계산 결과 [x, y, sta, angle]
        """
        subgae = []

        # 특정 타입(6번) 처리: 클로소이드(clothoid) 구간
        if subjks[0] == 6:
            # 역방향 계산: 기준 위치에서 현재 위치까지 거리
            xydog = subjks[2] - xydog
            if xydog == 0:
                xydog = 1e-06  # 0 방지

            # 클로소이드 계산
            clox = self.jclox(xydog, subjks[7] * subjks[7] / xydog)
            cloy = self.jcloy(xydog, subjks[7] * subjks[7] / xydog)
            cloceta = math.atan(cloy / clox)
            clolo = clox / math.cos(cloceta)

            # 방향 계산
            if what == 0:
                jks = self.j_cha(self.j_cha(subjks[8], math.pi), cloceta)
                taw = self.j_cha(subjks[8], xydog * xydog / 2 * subjks[7] * subjks[7])
            else:
                jks = self.j_hab(self.j_cha(subjks[8], math.pi), cloceta)
                taw = self.j_hab(subjks[8], xydog * xydog / 2 * subjks[7] * subjks[7])

            # 좌표 계산
            subgae.append(subjks[3] + clolo * math.cos(jks))
            subgae.append(subjks[4] + clolo * math.sin(jks))
            subgae.append(subjks[2] - xydog)  # sta
            subgae.append(taw)  # 최종 각도
            return subgae

        # 일반 역방향 직선 구간 계산
        xydog = subjks[2] - xydog
        subgae.append(subjks[3] + xydog * math.cos(self.j_hab(subjks[8], math.pi)))
        subgae.append(subjks[4] + xydog * math.sin(self.j_hab(subjks[8], math.pi)))
        subgae.append(subjks[2] - xydog)
        subgae.append(subjks[8])
        return subgae

hor_option = HorOption(0,1,VisibleType.STA,20.00)
HorizonInputData()
rows = [
    HorizonInputData(0, 1000, 2100, 0, 0, 0),
    HorizonInputData(1, 1500, 1700, 99, 20, 20),
    HorizonInputData(2, 1600, 1660, 100, 20, 20),
    HorizonInputData(3, 1750, 1650, 100, 20, 20),
    HorizonInputData(4, 1800, 1000, 0, 0, 0)
]
hor_cal = HorCalqu()
a = hor_cal.basic_calqu(hor_option, rows)
print(a.ip_va[0].x, a.ip_va[0].y)  # x, y 좌표 출력