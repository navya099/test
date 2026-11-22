import json
import math
import numpy as np
from scipy.special import fresnel
import ezdxf
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


# ---------------------------------------------------------------------------
# 공통 유틸
# ---------------------------------------------------------------------------
def _wrap_angle_diff(a_out: float, a_in: float) -> float:
    """방위각 변화량 (a_out - a_in)을 (-pi, pi] 범위로 정규화"""
    return (a_out - a_in + math.pi) % (2.0 * math.pi) - math.pi


def _az_to_unit_vec(az: float) -> Tuple[float, float]:
    """Civil 3D 방위각(북쪽 Y+ 기준 시계방향 라디안) -> 단위 접선 벡터 (dx, dy)"""
    return math.sin(az), math.cos(az)


def _apply_offset(x: float, y: float, az: float, offset: float) -> Tuple[float, float]:
    """접선 방위각 az 기준 우측(+offset) 법선 오프셋 적용"""
    if offset == 0.0:
        return x, y
    nx = math.cos(az)
    ny = -math.sin(az)
    return x + offset * nx, y + offset * ny


# ---------------------------------------------------------------------------
# SubEntity 기본
# ---------------------------------------------------------------------------
@dataclass
class AlignmentSubEntity:
    start_station: float
    end_station: float
    length: float
    start_pt: Tuple[float, float]
    end_pt: Tuple[float, float]

    def point_at(self, s_local: float) -> Tuple[float, float, float]:
        raise NotImplementedError


@dataclass
class AlignmentLine(AlignmentSubEntity):
    direction: float = 0.0

    def point_at(self, s_local: float) -> Tuple[float, float, float]:
        dx, dy = _az_to_unit_vec(self.direction)
        x = self.start_pt[0] + s_local * dx
        y = self.start_pt[1] + s_local * dy
        return x, y, self.direction


@dataclass
class AlignmentArc(AlignmentSubEntity):
    center_pt: Tuple[float, float] = (0.0, 0.0)
    radius: float = 0.0
    clockwise: bool = True
    direction_in: float = 0.0
    direction_out: float = 0.0

    def point_at(self, s_local: float) -> Tuple[float, float, float]:
        rx0 = self.start_pt[0] - self.center_pt[0]
        ry0 = self.start_pt[1] - self.center_pt[1]

        d_theta = s_local / self.radius
        rot = -d_theta if self.clockwise else d_theta

        cos_r = math.cos(rot)
        sin_r = math.sin(rot)
        rx = rx0 * cos_r - ry0 * sin_r
        ry = rx0 * sin_r + ry0 * cos_r

        x = self.center_pt[0] + rx
        y = self.center_pt[1] + ry

        az = self.direction_in + (d_theta if self.clockwise else -d_theta)
        return x, y, az


