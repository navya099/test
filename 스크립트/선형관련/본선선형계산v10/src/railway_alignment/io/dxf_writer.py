"""
평면선형 DXF Writer 모듈
=========================
기존 create_dxf 함수를 Writer 클래스 계층으로 분리.

구조:
  DxfDocument           — DXF 생성/저장 오케스트레이션
    ├ CoordTransform    — 토목↔수학 좌표 변환
    ├ PolylineBuilder   — 선형/폴리라인
    ├ IPBlockWriter     — IP 제원표 블록
    ├ StationSymbolWriter — 측점 심볼/문자/보조선
    └ IPJunctionWriter  — IP 교점선
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING
from shapely.geometry.linestring  import LineString
import ezdxf

from src.railway_alignment.core.constant_config import Config
from src.railway_alignment.core.math_util import degrees_to_dms2, calculate_destination_coordinates, format_distance, \
    calculate_bearing
from src.railway_alignment.core.models import StationRow, CurveParams
from src.railway_alignment.io.civil3d_wirter import dxf_save_with_retry

logger = logging.getLogger(__name__)


# ============================================================
# 좌표 변환 유틸
# ============================================================
class CoordTransform:
    """토목좌표(X=North, Y=East) ↔ 수학좌표(x=East, y=North) 변환"""

    @staticmethod
    def to_math(coord: tuple[float, float]) -> tuple[float, float]:
        """(X, Y) → (y, x)"""
        return (coord[1], coord[0])

    @staticmethod
    def to_civil(coord: tuple[float, float]) -> tuple[float, float]:
        """(y, x) → (X, Y)"""
        return (coord[1], coord[0])

    @staticmethod
    def list_to_math(coords: list[tuple[float, float]]) -> list[tuple[float, float]]:
        return [(y, x) for x, y in coords]

    @staticmethod
    def linestring_to_math(linestring: LineString) -> list[tuple[float, float]]:
        return [(y, x) for x, y in linestring.coords]


# ============================================================
# DXF 스타일 상수
# ============================================================
@dataclass(frozen=True)
class DxfStyle:
    """DXF 스타일/레이어 상수"""

    scale_factor: float
    text_height: float

    # 레이어명
    LAYER_FL = "FL"
    LAYER_IP_LINE = "IP라인"
    LAYER_IP_TABLE = "IP제원표"
    LAYER_IP_TEXT = "IP문자"
    LAYER_IP_JUNCTION = "IP교점선"
    LAYER_KM_SYMBOL = "km심볼"
    LAYER_KM_TEXT = "km문자"
    LAYER_200_SYMBOL = "200심볼"
    LAYER_200_TEXT = "200문자"
    LAYER_AUX = "보조측점"
    LAYER_CURVE_LEADER = "곡선인출선"
    LAYER_CURVE_TEXT = "곡선제원문자"

    @classmethod
    def from_scale(cls, scale: int) -> "DxfStyle":
        factor = scale / 1000
        return cls(scale_factor=factor, text_height=3 * factor)


# ============================================================
# 폴리라인 빌더
# ============================================================
class PolylineBuilder:
    """선형(FL) 및 IP라인 폴리라인 생성"""

    def __init__(self, msp: "Modelspace", style: DxfStyle):
        self.msp = msp
        self.style = style

    def build(
        self,
        coordinates: list[tuple[float, float]],
        linestring: "LineString",
    ) -> None:
        coords_math = CoordTransform.list_to_math(coordinates)
        ls_math = CoordTransform.linestring_to_math(linestring)

        polyline = self.msp.add_lwpolyline(coords_math)
        ippolyline = self.msp.add_lwpolyline(ls_math)

        polyline.dxf.layer = self.style.LAYER_FL


        polyline.dxf.color = Config.COLOR_RED
        polyline.dxf.const_width = self.style.scale_factor

        ippolyline.dxf.layer = self.style.LAYER_IP_LINE
        ippolyline.dxf.color = Config.COLOR_BYLAYER


# ============================================================
# IP 제원표 블록 Writer
# ============================================================
class IPBlockWriter:
    """IP 제원표 블록 (IP번호, IA, R, TL, CL, X, Y)"""

    TEXT_OFFSETS = [0, -10, -20, -30, -40, -50, -60]

    def __init__(self, doc: "Drawing", msp: "Modelspace", style: DxfStyle):
        self.doc = doc
        self.msp = msp
        self.style = style

    def write(self, curves: list["CurveParams"]) -> None:
        for i, curve in enumerate(curves):
            self._write_curve_block(curve, i)

    def _write_curve_block(self, curve: "CurveParams", idx: int) -> None:
        labels = self._build_labels(curve)
        block_name = f"IP_Block_{idx}"
        block = self.doc.blocks.new(name=block_name)

        for offset, label in zip(self.TEXT_OFFSETS, labels):
            coord = (curve.ip_xy[1], curve.ip_xy[0] + offset * self.style.scale_factor)
            block.add_text(label, dxfattribs={
                "insert": coord,
                "height": self.style.text_height,
                "color": Config.COLOR_WHITE,
                "layer": self.style.LAYER_IP_TABLE,
            })

        self.msp.add_blockref(block_name, insert=(0, 0))

    @staticmethod
    def _build_labels(curve: "CurveParams") -> list[str]:
        return [
            f"IP  NO. {curve.ip_no}",
            f"IA = {degrees_to_dms2(curve.ia_degree)}",
            f"R = {curve.radius:.2f}",
            f"TL = {curve.tl:.2f}",
            f"CL = {curve.cl:.2f}",
            f"X = {curve.ip_xy[0]:.4f}",
            f"Y = {curve.ip_xy[1]:.4f}",
        ]


# ============================================================
# 측점 심볼 Writer
# ============================================================
class StationSymbolWriter:
    """측점별 심볼/문자/보조선 출력

    분류:
      - km 배수   : 원 2개 + km문자 + 보조선
      - 200 배수  : 원 1개 + 200문자 + 보조선
      - unit 배수 : 보조선만
      - 기타      : 완화곡선 인출선 + 제원문자
    """

    def __init__(self, msp: "Modelspace", style: DxfStyle, unit: int):
        self.msp = msp
        self.style = style
        self.unit = unit

    def write(
        self,
        station_groups: list[list[list["StationRow"]]],
        curves: list["CurveParams"],
    ) -> None:
        for i, group in enumerate(station_groups):
            if i >= len(curves):
                logger.warning("IP %d: 대응 CurveParams 없음, 측점 심볼 스킵", i)
                continue
            curve = curves[i]
            for subgroup in group:
                # 원본 v9: 첫 IP 이후는 pop(0) → 슬라이싱으로 원본 보존
                rows = subgroup[1:] if i != 0 else subgroup
                for row in rows:
                    self._dispatch(row, curve)

    def _dispatch(self, row: "StationRow", curve: "CurveParams") -> None:
        if row.sta % 1000 == 0:
            self._write_km_marker(row)
        elif row.sta % 200 == 0:
            self._write_200_marker(row)
        elif row.sta % self.unit == 0:
            self._write_aux_tick(row)
        else:
            self._write_curve_leader(row, curve)

    # ---------- km 심볼 ----------
    def _write_km_marker(self, row: "StationRow") -> None:
        x, y = row.coord
        coord_math = (y, x)
        ta_math = self._ta_math(row.ta)

        self.msp.add_circle(
            coord_math, radius=2 * self.style.scale_factor,
            dxfattribs={"layer": self.style.LAYER_KM_SYMBOL, "color": Config.COLOR_RED},
        )
        self.msp.add_circle(
            coord_math, radius=1.5 * self.style.scale_factor,
            dxfattribs={"layer": self.style.LAYER_200_SYMBOL, "color": Config.COLOR_RED},
        )
        self.msp.add_text(
            f"{int(row.sta) // 1000}km",
            dxfattribs={
                "layer": self.style.LAYER_KM_TEXT, "insert": coord_math,
                "height": self.style.text_height, "color": Config.COLOR_RED,
                "rotation": ta_math,
            },
        )
        self._write_aux_tick(row)

    # ---------- 200 심볼 ----------
    def _write_200_marker(self, row: "StationRow") -> None:
        x, y = row.coord
        coord_math = (y, x)
        ta_math = self._ta_math(row.ta)

        self.msp.add_circle(
            coord_math, radius=1.5 * self.style.scale_factor,
            dxfattribs={"layer": self.style.LAYER_200_SYMBOL, "color": Config.COLOR_RED},
        )
        self.msp.add_text(
            str(int(row.sta) % 1000),
            dxfattribs={
                "layer": self.style.LAYER_200_TEXT, "insert": coord_math,
                "height": self.style.text_height, "color": Config.COLOR_RED,
                "rotation": ta_math,
            },
        )
        self._write_aux_tick(row)

    # ---------- 보조측점선 ----------
    def _write_aux_tick(self, row: "StationRow") -> None:
        x, y = row.coord
        ta_math = self._ta_math(row.ta)
        start = calculate_destination_coordinates(y, x, ta_math + 90, 1.5 * self.style.scale_factor)
        end = calculate_destination_coordinates(y, x, ta_math + 90, -1.5 * self.style.scale_factor)
        self.msp.add_line(
            start, end,
            dxfattribs={"layer": self.style.LAYER_AUX, "color": Config.COLOR_RED},
        )

    # ---------- 완화곡선 인출선 ----------
    def _write_curve_leader(self, row: "StationRow", curve: "CurveParams") -> None:
        x, y = row.coord
        coord_math = (y, x)
        ta_math = self._ta_math(row.ta)

        # 인출선 방향: LEFT면 +90, RIGHT면 -90
        leader_bearing = ta_math + 90 if curve.direction == "LEFT CURVE" else ta_math - 90
        end_point = calculate_destination_coordinates(
            y, x, leader_bearing, 50 * self.style.scale_factor,
        )
        self.msp.add_line(
            coord_math, end_point,
            dxfattribs={"layer": self.style.LAYER_CURVE_LEADER, "color": Config.COLOR_RED},
        )

        text_rotation = ta_math - 90
        insert_pos = self._text_insert_point(row, curve, ta_math, end_point)

        self.msp.add_text(
            f"{row.label}={format_distance(row.sta, Config.KM_PRECISION)}",
            dxfattribs={
                "layer": self.style.LAYER_CURVE_TEXT, "insert": insert_pos,
                "height": self.style.text_height, "color": Config.COLOR_RED,
                "rotation": text_rotation,
            },
        )

    def _text_insert_point(
        self, row: "StationRow", curve: "CurveParams",
        ta_math: float, leader_end: tuple[float, float],
    ) -> tuple[float, float]:
        """문자 삽입점 (km 구간별 거리 조정 + 좌우 방향)"""
        x, y = row.coord

        if curve.direction == "LEFT CURVE":
            return leader_end  # 인출선 끝에 배치

        reverse_rot = (ta_math + 90 + 180) if curve.direction == "LEFT CURVE" \
                      else (ta_math - 90 + 180)

        km = row.sta / 1000
        if km < 10:
            dist = -20 * self.style.scale_factor
        elif km < 100:
            dist = -16 * self.style.scale_factor
        else:
            dist = -12 * self.style.scale_factor

        return calculate_destination_coordinates(y, x, reverse_rot, dist)

    @staticmethod
    def _ta_math(ta: float) -> float:
        """접선방위각 → 수학각도 변환"""
        return (450 - ta) % 360


# ============================================================
# IP 교점선 Writer
# ============================================================
class IPJunctionWriter:
    """IP 교점선 및 IP 문자 출력"""

    def __init__(self, msp: "Modelspace", style: DxfStyle):
        self.msp = msp
        self.style = style

    def write(self, linestring_math: list[tuple[float, float]]) -> None:
        for i in range(len(linestring_math) - 2):
            x1, y1 = linestring_math[i]
            x2, y2 = linestring_math[i + 1]
            x3, y3 = linestring_math[i + 2]

            v1 = calculate_bearing(x1, y1, x2, y2)
            v2 = calculate_bearing(x2, y2, x3, y3)

            # v1 시작점 (이전 방향으로 연장)
            self.msp.add_line(
                calculate_destination_coordinates(x2, y2, v1 + 180, 7 * self.style.scale_factor),
                calculate_destination_coordinates(x2, y2, v1, 3 * self.style.scale_factor),
                dxfattribs={"layer": self.style.LAYER_IP_JUNCTION, "color": Config.COLOR_RED},
            )
            # v2 시작점 (다음 방향으로 연장)
            start_pt = (x2, y2)
            self.msp.add_line(
                start_pt,
                calculate_destination_coordinates(x2, y2, v2, 7 * self.style.scale_factor),
                dxfattribs={"layer": self.style.LAYER_IP_JUNCTION, "color": Config.COLOR_RED},
            )
            # IP 문자
            self.msp.add_text(
                f"IP NO.{i + 1}",
                dxfattribs={
                    "layer": self.style.LAYER_IP_TEXT, "insert": start_pt,
                    "height": self.style.text_height, "color": Config.COLOR_RED,
                    "rotation": 0,
                },
            )


# ============================================================
# DXF 문서 오케스트레이터
# ============================================================
class DxfDocument:
    """DXF 문서 생성/저장 오케스트레이션

    기존 create_dxf 함수를 대체.
    """

    def __init__(self, scale: int = Config.DEFAULT_SCALE):
        self.doc = ezdxf.new()
        self.msp = self.doc.modelspace()
        self.style = DxfStyle.from_scale(scale)

    def build(
        self,
        coordinates: list[tuple[float, float]],
        linestring: "LineString",
        curves: list["CurveParams"],
        station_groups: list[list[list["StationRow"]]],
        unit: int,
    ) -> None:
        """모든 레이어/심볼 생성"""
        # 1) 폴리라인
        PolylineBuilder(self.msp, self.style).build(coordinates, linestring)

        # 2) IP 제원표 블록
        IPBlockWriter(self.doc, self.msp, self.style).write(curves)

        # 3) 측점 심볼
        StationSymbolWriter(self.msp, self.style, unit).write(station_groups, curves)

        # 4) IP 교점선
        linestring_math = CoordTransform.linestring_to_math(linestring)
        IPJunctionWriter(self.msp, self.style).write(linestring_math)

    def save(self, filename: str) -> bool:
        """DXF 저장 (재시도 포함)"""

        return dxf_save_with_retry(self.doc, filename)


# ============================================================
# 편의 함수 (기존 create_dxf 대체)
# ============================================================
def create_dxf(
    coordinates: list[tuple[float, float]],
    linestring: "LineString",
    curves: list["CurveParams"],
    station_groups: list[list[list[StationRow]]],
    unit: int,
    filename: str = Config.DXF_FILENAME,
    scale: int = Config.DEFAULT_SCALE,
) -> None:
    """평면선형 DXF 출력

    Args:
        coordinates: 선형 폴리라인 좌표 (토목좌표)
        linestring: IP 연결선
        curves: IP별 곡선 파라미터
        station_groups: IP별 측점 그룹
        unit: 측점 간격
        filename: 출력 파일명
        scale: 축척 (1000 = 1:1000)
    """
    doc = DxfDocument(scale)
    doc.build(coordinates, linestring, curves, station_groups, unit)

    if not doc.save(filename):
        logger.error("DXF 저장 실패: %s", filename)
        raise IOError(f"DXF 저장 실패: {filename}")

    logger.info("DXF 저장 완료: %s", filename)
