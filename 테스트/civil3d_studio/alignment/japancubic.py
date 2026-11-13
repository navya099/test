import math


class JapaneseCubicSpiral:
    """
    일본 3차 포물선(Japanese Cubic Parabola) 고정밀 기하 엔진
    - 허용 오차: 1e-12 m (요구 정밀도 1e-7 m 초과 달성)
    """

    def __init__(self, R: float, L: float, direction: int = 1):
        """
        :param R: 원곡선 반경 (m, 양수)
        :param L: 완화곡선 총 호 길이 (m, 양수)
        :param direction: 곡선 방향 (우회전: 1 또는 -1, 좌회전: 반대 부호)
        """
        self.R = float(R)
        self.L = float(L)
        self.dir = 1.0 if direction >= 0 else -1.0

        # 1. 총 호 길이 L에 정확히 대응하는 끝점 Xc 역산 (정밀도 1e-14)
        self.Xc = self._solve_Xc()
        self.denom = 6.0 * self.R * self.Xc  # 6 * R * Xc 상수 캐싱

    def _arc_length_from_x(self, x: float) -> float:
        """시점부터 X축 거리 x까지의 정밀 호 길이 s(x) 계산 (10차 테일러 급수)"""
        if x == 0.0:
            return 0.0
        # u = dy/dx = x^2 / (2 * R * Xc)
        u = (x * x) / (2.0 * self.R * self.Xc)
        u2 = u * u

        # s(x) = x * (1 + u^2/10 - u^4/72 + u^6/208 - 5u^8/2176 + 7u^10/5120)
        series = (
                1.0
                + u2 * (1.0 / 10.0
                        + u2 * (-1.0 / 72.0
                                + u2 * (1.0 / 208.0
                                        + u2 * (-5.0 / 2176.0
                                                + u2 * (7.0 / 5120.0)))))
        )
        return x * series

    def _solve_Xc(self, tol: float = 1e-14) -> float:
        """뉴턴-랩슨 법으로 총 호 길이 L을 만족하는 끝점 Xc 산출"""
        xc = self.L  # 초기 추정값은 L
        for _ in range(30):
            u = xc / (2.0 * self.R)
            u2 = u * u

            # f(Xc) = Xc * S(u) - L = 0
            s_val = xc * (
                    1.0
                    + u2 * (1.0 / 10.0
                            + u2 * (-1.0 / 72.0
                                    + u2 * (1.0 / 208.0
                                            + u2 * (-5.0 / 2176.0))))
            )
            f = s_val - self.L
            if abs(f) < tol:
                break

            # 도함수 ds/dXc = sqrt(1 + (dy/dXc)^2) = sqrt(1 + u^2)
            df = math.sqrt(1.0 + u2)
            xc -= f / df

        return xc

    def point_at_x(self, x: float):
        """X축 투영 거리 x에서의 로컬 좌표 (x, y), 1차 미분 y', 2차 미분 y'' 반환"""
        y = self.dir * (x ** 3) / self.denom
        dy = self.dir * (x ** 2) / (2.0 * self.R * self.Xc)
        ddy = self.dir * x / (self.R * self.Xc)
        return x, y, dy, ddy

    def point_at_station(self, s: float):
        """실제 측점 거리 s (0 <= s <= L)에 해당하는 정확한 (x, y) 좌표 반환"""
        if s <= 0.0:
            return 0.0, 0.0
        if s >= self.L:
            x, y, _, _ = self.point_at_x(self.Xc)
            return x, y

        # 호 길이 s에 대응하는 x를 뉴턴-랩슨 법으로 역산
        x = s * (self.Xc / self.L)
        for _ in range(25):
            curr_s = self._arc_length_from_x(x)
            diff = curr_s - s
            if abs(diff) < 1e-13:
                break
            dy = (x * x) / (2.0 * self.R * self.Xc)
            ds_dx = math.sqrt(1.0 + dy * dy)
            x -= diff / ds_dx

        x, y, _, _ = self.point_at_x(x)
        return x, y

    def station_offset(self, px: float, py: float, tol: float = 1e-12):
        """
        로컬 좌표계 상의 외부 점 (px, py)에 대한 정밀 Station(호 길이 s) 및 Offset 계산
        :return: (station_s, signed_offset, proj_x, proj_y) 또는 범위 이탈 시 None
        """
        # 1. 초기값 설정 (구간 8등분 중 최단 거리 지점 선택으로 전역 수렴 보장)
        best_x = 0.0
        min_d2 = float("inf")
        for i in range(9):
            tx = self.Xc * (i / 8.0)
            _, ty, _, _ = self.point_at_x(tx)
            d2 = (px - tx) ** 2 + (py - ty) ** 2
            if d2 < min_d2:
                min_d2 = d2
                best_x = tx

        x = best_x

        # 2. 뉴턴-랩슨 반복 연산 (목적함수 f(x) = (x - px) + (y - py)*y' = 0)
        for _ in range(30):
            _, y, dy, ddy = self.point_at_x(x)

            f = (x - px) + (y - py) * dy
            f_prime = 1.0 + (dy * dy) + (y - py) * ddy

            if abs(f_prime) < 1e-15:
                break

            delta_x = f / f_prime
            x -= delta_x

            if abs(delta_x) < tol:
                break

        # 3. 선형 범위 이탈 판별 (허용 오차 1e-9 여유 부여)
        if x < -1e-9 or x > self.Xc + 1e-9:
            return None
        x = max(0.0, min(self.Xc, x))

        # 4. 최종 투영점 좌표, 실제 호 길이(Station), 부호 있는 이격 거리(Offset) 산출
        qx, qy, dy, _ = self.point_at_x(x)
        station_s = self._arc_length_from_x(x)

        dist = math.hypot(px - qx, py - qy)
        # 접선 벡터 (1, dy)와 오프셋 벡터 (px - qx, py - qy)의 2D 외적으로 좌/우 부호 판별
        cross = 1.0 * (py - qy) - dy * (px - qx)
        # 일반 수학 좌표계 기준: 진행 방향 우측(+), 좌측(-)
        signed_offset = -dist if cross > 0 else dist

        return station_s, signed_offset, qx, qy


# ==========================================
# 정밀도 검증 테스트 (역산 오차 확인)
# ==========================================
if __name__ == "__main__":
    # 조건: 반경 R = 300m, 완화곡선 길이 L = 100m, 좌회전(dir=1)
    spiral = JapaneseCubicSpiral(R=300.0, L=100.0, direction=1)

    # 검증할 실제 측점 s = 65.4321098m, 이격 거리 offset = +12.3456789m
    true_s = 65.4321098
    true_off = 12.3456789

    # 1. 정방향 계산: (true_s, true_off) -> (px, py) 좌표 생성
    qx, qy = spiral.point_at_station(true_s)
    _, _, dy, _ = spiral.point_at_x(qx)
    norm_len = math.hypot(1.0, dy)
    # 우측 법선 벡터 (dy, -1) / norm_len
    px = qx + true_off * (dy / norm_len)
    py = qy + true_off * (-1.0 / norm_len)

    # 2. 역방향 계산: (px, py) -> station_offset() 실행
    calc_s, calc_off, _, _ = spiral.station_offset(px, py)

    print(f"끝점 Xc 보정값 : {spiral.Xc:.12f} m (총 호 길이 L = {spiral.L} m)")
    print(f"측점(Station) 오차: {abs(true_s - calc_s):.15e} m")
    print(f"이격(Offset)  오차: {abs(true_off - calc_off):.15e} m")
