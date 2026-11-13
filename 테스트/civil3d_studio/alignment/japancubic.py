import math


class JapaneseCubicSpiral:
    """
    글로벌(WCS) 좌표계를 지원하는 고정밀 일본 3차 포물선(Japanese Cubic) 엔진
    - 진입 완화곡선(직선->원곡선) 및 진출 완화곡선(원곡선->직선) 모두 지원
    - 허용 오차: 1e-12 m (요구 정밀도 0.0000001 m 초과 달성)
    """

    def __init__(
            self,
            start_easting: float,
            start_northing: float,
            start_angle_rad: float,
            start_station: float,
            R: float,
            L: float,
            turn_direction: int = 1,
            is_exit_spiral: bool = False
    ):
        """
        :param start_easting: 완화곡선 시점의 도면 X (Easting) 좌표
        :param start_northing: 완화곡선 시점의 도면 Y (Northing) 좌표
        :param start_angle_rad: 시점 진행 방향 접선 각도 (동쪽=0, 반시계 양수, 라디안)
        :param start_station: 완화곡선 시점의 누적 측점 (예: 120.0)
        :param R: 접속 원곡선 반경 (m, 양수)
        :param L: 완화곡선 총 호 길이 (m, 양수)
        :param turn_direction: 진행 방향 기준 좌회전 = +1, 우회전 = -1
        :param is_exit_spiral: 진입(TS->SC) = False, 진출(CS->ST) = True
        """
        self.R = float(R)
        self.L = float(L)
        self.start_sta = float(start_station)
        self.is_exit = bool(is_exit_spiral)

        # 1. 총 호 길이 L에 대응하는 끝점 Xc 역산 (1e-14 정밀도)
        self.Xc = self._solve_Xc()
        self.denom = 6.0 * self.R * self.Xc

        # 2. 기준 원점 및 회전각 설정 (진출 완화곡선일 경우 종점 기준 역방향 로컬 좌표계로 변환)
        if not self.is_exit:
            self.origin_e = float(start_easting)
            self.origin_n = float(start_northing)
            self.base_angle = float(start_angle_rad)
            self.local_dir = 1.0 if turn_direction >= 0 else -1.0
        else:
            # 진출 완화곡선은 끝점(ST)에서 역방향으로 들어가는 로컬 좌표계 구성
            # 먼저 시점(CS)에서 끝점(ST)까지의 로컬 변위를 계산하여 끝점 글로벌 좌표 확정
            end_theta_offset = math.atan((self.Xc ** 2) / (2.0 * self.R * self.Xc))
            # 진행 방향 기준 끝점 접선각 계산
            end_angle = start_angle_rad + (end_theta_offset if turn_direction >= 0 else -end_theta_offset)
            self.base_angle = end_angle + math.pi
            self.local_dir = -1.0 if turn_direction >= 0 else 1.0

            # 끝점(ST) 글로벌 좌표 역산
            yc_local = self.local_dir * (self.Xc ** 3) / self.denom
            cos_b, sin_b = math.cos(self.base_angle), math.sin(self.base_angle)
            self.origin_e = float(start_easting) - (self.Xc * cos_b - yc_local * sin_b)
            self.origin_n = float(start_northing) - (self.Xc * sin_b + yc_local * cos_b)

        # 삼각함수 값 사전 캐싱 (실시간 연산 최적화)
        self.cos_a = math.cos(self.base_angle)
        self.sin_a = math.sin(self.base_angle)

    def _solve_Xc(self, tol: float = 1e-14) -> float:
        xc = self.L
        for _ in range(30):
            u = xc / (2.0 * self.R)
            u2 = u * u
            s_val = xc * (
                    1.0 + u2 * (1.0 / 10.0 + u2 * (-1.0 / 72.0 + u2 * (1.0 / 208.0 + u2 * (-5.0 / 2176.0))))
            )
            f = s_val - self.L
            if abs(f) < tol:
                break
            xc -= f / math.sqrt(1.0 + u2)
        return xc

    def _arc_length_from_x(self, x: float) -> float:
        if x <= 0.0:
            return 0.0
        u = (x * x) / (2.0 * self.R * self.Xc)
        u2 = u * u
        series = (
                1.0 + u2 * (1.0 / 10.0 + u2 * (-1.0 / 72.0 + u2 * (1.0 / 208.0
                                                                   + u2 * (-5.0 / 2176.0 + u2 * (7.0 / 5120.0)))))
        )
        return x * series

    def _local_point_at_x(self, x: float):
        y = self.local_dir * (x ** 3) / self.denom
        dy = self.local_dir * (x ** 2) / (2.0 * self.R * self.Xc)
        ddy = self.local_dir * x / (self.R * self.Xc)
        return x, y, dy, ddy

    def to_global(self, lx: float, ly: float):
        """로컬 좌표 (lx, ly) -> 글로벌 WCS 좌표 (E, N)"""
        ge = self.origin_e + lx * self.cos_a - ly * self.sin_a
        gn = self.origin_n + lx * self.sin_a + ly * self.cos_a
        return ge, gn

    def to_local(self, ge: float, gn: float):
        """글로벌 WCS 좌표 (E, N) -> 로컬 좌표 (lx, ly)"""
        de = ge - self.origin_e
        dn = gn - self.origin_n
        lx = de * self.cos_a + dn * self.sin_a
        ly = -de * self.sin_a + dn * self.cos_a
        return lx, ly

    def point_location(self, station: float, offset: float = 0.0):
        """
        C3D Alignment.PointLocation(station, offset)과 동일한 정방향 계산
        :param station: 글로벌 측점 (start_station ~ start_station + L)
        :param offset: 진행 방향 기준 우측(+), 좌측(-) 이격 거리
        :return: (Easting, Northing)
        """
        ds = station - self.start_sta
        if ds < -1e-9 or ds > self.L + 1e-9:
            raise ValueError("측점이 완화곡선 범위를 벗어났습니다.")
        ds = max(0.0, min(self.L, ds))

        # 진출 완화곡선인 경우 로컬 호 길이 반전
        target_s = (self.L - ds) if self.is_exit else ds

        # target_s에 대응하는 로컬 x 역산 (뉴턴-랩슨 법)
        x = target_s * (self.Xc / self.L)
        for _ in range(25):
            diff = self._arc_length_from_x(x) - target_s
            if abs(diff) < 1e-13:
                break
            dy = (x * x) / (2.0 * self.R * self.Xc)
            x -= diff / math.sqrt(1.0 + dy * dy)

        lx, ly, dy, _ = self._local_point_at_x(x)

        # 진행 방향 기준 우측 법선 벡터 적용
        norm = math.hypot(1.0, dy)
        # 진출 곡선은 로컬 진행 방향이 반대이므로 오프셋 부호 반전
        eff_offset = -offset if self.is_exit else offset
        lx_off = lx + eff_offset * (dy / norm)
        ly_off = ly + eff_offset * (-1.0 / norm)

        return self.to_global(lx_off, ly_off)

    def station_offset(self, easting: float, northing: float, tol: float = 1e-12):
        """
        C3D Alignment.StationOffset(easting, northing)과 동일한 역방향 투영 계산
        :return: (global_station, signed_offset, proj_easting, proj_northing) 또는 범위 밖이면 None
        """
        # 1. 글로벌 좌표를 로컬 좌표계로 변환 (평행이동 먼저 수행하여 대단위 좌표 정밀도 유지)
        px, py = self.to_local(easting, northing)

        # 2. 초기값 설정 (8등분 탐색)
        best_x = 0.0
        min_d2 = float("inf")
        for i in range(9):
            tx = self.Xc * (i / 8.0)
            _, ty, _, _ = self._local_point_at_x(tx)
            d2 = (px - tx) ** 2 + (py - ty) ** 2
            if d2 < min_d2:
                min_d2 = d2
                best_x = tx

        x = best_x

        # 3. 뉴턴-랩슨 수직 투영 연산
        for _ in range(30):
            _, y, dy, ddy = self._local_point_at_x(x)
            f = (x - px) + (y - py) * dy
            f_prime = 1.0 + (dy * dy) + (y - py) * ddy
            if abs(f_prime) < 1e-15:
                break
            delta_x = f / f_prime
            x -= delta_x
            if abs(delta_x) < tol:
                break

        # 4. 범위 이탈 판별
        if x < -1e-9 or x > self.Xc + 1e-9:
            return None
        x = max(0.0, min(self.Xc, x))

        # 5. 글로벌 측점, 이격 거리, 투영점 글로벌 좌표 환산
        qx, qy, dy, _ = self._local_point_at_x(x)
        local_s = self._arc_length_from_x(x)

        if not self.is_exit:
            global_sta = self.start_sta + local_s
        else:
            global_sta = self.start_sta + (self.L - local_s)

        dist = math.hypot(px - qx, py - qy)
        cross = 1.0 * (py - qy) - dy * (px - qx)
        # 진행 방향 기준 우측(+), 좌측(-) 부호 결정
        signed_offset = -dist if cross > 0 else dist
        if self.is_exit:
            signed_offset = -signed_offset

        proj_e, proj_n = self.to_global(qx, qy)
        return global_sta, signed_offset, proj_e, proj_n