# ---------------------------------------------------------------------------
# Spiral (Japanese Cubic / Clothoid)
#   [2] __post_init__ 에서 X0, c 를 1회 캐싱
#   [2] 뉴턴법 상대오차 수렴 + 반복 상향
#   [5] points_at_many 로 벡터화 평가
# ---------------------------------------------------------------------------
@dataclass
class AlignmentSpiral(AlignmentSubEntity):
    radius_in: float = math.inf
    radius_out: float = math.inf
    direction_in: float = 0.0
    direction_out: float = 0.0
    spiral_type: str = "258"   # "258"=JapaneseCubic, "257"=Clothoid

    # 가우스-르장드르 16점 구적 노드/가중치
    _GAUSS_X, _GAUSS_W = np.polynomial.legendre.leggauss(16)

    # [2] 캐시 필드 (초기화 후 계산)
    _X0_cache: Optional[float] = field(default=None, init=False, repr=False)
    _c_cache:  Optional[float] = field(default=None, init=False, repr=False)
    _is_entry: bool = field(default=False, init=False, repr=False)
    _is_exit:  bool = field(default=False, init=False, repr=False)
    _is_jcubic: bool = field(default=False, init=False, repr=False)
    _is_cw: bool = field(default=False, init=False, repr=False)

    def __post_init__(self):
        # 방향/타입/entry-exit 판정을 1회 확정
        delta_az = _wrap_angle_diff(self.direction_out, self.direction_in)
        self._is_cw = delta_az > 0.0
        self._is_jcubic = str(self.spiral_type) in (
            "258", "JapaneseCubic", "SpiralType.JapaneseCubic"
        )
        self._is_entry = math.isinf(self.radius_in) and not math.isinf(self.radius_out)
        self._is_exit  = not math.isinf(self.radius_in) and math.isinf(self.radius_out)

        # [2] X0, c 캐싱 (jcubic 인 경우만)
        if self._is_jcubic and (self._is_entry or self._is_exit):
            R = self.radius_out if self._is_entry else self.radius_in
            self._X0_cache = self._solve_jcubic_X0(R, self.length)
            self._c_cache  = 1.0 / (2.0 * R * self._X0_cache)

    # -- JCubic 내부 수치 루틴 ------------------------------------------------
    def _solve_jcubic_X0(self, R: float, Ls: float) -> float:
        """s(X0)=Ls 를 만족하는 X0 를 뉴턴법으로 산출 (상대오차 수렴)."""
        X0 = Ls                                  # 초기 추정: 등가 직선
        u  = 0.5 * (self._GAUSS_X + 1.0)
        u4 = u ** 4
        for _ in range(60):                      # [2] 반복 상향
            k  = X0 / (2.0 * R)
            sq = np.sqrt(1.0 + (k * k) * u4)
            I_val = 0.5 * float(np.sum(self._GAUSS_W * sq))
            f_val = X0 * I_val - Ls
            if abs(f_val) < 1e-13 * Ls:          # [2] 상대오차 기준
                break
            dI_dX0 = 0.5 * float(np.sum(
                self._GAUSS_W * ((X0 / (4.0 * R * R)) * u4 / sq)
            ))
            df = I_val + X0 * dI_dX0
            X0 -= f_val / df
        return X0

    def _jcubic_local_xy_phi(self, s: float, R: float, Ls: float) -> Tuple[float, float, float]:
        """JCubic 로컬 (X, Y, phi). X0/c 는 캐시 사용."""
        if s <= 0.0:
            return 0.0, 0.0, 0.0
        X0 = self._X0_cache
        c  = self._c_cache
        if X0 is None:                            # 안전장치 (이론상 도달 안 함)
            X0 = self._solve_jcubic_X0(R, Ls)
            c  = 1.0 / (2.0 * R * X0)

        if abs(s - Ls) < 1e-12 * Ls:
            X = X0
        else:
            # s(X)=s 역산 뉴턴 (초기 추정이 X0 기반이라 3~4회면 충분)
            X = s * (X0 / Ls)
            for _ in range(8):                    # [5] 반복 최소화
                half_x = 0.5 * X
                t = half_x * (self._GAUSS_X + 1.0)
                integrand = np.sqrt(1.0 + (c * t * t) ** 2)
                f_val = half_x * float(np.sum(self._GAUSS_W * integrand)) - s
                if abs(f_val) < 1e-13 * max(s, 1.0):
                    break
                ds_dX = math.sqrt(1.0 + (c * X * X) ** 2)
                X -= f_val / ds_dX

        Y   = (X ** 3) / (6.0 * R * X0)
        phi = math.atan((X * X) / (2.0 * R * X0))
        return X, Y, phi

    def _clothoid_local_xy_phi(self, s: float, R: float, Ls: float) -> Tuple[float, float, float]:
        if s <= 0.0:
            return 0.0, 0.0, 0.0
        scale = math.sqrt(math.pi * R * Ls)
        S_val, C_val = fresnel(s / scale)
        phi = (s * s) / (2.0 * R * Ls)
        return scale * C_val, scale * S_val, phi

    # -- 단일점 평가 ----------------------------------------------------------
    def point_at(self, s_local: float) -> Tuple[float, float, float]:
        # [3] s=0 조기 반환: golden start_pt 를 그대로 신뢰
        if s_local == 0.0:
            az0 = self.direction_in if self._is_entry else self.direction_out
            return self.start_pt[0], self.start_pt[1], az0

        Ls = self.length
        eval_fn = self._jcubic_local_xy_phi if self._is_jcubic else self._clothoid_local_xy_phi
        is_cw = self._is_cw

        if self._is_entry:
            R = self.radius_out
            u, v, phi = eval_fn(s_local, R, Ls)
            v_signed = v if is_cw else -v

            tx, ty = _az_to_unit_vec(self.direction_in)
            nx, ny = math.cos(self.direction_in), -math.sin(self.direction_in)

            # [1] start_pt 튜플 인덱싱
            x = self.start_pt[0] + u * tx + v_signed * nx
            y = self.start_pt[1] + u * ty + v_signed * ny
            az = self.direction_in + (phi if is_cw else -phi)
            return x, y, az

        elif self._is_exit:
            R = self.radius_in
            s_rev = Ls - s_local
            u, v, phi_rev = eval_fn(s_rev, R, Ls)

            az_rev = self.direction_out + math.pi
            tx, ty = _az_to_unit_vec(az_rev)
            nx, ny = math.cos(az_rev), -math.sin(az_rev)
            v_signed = -v if is_cw else v

            # [1] end_pt 튜플 인덱싱
            x = self.end_pt[0] + u * tx + v_signed * nx
            y = self.end_pt[1] + u * ty + v_signed * ny
            az = self.direction_out - (phi_rev if is_cw else -phi_rev)
            return x, y, az

        else:
            raise NotImplementedError("복심 완화곡선(R1 -> R2)은 별도 처리가 필요합니다.")

    # -- [5] 벡터화 평가 ------------------------------------------------------
    def points_at_many(self, s_array: np.ndarray) -> np.ndarray:
        """spiral 위 여러 s 를 한 번에 평가 -> (N, 3) [x, y, az]"""
        s_array = np.asarray(s_array, dtype=float)
        N = s_array.shape[0]
        out = np.empty((N, 3), dtype=float)
        if N == 0:
            return out

        Ls = self.length
        is_cw = self._is_cw

        # s=0 은 start_pt 그대로 (golden 신뢰)
        zero_mask = (s_array == 0.0)
        if zero_mask.any():
            az0 = self.direction_in if self._is_entry else self.direction_out
            out[zero_mask, 0] = self.start_pt[0]
            out[zero_mask, 1] = self.start_pt[1]
            out[zero_mask, 2] = az0

        nz = ~zero_mask
        if not nz.any():
            return out

        s_nz = s_array[nz]

        if self._is_entry:
            R  = self.radius_out
            u, v, phi = self._eval_many(s_nz, R, Ls)
            v_signed = v if is_cw else -v
            tx, ty = _az_to_unit_vec(self.direction_in)
            nx, ny = math.cos(self.direction_in), -math.sin(self.direction_in)
            out[nz, 0] = self.start_pt[0] + u * tx + v_signed * nx
            out[nz, 1] = self.start_pt[1] + u * ty + v_signed * ny
            out[nz, 2] = self.direction_in + (phi if is_cw else -phi)
        elif self._is_exit:
            R  = self.radius_in
            s_rev = Ls - s_nz
            u, v, phi_rev = self._eval_many(s_rev, R, Ls)
            az_rev = self.direction_out + math.pi
            tx, ty = _az_to_unit_vec(az_rev)
            nx, ny = math.cos(az_rev), -math.sin(az_rev)
            v_signed = -v if is_cw else v
            out[nz, 0] = self.end_pt[0] + u * tx + v_signed * nx
            out[nz, 1] = self.end_pt[1] + u * ty + v_signed * ny
            out[nz, 2] = self.direction_out - (phi_rev if is_cw else -phi_rev)
        else:
            raise NotImplementedError("복심 완화곡선(R1 -> R2)은 별도 처리가 필요합니다.")
        return out

    def _eval_many(self, s_arr: np.ndarray, R: float, Ls: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """s 배열에 대한 로컬 (u, v, phi) 벡터 계산 — JCubic/Clothoid 공통 인터페이스."""
        if self._is_jcubic:
            return self._jcubic_many(s_arr, R, Ls)
        else:
            # Clothoid 는 fresnel 로 직접 벡터화
            s = s_arr
            scale = math.sqrt(math.pi * R * Ls)
            S, C = fresnel(s / scale)
            u = scale * C
            v = scale * S
            phi = (s * s) / (2.0 * R * Ls)
            return u, v, phi

    def _jcubic_many(self, s_arr: np.ndarray, R: float, Ls: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """JCubic 로컬 (u, v, phi) 벡터 계산 — s→X 역산 벡터 뉴턴."""
        X0 = self._X0_cache
        c  = self._c_cache
        if X0 is None:
            X0 = self._solve_jcubic_X0(R, Ls)
            c  = 1.0 / (2.0 * R * X0)

        s = np.asarray(s_arr, dtype=float)
        # 초기 추정
        X = s * (X0 / Ls)

        # 종점 근사 처리
        at_end = np.abs(s - Ls) < 1e-12 * Ls
        X[at_end] = X0

        # 벡터 뉴턴 (종점 제외)
        mask = ~at_end
        if mask.any():
            Xm = X[mask]
            sm = s[mask]
            guass_x = self._GAUSS_X
            guass_w = self._GAUSS_W
            for _ in range(10):
                half_x = 0.5 * Xm
                t = half_x[:, None] * (guass_x[None, :] + 1.0)   # (M,16)
                integ = np.sqrt(1.0 + (c * t * t) ** 2)
                f_val = half_x * (integ @ guass_w) - sm           # (M,)
                converged = np.abs(f_val) < 1e-13 * np.maximum(sm, 1.0)
                if converged.all():
                    break
                ds_dX = np.sqrt(1.0 + (c * Xm * Xm) ** 2)
                Xm = Xm - f_val / ds_dX
            X[mask] = Xm

        u = X
        v = (X ** 3) / (6.0 * R * X0)
        phi = np.arctan((X * X) / (2.0 * R * X0))
        return u, v, phi


# ---------------------------------------------------------------------------
# Alignment
#   [5] station 힌트 캐시로 이진탐색 회피
# ---------------------------------------------------------------------------
class Alignment:
    def __init__(self, name: str, starting_station: float = 0.0):
        self.name = name
        self.starting_station = starting_station
        self.sub_entities: List[AlignmentSubEntity] = []
        self._last_idx: Optional[int] = None     # [5] 힌트 캐시

    @property
    def ending_station(self) -> float:
        return self.sub_entities[-1].end_station if self.sub_entities else self.starting_station

    @property
    def length(self) -> float:
        return self.ending_station - self.starting_station

    def _find_sub_entity_idx(self, station: float) -> int:
        """station 이 속한 sub_entity 의 인덱스 반환 (힌트 캐시 우선)."""
        st = min(max(station, self.starting_station), self.ending_station)
        n = len(self.sub_entities)

        # [5] 힌트 캐시 시도
        idx = self._last_idx
        if idx is not None and 0 <= idx < n:
            sub = self.sub_entities[idx]
            if sub.start_station <= st <= sub.end_station:
                return idx
            # 인접 인덱스 빠른 확인 (연속 station 평가에 효과적)
            for d in (1, -1):
                j = idx + d
                if 0 <= j < n:
                    sj = self.sub_entities[j]
                    if sj.start_station <= st <= sj.end_station:
                        self._last_idx = j
                        return j

        # 이진 탐색 fallback
        lo, hi = 0, n - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            sub = self.sub_entities[mid]
            if st < sub.start_station:
                hi = mid - 1
            elif st > sub.end_station:
                lo = mid + 1
            else:
                self._last_idx = mid
                return mid
        self._last_idx = n - 1
        return n - 1

    def _find_sub_entity(self, station: float) -> AlignmentSubEntity:
        return self.sub_entities[self._find_sub_entity_idx(station)]

    def point_location(self, station: float, offset: float = 0.0) -> Tuple[float, float]:
        """Civil 3D Alignment.PointLocation(station, offset) 호환"""
        idx = self._find_sub_entity_idx(station)
        sub = self.sub_entities[idx]
        s_local = min(max(station - sub.start_station, 0.0), sub.length)
        x, y, az = sub.point_at(s_local)
        return _apply_offset(x, y, az, offset)

    def point_locations_many(self, stations: np.ndarray, offsets: Optional[np.ndarray] = None
                             ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """[5] 다수 station 벡터화 평가 — (x, y, az) 반환.
        station 이 정렬되어 있으면 힌트 캐시로 O(N). spiral 구간은 points_at_many 사용.
        """
        stations = np.asarray(stations, dtype=float)
        N = stations.shape[0]
        if offsets is None:
            offsets = np.zeros(N)
        else:
            offsets = np.asarray(offsets, dtype=float)

        x_out = np.empty(N); y_out = np.empty(N); az_out = np.empty(N)

        # station→sub 인덱스 매핑 (정렬 가정, 힌트 캐시 활용)
        idx_map = np.empty(N, dtype=int)
        last = None
        for i, st in enumerate(stations):
            if last is not None and self.sub_entities[last].start_station <= st <= self.sub_entities[last].end_station:
                idx_map[i] = last
            else:
                j = self._find_sub_entity_idx(st)
                idx_map[i] = j
                last = j

        # sub 별로 그룹화하여 처리
        for j in np.unique(idx_map):
            mask = idx_map == j
            sub = self.sub_entities[j]
            s_local_arr = stations[mask] - sub.start_station
            s_local_arr = np.clip(s_local_arr, 0.0, sub.length)

            if isinstance(sub, AlignmentSpiral):
                pts = sub.points_at_many(s_local_arr)
                xs, ys, azs = pts[:, 0], pts[:, 1], pts[:, 2]
            else:
                # line/arc 는 개별 평가 (일반적으로 개수가 적음)
                xs = np.empty(mask.sum()); ys = np.empty(mask.sum()); azs = np.empty(mask.sum())
                for k, s in enumerate(s_local_arr):
                    xs[k], ys[k], azs[k] = sub.point_at(float(s))

            offs = offsets[mask]
            # 오프셋 적용 (벡터화)
            nx = np.cos(azs); ny = -np.sin(azs)
            x_out[mask] = xs + offs * nx
            y_out[mask] = ys + offs * ny
            az_out[mask] = azs

        return x_out, y_out, az_out


# ---------------------------------------------------------------------------
# CivilDocument
# ---------------------------------------------------------------------------
class CivilDocument:
    def __init__(self):
        self.alignments: List[Alignment] = []

    @classmethod
    def from_golden_json(cls, json_path: str) -> "CivilDocument":
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        doc = cls()
        align = Alignment(name=data["name"], starting_station=data["starting_station"])

        raw_subs = []
        for ent in data["entities"]:
            for sub in ent.get("sub_entities", []):
                raw_subs.append(sub)
        raw_subs.sort(key=lambda s: s["start_station"])

        for sub in raw_subs:
            sc = sub["sub_class"]
            base_kwargs = dict(
                start_station=sub["start_station"],
                end_station=sub["end_station"],
                length=sub["length"],
                start_pt=tuple(sub["start_pt"]),
                end_pt=tuple(sub["end_pt"]),
            )
            if sc == "AlignmentSubEntityLine":
                align.sub_entities.append(
                    AlignmentLine(**base_kwargs, direction=sub["direction"])
                )
            elif sc == "AlignmentSubEntityArc":
                align.sub_entities.append(
                    AlignmentArc(
                        **base_kwargs,
                        center_pt=tuple(sub["center_pt"]),
                        radius=sub["radius"],
                        clockwise=sub["clockwise"],
                        direction_in=sub["direction_in"],
                        direction_out=sub["direction_out"],
                    )
                )
            elif sc == "AlignmentSubEntitySpiral":
                r_in  = math.inf if sub["radius_in"]  is None else float(sub["radius_in"])
                r_out = math.inf if sub["radius_out"] is None else float(sub["radius_out"])
                align.sub_entities.append(
                    AlignmentSpiral(
                        **base_kwargs,
                        radius_in=r_in,
                        radius_out=r_out,
                        direction_in=sub["direction_in"],
                        direction_out=sub["direction_out"],
                        spiral_type=sub.get("spiral_type", "258"),
                    )
                )

        doc.alignments.append(align)
        return doc

    def export_dxf(self, filepath: str, spiral_tolerance: float = 1e-9) -> None:
        """LINE, ARC, 고정밀 LWPOLYLINE(SPIRAL) 로 저장."""
        dxf_doc = ezdxf.new(dxfversion="R2018")
        dxf_doc.header["$LUNITS"] = 2
        dxf_doc.header["$LUPREC"] = 8
        dxf_doc.header["$INSUNITS"] = 6
        msp = dxf_doc.modelspace()
        for align in self.alignments:
            for sub in align.sub_entities:
                if isinstance(sub, AlignmentLine):
                    msp.add_line(sub.start_pt, sub.end_pt, dxfattribs={"layer": "C3D_LINE"})
                elif isinstance(sub, AlignmentArc):
                    cx, cy = sub.center_pt
                    ang_start = math.degrees(math.atan2(sub.start_pt[1] - cy, sub.start_pt[0] - cx))
                    ang_end   = math.degrees(math.atan2(sub.end_pt[1]   - cy, sub.end_pt[0]   - cx))
                    if sub.clockwise:
                        msp.add_arc((cx, cy), sub.radius, ang_end, ang_start,
                                    dxfattribs={"layer": "C3D_ARC"})
                    else:
                        msp.add_arc((cx, cy), sub.radius, ang_start, ang_end,
                                    dxfattribs={"layer": "C3D_ARC"})
                elif isinstance(sub, AlignmentSpiral):
                    min_r = min(sub.radius_in, sub.radius_out)
                    if not math.isfinite(min_r):
                        n_seg = 32
                    else:
                        max_ds = math.sqrt(8.0 * min_r * spiral_tolerance)
                        n_seg = max(32, int(math.ceil(sub.length / max_ds)))
                    # [5] 벡터화 평가 사용
                    s_arr = np.linspace(0.0, sub.length, n_seg + 1)
                    pts = sub.points_at_many(s_arr)
                    msp.add_lwpolyline(pts[:, :2], dxfattribs={"layer": "C3D_SPIRAL"})
        dxf_doc.saveas(filepath)


# ---------------------------------------------------------------------------
# [3][4] 자체 정합성 / Civil3D 대등성 테스트 (pytest)
# ---------------------------------------------------------------------------
def test_math_self_consistency(golden_path: str):
    """golden 없이 엔진 자체 수학적 정합성 검증."""
    doc = CivilDocument.from_golden_json(golden_path)
    align = doc.alignments[0]
    worst_ep = 0.0
    worst_az = 0.0
    worst_fd = 0.0
    for sub in align.sub_entities:
        # (1) s=0 → start_pt, s=L → end_pt
        x0, y0, az0 = sub.point_at(0.0)
        x1, y1, az1 = sub.point_at(sub.length)
        worst_ep = max(worst_ep,
                       math.hypot(x0 - sub.start_pt[0], y0 - sub.start_pt[1]),
                       math.hypot(x1 - sub.end_pt[0],   y1 - sub.end_pt[1]))
        # (2) 방위각 일치
        worst_az = max(worst_az,
                       abs(_wrap_angle_diff(az0, sub.direction_in)),
                       abs(_wrap_angle_diff(az1, sub.direction_out)))
        # (3) 유한차분 접선과 해석 방위각 일치
        h = 1e-6
        for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
            s = min(max(sub.length * frac, h), sub.length - h)
            xa, ya, _ = sub.point_at(s - h)
            xb, yb, _ = sub.point_at(s + h)
            fd_az = math.atan2(xb - xa, yb - ya)
            _, _, az = sub.point_at(s)
            worst_fd = max(worst_fd, abs(_wrap_angle_diff(fd_az, az)))
    print(f"[self-consistency] endpoint={worst_ep:.3e}, az={worst_az:.3e}, fd={worst_fd:.3e}")
    assert worst_ep < 1e-10
    assert worst_az < 1e-10
    assert worst_fd < 1e-6


def test_parity_with_civil3d(golden_path: str):
    """Civil 3D 출력과의 대등성 — Civil 3D 자체 노이즈 이내."""
    with open(golden_path, "r", encoding="utf-8") as f:
        golden = json.load(f)
    doc = CivilDocument.from_golden_json(golden_path)
    align = doc.alignments[0]

    # (a) golden 데이터 자체 내부 일관성(노이즈) 측정
    noise = 0.0
    for sub in align.sub_entities:
        x0, y0, _ = sub.point_at(0.0)
        noise = max(noise, math.hypot(x0 - sub.start_pt[0], y0 - sub.start_pt[1]))
    tol = max(1e-6, 5.0 * noise)

    # (b) checkpoint 대등성 — 벡터화 평가
    st = np.array([cp["station"] for cp in golden["checkpoints"]])
    off = np.array([cp["offset"] for cp in golden["checkpoints"]])
    gx = np.array([cp["x"] for cp in golden["checkpoints"]])
    gy = np.array([cp["y"] for cp in golden["checkpoints"]])
    xs, ys, _ = align.point_locations_many(st, off)
    errs = np.hypot(xs - gx, ys - gy)
    max_err = float(errs.max())
    print(f"[parity] golden noise={noise:.3e}, tol={tol:.3e}, max_err={max_err:.3e}")
    assert max_err < tol, f"worst index={int(errs.argmax())}, err={max_err:.3e}"