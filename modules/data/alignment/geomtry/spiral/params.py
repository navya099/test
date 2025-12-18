from dataclasses import dataclass
import math
from CIVIL3D.Civil.spiralparamyype import SpiralParamType
from CIVIL3D.Civil.spiraltype import SpiralType


@dataclass
class TransitionCurveParams:
    """완화곡선 파라미터 (일본식 / 공용식 모두 지원)"""
    type: SpiralType =   SpiralType.OffsetInvalidSpiralType

    # 국철변수 (M, V, Z)
    m: float | None = None
    v: float | None = None
    z: float | None = None

    # 공용식 변수 (A, L)
    a: float | None = None
    l: float | None = None

    radius: float | None = None
    internal_angle: float | None = None
    sp_type: SpiralParamType | None = None

    _x1 = None

    def cal_params(self,
                   radius: float,
                   internal_angle: float,
                   sp_type: SpiralParamType,
                   length=None,
                   a=None,
                   m=None,
                   v=None,
                   z=None):

        self.radius = radius
        self.internal_angle = internal_angle
        self.sp_type = sp_type

        # --- 공용식(클로소이드) 계산 ---
        if sp_type == SpiralParamType.Length:
            # L 입력 → A 계산
            if length is None:
                raise ValueError("Length(L) must be provided for Length mode.")
            self.l = length
            self.a = math.sqrt(self.l * self.radius)
            self._x1 = self.solve_x1(self.l, self.radius)
        elif sp_type == SpiralParamType.AValue:
            # A 입력 → L 계산
            if a is None:
                raise ValueError("A value must be provided for AValue mode.")
            self.a = a
            self.l = (self.a ** 2) / self.radius
            self._x1 = self.solve_x1(self.l, self.radius)
        # --- 국철변수(M, V, Z) ---
        else:
            if m is None:
                raise ValueError("M value must be provided for K-mode.")
            if v is None:
                raise ValueError("V value must be provided for K-mode.")
            if z is None:
                raise ValueError("Z value must be provided for K-mode.")

            self.m = m
            self.v = v
            self.z = z
            self._x1 = self.m * self.z
            self.l = self.x1 * (1 + (math.tan(self.theta_pc) ** 2) / 10)  # 완화곡선 길이
            self.a = math.sqrt(self.l * self.radius)

    @staticmethod
    def solve_x1(l, r, tol=1e-9, max_iter=20):
        """X1역산"""
        x = l  # 초기값
        for _ in range(max_iter):
            f = x + (x ** 3) / (40 * r * r) - l
            fp = 1 + (3 * x * x) / (40 * r * r)
            x_new = x - f / fp
            if abs(x_new - x) < tol:
                return x_new
            x = x_new
        return x


    @property
    def x1(self):
        """완화곡선 횡거 X"""
        return self._x1

    @property
    def theta_pc(self):
        """PC점의 접선각 THETA"""
        return math.atan(self.x1 / (2 * self.radius))

    @property
    def x2(self):
        """완화곡선 설치후 X축으로 이동된 원곡선 중심거리"""
        return self.x1 - (self.radius * math.sin(self.theta_pc))

    @property
    def x3(self):
        """X3"""
        return self.x1 / 3
    @property
    def x4(self):
        """X4"""
        return self.x1 - self.x3
    @property
    def y1(self):
        """완화곡선 종거 Y"""
        return (self.x1 ** 2) / (6 * self.radius)

    @property
    def f(self):
        """완화곡선 중짐이 이동된 종거 F:완화곡선 설치후 중심 Y축 이동거리임"""
        return self.y1 - self.radius * (1 - math.cos(self.theta_pc))

    @property
    def k(self):
        """수평좌표차 K:완화곡선 설치후 중심 X축 이동거리임"""
        return self.f * math.tan(self.internal_angle / 2)

    @property
    def s(self):
        """이정량 S"""
        return self.f / math.cos(self.internal_angle / 2)

    @property
    def total_tangent_length(self):
        """TL"""
        return self.radius * math.tan(self.internal_angle / 2) + self.x2 + self.k

    @property
    def circle_length(self):
        """원곡선 길이 LC"""
        return self.radius * (self.internal_angle - 2 * self.theta_pc)

    @property
    def total_curve_length(self):
        """전체곡선길이 CL"""
        return self.circle_length + 2 * self.l

    @property
    def sl(self):
        """외선장 SL"""
        return self.radius * (1 / (math.cos(self.internal_angle / 2)) - 1) + self.s

    @property
    def circle_internal_angle(self):
        """원곡선교각"""
        return self.internal_angle - (2 * self.theta_pc)

    @property
    def c(self):
        """완화곡선 횡거 종거 사이각 C"""
        return math.atan(self.y1 / self.x1)

    @property
    def xb(self):
        """XB"""
        return math.pi / 2 - self.theta_pc

    @property
    def b(self):
        """B"""
        return math.pi / 2 - self.c - self.xb