# =========================================================
# 실무 TM 대단위 좌표계 정밀도 검증 테스트
# =========================================================
if __name__ == "__main__":
    # 실제 한국 중부원점 TM 좌표 예시 (E = 204,512.345m, N = 541,230.678m)
    # 시점 방위각: 북동쪽 35도, 시점 측점: 1+240.000 (1240.0m), 반경 R=400m, 길이 L=120m
    spiral_in = GlobalJapaneseCubicSpiral(
        start_easting=204512.345,
        start_northing=541230.678,
        start_angle_rad=math.radians(35.0),
        start_station=1240.0,
        R=400.0,
        L=120.0,
        turn_direction=-1,  # 우회전 곡선
        is_exit_spiral=False  # 진입 완화곡선 (TS -> SC)
    )

    test_sta = 1315.6789123  # 목표 측점: 1+315.6789123
    test_off = -15.4321987  # 목표 오프셋: 좌측 15.4321987m

    # 정방향: 글로벌 측점/오프셋 -> 글로벌 (E, N)
    ge, gn = spiral_in.point_location(test_sta, test_off)

    # 역방향: 글로벌 (E, N) -> 글로벌 측점/오프셋
    res_sta, res_off, pe, pn = spiral_in.station_offset(ge, gn)

    print(f"계산된 글로벌 좌표 : E = {ge:.9f}, N = {gn:.9f}")
    print(f"측점(Station) 오차 : {abs(test_sta - res_sta):.15e} m")
    print(f"이격(Offset)  오차 : {abs(test_off - res_off):.15e} m")
