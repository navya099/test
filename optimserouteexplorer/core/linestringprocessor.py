# core/linestringprocessor.py
"""
LineString 처리: 각도 계산, 급각 정점 조정, 호 결합, 재샘플링.

설계 원칙:
- angles 길이는 항상 len(coords) - 2 (NaN 허용)
- 중복점(norm=0) 은 NaN 으로 표시 → 정점 유지
- _adjust_linestring 은 angles 와 정점을 1:1 매칭
"""
import logging

import numpy as np
from shapely.geometry import LineString, Point

from xref.utils.math_utils import draw_arc

logger = logging.getLogger(__name__)


class LineStringProcessor:
    def __init__(self, linestring: LineString):
        self.stations: list[float] = []
        self.linestring = linestring
        self.angles: list[float] = []

    # ------------------------------------------------------------------
    def process_linestring(self, tolerance: float = 60):
        """각도 계산 → 급각 정점 조정 → 각도 재계산."""
        self._calculate_angles()
        self._adjust_linestring(tolerance)
        self._calculate_angles()

    def compute_angles_only(self) -> list[float]:
        """각도만 계산 (정점 조정 없음). GA crossover 후 사용."""
        self._calculate_angles()
        return self.angles

    # ------------------------------------------------------------------
    def _calculate_angles(self):
        """
        각 중간 정점의 내부 각도 계산.
        angles 길이 = len(coords) - 2. 중복점은 NaN.
        """
        coords = np.asarray(self.linestring.coords, dtype=float)
        if len(coords) < 3:
            self.angles = []
            return

        vectors_prev = coords[1:-1] - coords[:-2]
        vectors_next = coords[2:] - coords[1:-1]
        norms_prev = np.linalg.norm(vectors_prev, axis=1)
        norms_next = np.linalg.norm(vectors_next, axis=1)

        angles_full = np.full(len(coords) - 2, np.nan, dtype=float)
        valid = (norms_prev > 0) & (norms_next > 0)

        if valid.any():
            dot = np.einsum('ij,ij->i', vectors_prev[valid], vectors_next[valid])
            denom = norms_prev[valid] * norms_next[valid]
            cos = np.clip(dot / denom, -1.0, 1.0)
            angles_full[valid] = np.degrees(np.arccos(cos))

        self.angles = angles_full.tolist()

    def _adjust_linestring(self, tolerance: float = 60):
        """각도가 tolerance 초과인 중간 정점 제거. NaN 은 유지."""
        coords = list(self.linestring.coords)
        if len(coords) <= 2:
            return

        new_points = [coords[0]]
        for i in range(1, len(coords) - 1):
            a = self.angles[i - 1]
            if a is None or np.isnan(a) or a <= tolerance:
                new_points.append(coords[i])
        new_points.append(coords[-1])
        self.linestring = LineString(new_points)

    # ------------------------------------------------------------------
    def create_joined_line_and_arc_linestirng(
        self,
        start_points: list[Point],
        end_points: list[Point],
        center_points: list[Point],
        direction_list: list[int],
    ):
        """선과 호를 이어서 새 LineString 생성. stations 무효화."""
        if len(start_points) == 0:
            return

        acr1, acr2 = [], []
        for i in range(len(start_points)):
            x_arc, y_arc = draw_arc(
                direction_list[i], start_points[i], end_points[i], center_points[i]
            )
            acr1.append(x_arc)
            acr2.append(y_arc)

        acr1 = [item for sublist in acr1 for item in sublist]
        acr2 = [item for sublist in acr2 for item in sublist]
        curve_coords = list(zip(acr1, acr2))
        combined_coords = (
            [self.linestring.coords[0]] + curve_coords + [self.linestring.coords[-1]]
        )
        self.linestring = LineString(combined_coords)
        self.stations = []   # 재샘플링 전까지 무효

    # ------------------------------------------------------------------
    def resample_linestring(self, interval: float = 40):
        """일정 간격으로 재샘플링. stations 갱신, 중복점 제거."""
        if self.linestring is None or len(self.linestring.coords) < 2:
            return

        total_length = self.linestring.length
        if total_length <= 0:
            return

        num_points = int(total_length // interval)
        distances = [i * interval for i in range(num_points + 1)]
        if total_length - distances[-1] > 1e-6:
            distances.append(total_length)

        new_points = [self.linestring.interpolate(d) for d in distances]

        # 인접 중복점 제거
        dedup = [new_points[0]]
        for p in new_points[1:]:
            if p.distance(dedup[-1]) > 1e-6:
                dedup.append(p)

        self.linestring = LineString(dedup)
        self.stations = [self.linestring.project(p) for p in dedup]