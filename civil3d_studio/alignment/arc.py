# ==============================================================================
# 3. 원곡선 요소 (Circular Arc Segment)
# ==============================================================================
from alignment.alignment_entity import AlignmentEntity
import math

class ArcSegment(AlignmentEntity):
    def __init__(
        self,
        start_e: float,
        start_n: float,
        start_angle: float,
        start_sta: float,
        R: float,
        length: float,
        turn_direction: int = 1
    ):
        """
        :param R: 원곡선 반경 (m, 양수)
        :param length: 원곡선 호 길이 (m, 양수)
        :param turn_direction: 좌회전 = +1, 우회전 = -1
        """
        super().__init__(start_e, start_n, start_angle, start_sta, length)
        self.R = float(R)
        self.dir = 1.0 if turn_direction >= 0 else -1.0
        self.sweep_angle = (self.length / self.R) * self.dir  # 중심각 변화량 (라디안)

        # 원곡선 중심점(Center) 계산: 시점에서 좌측(+dir)으로 R만큼 수직 이동
        to_center_angle = self.start_angle + self.dir * (math.pi * 0.5)
        self.center_e = self.start_e + self.R * math.cos(to_center_angle)
        self.center_n = self.start_n + self.R * math.sin(to_center_angle)

        # 원 중심에서 시점을 바라보는 기준 방사각
        self.start_radial_angle = math.atan2(self.start_n - self.center_n, self.start_e - self.center_e)
        self._end_angle = self.start_angle + self.sweep_angle
        end_radial = self.start_radial_angle + self.sweep_angle
        self._end_e = self.center_e + self.R * math.cos(end_radial)
        self._end_n = self.center_n + self.R * math.sin(end_radial)

    @property
    def end_pose(self):
        return self._end_e, self._end_n, self._end_angle, self.end_sta

    def point_location(self, station: float, offset: float = 0.0):
        ds = station - self.start_sta
        if ds < -1e-9 or ds > self.length + 1e-9:
            raise ValueError("측점이 원곡선 구간 범위를 벗어났습니다.")
        ds = max(0.0, min(self.length, ds))

        curr_radial = self.start_radial_angle + (ds / self.R) * self.dir
        # 좌회전(+1)일 때 우측 오프셋(+)은 반경 바깥쪽(+offset), 우회전(-1)일 때는 안쪽(-offset)
        eff_r = self.R + self.dir * offset
        ge = self.center_e + eff_r * math.cos(curr_radial)
        gn = self.center_n + eff_r * math.sin(curr_radial)
        return ge, gn

    def station_offset(self, easting: float, northing: float):
        de = easting - self.center_e
        dn = northing - self.center_n
        dist_from_center = math.hypot(de, dn)
        if dist_from_center < 1e-12:
            return None

        pt_radial = math.atan2(dn, de)
        # 시점 방사각으로부터 회전한 각도 차이 계산 (-pi ~ +pi 정규화 후 방향 정렬)
        delta_angle = (pt_radial - self.start_radial_angle) * self.dir
        delta_angle = (delta_angle + math.pi) % (2.0 * math.pi) - math.pi

        abs_sweep = abs(self.sweep_angle)
        if delta_angle < -1e-9 or delta_angle > abs_sweep + 1e-9:
            return None
        delta_angle = max(0.0, min(abs_sweep, delta_angle))

        ds = delta_angle * self.R
        curr_radial = self.start_radial_angle + delta_angle * self.dir
        proj_e = self.center_e + self.R * math.cos(curr_radial)
        proj_n = self.center_n + self.R * math.sin(curr_radial)

        # 진행 방향 우측(+) 오프셋 부호 산출
        signed_offset = (dist_from_center - self.R) * self.dir
        return self.start_sta + ds, signed_offset, proj_e, proj_n