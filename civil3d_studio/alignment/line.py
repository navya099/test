# ==============================================================================
# 2. 직선 요소 (Line Segment)
# ==============================================================================
from alignment.alignment_entity import AlignmentEntity
import math

class LineSegment(AlignmentEntity):
    def __init__(self, start_e: float, start_n: float, start_angle: float, start_sta: float, length: float):
        super().__init__(start_e, start_n, start_angle, start_sta, length)

        self.cos_a = math.cos(self.start_angle)
        self.sin_a = math.sin(self.start_angle)
        self._end_e = self.start_e + self.length * self.cos_a
        self._end_n = self.start_n + self.length * self.sin_a

    @property
    def end_pose(self):
        return self._end_e, self._end_n, self.start_angle, self.end_sta

    def point_location(self, station: float, offset: float = 0.0):
        ds = station - self.start_sta
        if ds < -1e-9 or ds > self.length + 1e-9:
            raise ValueError("측점이 직선 구간 범위를 벗어났습니다.")
        ds = max(0.0, min(self.length, ds))

        # 진행 방향 우측(+) 법선 벡터: (sin_a, -cos_a)
        ge = self.start_e + ds * self.cos_a + offset * self.sin_a
        gn = self.start_n + ds * self.sin_a - offset * self.cos_a
        return ge, gn

    def station_offset(self, easting: float, northing: float):
        de = easting - self.start_e
        dn = northing - self.start_n

        # 진행 방향 단위 벡터와의 내적(투영 거리)
        ds = de * self.cos_a + dn * self.sin_a
        if ds < -1e-9 or ds > self.length + 1e-9:
            return None
        ds = max(0.0, min(self.length, ds))

        proj_e = self.start_e + ds * self.cos_a
        proj_n = self.start_n + ds * self.sin_a

        # 우측 법선 벡터 (sin_a, -cos_a)와의 내적으로 부호 있는 이격 거리 계산
        signed_offset = (easting - proj_e) * self.sin_a - (northing - proj_n) * self.cos_a
        return self.start_sta + ds, signed_offset, proj_e, proj_n

