# 평면선형 계산 테스트
import math
'''
hor_option = [
            '시작측점 누가거리',
            '시작 IP번호',
            '측점 표시방법(STA)',
            '측점 표시방법(NO)',
            '측점 계산 간격'
            ]
            
rows = [,
,
,
,
,
]
'''




class HorCalqu:
    """HorCalqu"""

    def __init__(self):
        self.cursor_hor = None
        self.conn_hor = None
        self.rows = None
        self.sta = None

    def print_dxf(self, cursor_hor, conn_hor, hor_option):
        pass

    def print_01(self, cursor_hor, conn_hor, hor_option):
        pass


    def basic_calqu(self, hor_option, rows):
        self.rows = rows
        ip_count = len(self.rows)
        self.sta = float(hor_option[0]) #시작 측점 누가거리
        gan = float(hor_option[4]) #계산 간격 DEFAULT 20.00
        ip_va = []  # 최종 VIP/곡선 점 계산값 저장
        lo = []  # 구간 길이
        gou = []  # 각도 변화량
        ip = []  # IP 관련 계산값
        bc = []  # 시작점 좌표 (Begin Coordinate)
        ec = []  # 종료점 좌표 (End Coordinate)
        btc = []  # BTC 좌표 (보조)
        etc = []  # ETC 좌표 (보조)
        bang = []  # 방위각 각도(방향)
        clo = []  # 클로소이드 계산용 배열
        for i in range(0, ip_count - 1):
            lo.append(0)
            gou.append(0)
            ip.append([
                0,
                0,
                0,
                0,
                0,
                0])
            bc.append([
                0,
                0])
            ec.append([
                0,
                0])
            btc.append([
                0,
                0,
                0])
            etc.append([
                0,
                0,
                0])
            bang.append(0)
            clo.append([
                [
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0],
                [
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0]])
        back = 0

        try:
            for i in range(0, ip_count - 1):
                # 두 점 사이의 직선 거리 계산 (유클리드 거리)
                temp_ip_dist = math.hypot(
                    self.rows[i + 1][1] - self.rows[i][1],  # ΔX
                    self.rows[i + 1][2] - self.rows[i][2]  # ΔY
                )

                # 두 점의 X 좌표가 같으면 수직선 처리
                if self.rows[i + 1][1] == self.rows[i][1]:
                    if self.rows[i][2] > self.rows[i + 1][2]:
                        temp_bang_yui = math.pi * -1 / 2  # -90도 (아래 방향)
                    else:
                        temp_bang_yui = math.pi / 2  # 90도 (위 방향)
                else:
                    # 일반적인 두 점의 방향 각도 계산 (atan2 대신 atan 사용)
                    temp_bang_yui = math.atan(
                        (self.rows[i + 1][2] - self.rows[i][2]) /
                        (self.rows[i + 1][1] - self.rows[i][1])
                    )

                # 추가 보정: X 좌표 증가 방향에 따라 각도 조정
                if self.rows[i][1] <= self.rows[i + 1][1]:
                    if self.rows[i][2] > self.rows[i + 1][2]:
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

                # 2. 곡선 요소 계산
                ip[i][0] = self.rows[i][3] * math.tan(gou[i] / 2)  # 접선 거리
                ip[i][1] = self.rows[i][3] * gou[i]  # 곡선 길이
                ip[i][2] = self.rows[i][3] * (1 / math.cos(gou[i] / 2) - 1)  # 곡선 편심
                ip[i][3] = self.rows[i][3] * (1 - math.cos(gou[i] / 2))  # 곡선 높이 변화
                ip[i][4] = 2 * self.rows[i][3] * math.sin(gou[i] / 2)  # 곡선 폭
                ip[i][5] = 0 if bang[i] > bang[i - 1] else 1  # 곡선 진행 방향 플래그

                # 3. 각도 예외 처리: 반시계/시계 방향 보정
                if math.pi * 2 > bang[i - 1] > math.pi:
                    if bang[i - 1] - math.pi >= bang[i] >= 0:
                        ip[i][5] = 0
                    elif bang[i - 1] + math.pi <= bang[i] <= 2 * math.pi:
                        ip[i][5] = 1

                # 4. 각 점의 왼쪽/오른쪽 클로징(clo) 계산
                for k in range(0, 2):  # 0=왼쪽, 1=오른쪽
                    if self.rows[i][4 + k] == 0:  # 클로징 값이 0이면 초기화
                        for j in range(5, 15):
                            clo[i][k][j] = 0
                        continue

                    # 곡선 요소 기반 계산
                    clo[i][k][5] = self.rows[i][4 + k] ** 2 / self.rows[i][3]
                    clo[i][k][6] = self.jclox(clo[i][k][5], self.rows[i][3])
                    clo[i][k][7] = self.jcloy(clo[i][k][5], self.rows[i][3])
                    clo[i][k][8] = clo[i][k][5] / 2 * self.rows[i][3]
                    clo[i][k][9] = clo[i][k][7] + self.rows[i][3] * math.cos(clo[i][k][8]) - self.rows[i][3]
                    clo[i][k][10] = clo[i][k][6] - self.rows[i][3] * math.sin(clo[i][k][8])
                    clo[i][k][11] = clo[i][k][7] / math.sin(clo[i][k][8])
                    clo[i][k][12] = clo[i][k][6] - clo[i][k][7] / math.tan(clo[i][k][8])
                    clo[i][k][13] = math.atan(clo[i][k][7] / clo[i][k][6])
                    clo[i][k][14] = clo[i][k][7] / math.sin(clo[i][k][13])

                # 5. clo[i] 좌표 기반 최종 위치 계산
                clo[i][0][0] = clo[i][1][0] = (self.rows[i][3] + clo[i][1][9]) * math.tan(gou[i] / 2)
                clo[i][0][1] = (clo[i][0][9] - clo[i][1][9]) / math.tan(gou[i])
                clo[i][1][1] = (clo[i][0][9] - clo[i][1][9]) / math.sin(gou[i])
                clo[i][0][2] = clo[i][0][10] + clo[i][0][0] - clo[i][0][1]
                clo[i][1][2] = clo[i][1][10] + clo[i][1][0] + clo[i][1][1]
                clo[i][0][3] = clo[i][1][3] = gou[i] - clo[i][0][8] + clo[i][1][8]
                clo[i][0][4] = clo[i][1][4] = self.rows[i][3] * clo[i][0][3]

                # 6. 곡선의 시작/종료 좌표 계산
                btc[i][0] = self.rows[i][1] + clo[i][0][2] * math.cos(back)
                btc[i][1] = self.rows[i][2] + clo[i][0][2] * math.sin(back)
                etc[i][0] = self.rows[i][1] + clo[i][1][2] * math.cos(bang[i])
                etc[i][1] = self.rows[i][2] + clo[i][1][2] * math.sin(bang[i])

                # 7. 곡선 진행 각도 계산 (s1, s2)
                if ip[i][5] == 0:
                    s1 = self.j_hab(bang[i - 1], clo[i][0][13])
                    if bang[i] >= math.pi:
                        back = bang[i] - math.pi
                    else:
                        back = bang[i] + math.pi
                    s2 = self.j_cha(back, clo[i][1][13])
                else:
                    s1 = self.j_cha(bang[i - 1], clo[i][0][13])
                    if bang[i] >= math.pi:
                        back = bang[i] - math.pi
                    else:
                        back = bang[i] + math.pi
                    s2 = self.j_hab(back, clo[i][1][13])

                # 8. 최종 곡선 좌표 계산
                bc[i][0] = btc[i][0] + clo[i][0][14] * math.cos(s1)
                bc[i][1] = btc[i][1] + clo[i][0][14] * math.sin(s1)
                ec[i][0] = etc[i][0] + clo[i][1][14] * math.cos(s2)
                ec[i][1] = etc[i][1] + clo[i][1][14] * math.sin(s2)

        finally:
            pass
        print('계산이 완료되었습니다.')
        j_g = 0
        j_what = ip[1][5]
        j_sta = 0
        j_x = self.rows[0][1]
        j_y = self.rows[0][2]
        j_r = 0
        j_a1 = 0
        j_a2 = 0
        j_bang = bang[0]
        ip_va.append([
            j_g,
            j_what,
            j_sta,
            j_x,
            j_y,
            j_r,
            j_a1,
            j_a2,
            j_bang])
        # VIP(Intersection Point)별로 좌표와 곡선 정보 계산
        for i in range(1, ip_count - 1):
            # 좌측 곡선(clo[i][0])이 존재하면
            if clo[i][0][5] != 0:
                # 곡선 시작점 정보 추가
                j_g = 5  # 구간 타입 코드 (5 = 곡선 시작점)
                j_what = ip[i][5]  # 좌우 방향 정보
                j_sta = self.jround(j_sta + math.hypot(j_x - btc[i][0], j_y - btc[i][1]), 5)  # 거리 누적
                j_x = self.jround(btc[i][0], 5)  # x좌표
                j_y = self.jround(btc[i][1], 5)  # y좌표
                j_r = self.rows[i][3]  # 곡선 반경
                j_a1 = self.rows[i][4]  # 추가 파라미터1
                j_a2 = self.rows[i][5]  # 추가 파라미터2
                j_bang = bang[i - 1]  # 이전 방향각
                ip_va.append([j_g, j_what, j_sta, j_x, j_y, j_r, j_a1, j_a2, j_bang])

                # 곡선 중간점 정보 추가
                j_g = 1  # 구간 타입 코드 (1 = 곡선 중간점)
                j_what = ip[i][5]
                j_sta = self.jround(j_sta + clo[i][0][5], 5)  # 좌측 곡선 거리
                j_x = self.jround(bc[i][0], 5)  # 중간 x
                j_y = self.jround(bc[i][1], 5)  # 중간 y
                j_r = self.rows[i][3]
                j_a1 = self.rows[i][4]
                j_a2 = self.rows[i][5]

                # 곡선 진행 방향에 따라 방위각 계산
                if j_what == 0:
                    j_bang = self.j_hab(bang[i - 1], clo[i][0][8])
                else:
                    j_bang = self.j_cha(bang[i - 1], clo[i][0][8])
                ip_va.append([j_g, j_what, j_sta, j_x, j_y, j_r, j_a1, j_a2, j_bang])

            # 좌측 곡선이 없으면 곡선 중간점만 추가
            else:
                j_g = 1
                j_what = ip[i][5]
                j_sta = self.jround(j_sta + math.hypot(j_x - bc[i][0], j_y - bc[i][1]), 5)
                j_x = self.jround(bc[i][0], 5)
                j_y = self.jround(bc[i][1], 5)
                j_r = self.rows[i][3]
                j_a1 = self.rows[i][4]
                j_a2 = self.rows[i][5]
                j_bang = bang[i - 1]
                ip_va.append([j_g, j_what, j_sta, j_x, j_y, j_r, j_a1, j_a2, j_bang])

            # 우측 곡선(clo[i][1])이 존재하면
            if clo[i][1][5] != 0:
                # 곡선 중간점
                j_g = 2
                j_what = ip[i][5]
                j_sta = self.jround(j_sta + clo[i][1][4], 5)
                j_x = self.jround(ec[i][0], 5)
                j_y = self.jround(ec[i][1], 5)
                j_r = self.rows[i][3]
                j_a1 = self.rows[i][4]
                j_a2 = self.rows[i][5]

                if j_what == 0:
                    j_bang = self.j_cha(bang[i], clo[i][1][8])
                else:
                    j_bang = self.j_hab(bang[i], clo[i][1][8])
                ip_va.append([j_g, j_what, j_sta, j_x, j_y, j_r, j_a1, j_a2, j_bang])

                # 곡선 끝점
                j_g = 6
                j_what = ip[i][5]
                j_sta = self.jround(j_sta + clo[i][1][5], 5)
                j_x = self.jround(etc[i][0], 5)
                j_y = self.jround(etc[i][1], 5)
                j_r = self.rows[i][3]
                j_a1 = self.rows[i][4]
                j_a2 = self.rows[i][5]
                j_bang = bang[i]
                ip_va.append([j_g, j_what, j_sta, j_x, j_y, j_r, j_a1, j_a2, j_bang])
                continue

            # 우측 곡선이 없으면 중간점만 추가
            j_g = 2
            j_what = ip[i][5]
            j_sta = self.jround(j_sta + clo[i][1][4], 5)
            j_x = self.jround(ec[i][0], 5)
            j_y = self.jround(ec[i][1], 5)
            j_r = self.rows[i][3]
            j_a1 = self.rows[i][4]
            j_a2 = self.rows[i][5]
            j_bang = bang[i]
            ip_va.append([j_g, j_what, j_sta, j_x, j_y, j_r, j_a1, j_a2, j_bang])

        # 마지막 VIP(종점) 추가
        j_g = 3
        j_what = ip[ip_count - 2][5]
        j_sta = self.jround(j_sta + math.hypot(j_x - self.rows[ip_count - 1][1], j_y - self.rows[ip_count - 1][2]), 5)
        j_x = self.rows[ip_count - 1][1]
        j_y = self.rows[ip_count - 1][2]
        j_r = self.rows[ip_count - 1][3]
        j_a1 = self.rows[ip_count - 1][4]
        j_a2 = self.rows[ip_count - 1][5]
        j_bang = bang[ip_count - 2]
        ip_va.append([j_g, j_what, j_sta, j_x, j_y, j_r, j_a1, j_a2, j_bang])

        # 최종 반환: VIP 좌표와 곡선 정보
        return (ip_va, gou, ip, bang, clo)

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
        clox = jclo * (((
                                    1 - jclo ** 2 / 40 * jr ** 2) + jclo ** 4 / 3456 * jr ** 4 - jclo ** 6 / 599040 * jr ** 6) + jclo ** 8 / 1.75473e+08 * jr ** 8)
        return clox


    def jcloy(self, jclo, jr):
        cloy = (jclo ** 2 / 6 * jr) * (((
                                                    1 - jclo ** 2 / 56 * jr ** 2) + jclo ** 4 / 7040 * jr ** 4 - jclo ** 6 / 1.6128e+06 * jr ** 6) + jclo ** 8 / 5.88349e+08 * jr ** 8)
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
        for k in range(0, q):
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

hor_option = [
    0,
    1,
    True,
    False,
    20.00
]
rows = [
    ['BP', 1000, 2100, 0, 0, 0],
    [1, 1500, 1700, 99, 20, 20],
    [2, 1600, 1660, 100, 20, 20],
    [3, 1750, 1650, 100, 20, 20],
    ['EP', 1800, 1000, 0, 0, 0]
]
hor_cal = HorCalqu()
a = hor_cal.basic_calqu(hor_option, rows)
print('피니쉬')