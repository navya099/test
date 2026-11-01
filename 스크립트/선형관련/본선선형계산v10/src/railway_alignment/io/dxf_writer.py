"""
평면선형 DXF Writer 모듈
=========================
DXFConfig 기반으로 레이어/색상/크기/오프셋을 커스텀.

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
from shapely.geometry.linestring import LineString
import ezdxf

from src.railway_alignment.core.constants import Config
from src.railway_alignment.core.math_util import (
    calculate_bearing,
    calculate_destination_coordinates,
    degrees_to_dms2,
    format_distance,
)
from src.railway_alignment.core.models import CurveParams, StationRow
from src.railway_alignment.io.civil3d_wirter import dxf_save_with_retry
from src.railway_alignment.io.dxf_config import DXFConfig, LayerStyle, IMPLEMENTED_BLOCK_TYPES

logger = logging.getLogger(__name__)


# ============================================================
# 좌표 변환
# ============================================================
class CoordTransform:
    """토목좌표(X=North, Y=East) ↔ 수학좌표(x=East, y=North)"""

    @staticmethod
    def to_math(coord: tuple[float, float]) -> tuple[float, float]:
        return (coord[1], coord[0])

    @staticmethod
    def to_civil(coord: tuple[float, float]) -> tuple[float, float]:
        return (coord[1], coord[0])

    @staticmethod
    def list_to_math(coords: list[tuple[float, float]]) -> list[tuple[float, float]]:
        return [(y, x) for x, y in coords]

    @staticmethod
    def linestring_to_math(linestring: LineString) -> list[tuple[float, float]]:
        return [(y, x) for x, y in linestring.coords]


# ============================================================
# 런타임 스타일 (scale 반영 계산값 + config 원본)
# ============================================================
@dataclass(frozen=True)
class DxfStyle:
    """DXF 스타일 런타임 계산값 + config 참조"""

    config: DXFConfig
    scale_factor: float

    @property
    def layer_km_symbol(self): return self.config.layer_km_symbol

    @property
    def layer_sub_symbol(self): return self.config.layer_sub_symbol

    @property
    def layer_km_text(self): return self.config.layer_km_text

    @property
    def layer_sub_text(self): return self.config.layer_sub_text

    @property
    def layer_aux(self): return self.config.layer_aux_station

    @classmethod
    def from_scale(cls, scale: int, config: DXFConfig | None = None) -> "DxfStyle":
        return cls(
            config=config or DXFConfig(),
            scale_factor=scale / 1000,
        )

    # ---- 계산된 크기 (m 단위 × scale_factor) ----
    @property
    def text_height(self) -> float:
        return self.config.text_height * self.scale_factor

    def length(self, meters: float) -> float:
        """config의 m 단위 값을 scale 반영 길이로."""
        return meters * self.scale_factor

    # ---- 레이어 헬퍼 ----
    @property
    def layer_fl(self) -> LayerStyle:
        return self.config.layer_fl

    @property
    def layer_ip_line(self) -> LayerStyle:
        return self.config.layer_ip_line

    @property
    def layer_ip_table(self) -> LayerStyle:
        return self.config.layer_ip_table

    @property
    def layer_ip_text(self) -> LayerStyle:
        return self.config.layer_ip_text

    @property
    def layer_ip_junction(self) -> LayerStyle:
        return self.config.layer_ip_intersect


    @property
    def layer_curve_leader(self) -> LayerStyle:
        return self.config.layer_curve_leader

    @property
    def layer_curve_text(self) -> LayerStyle:
        return self.config.layer_curve_text


# ============================================================
# 폴리라인 빌더
# ============================================================
class PolylineBuilder:
    def __init__(self, msp, style: DxfStyle):
        self.msp = msp
        self.style = style

    def build(
        self,
        coordinates: list[tuple[float, float]],
        linestring: LineString,
    ) -> None:
        coords_math = CoordTransform.list_to_math(coordinates)
        ls_math = CoordTransform.linestring_to_math(linestring)

        polyline = self.msp.add_lwpolyline(coords_math)
        ippolyline = self.msp.add_lwpolyline(ls_math)

        lyr_fl = self.style.layer_fl
        lyr_ip = self.style.layer_ip_line

        polyline.dxf.layer = lyr_fl.name
        polyline.dxf.color = lyr_fl.color
        polyline.dxf.const_width = self.style.scale_factor

        ippolyline.dxf.layer = lyr_ip.name
        ippolyline.dxf.color = lyr_ip.color


# ============================================================
# IP 제원표 블록 Writer
# ============================================================

class IPBlockWriter:
    """IP 제원표 블록 — ip_block_type별 분기"""

    def __init__(self, doc, msp, style: DxfStyle):
        self.doc = doc
        self.msp = msp
        self.style = style
        self.cfg = style.config

    def write(self, curves: list[CurveParams]) -> None:
        block_type = self.cfg.ip_block_type

        # 블록 없음
        if block_type == "none":
            return

        # 미구현 타입 → 명시적 예외
        if block_type not in IMPLEMENTED_BLOCK_TYPES:
            raise NotImplementedError(
                f"IP 제원표 블록 타입 '{block_type}'은 아직 구현되지 않았습니다. "
                f"지원: {sorted(IMPLEMENTED_BLOCK_TYPES)}"
            )

        for i, curve in enumerate(curves):
            labels = self._build_labels(curve, block_type)
            if labels:
                self._write_curve_block(curve, i, labels)

    def _build_labels(self, curve: CurveParams, block_type: str) -> list[str]:
        if block_type == "default":
            return [
                f"IP  NO. {curve.ip_no}",
                f"IA = {degrees_to_dms2(curve.ia_degree)}",
                f"R = {curve.radius:.2f}",
                f"TL = {curve.tl:.2f}",
                f"CL = {curve.cl:.2f}",
                f"X = {curve.ip_xy[0]:.4f}",
                f"Y = {curve.ip_xy[1]:.4f}",
            ]
        if block_type == "compact":
            return [
                f"IP  NO. {curve.ip_no}",
                f"R = {curve.radius:.2f}",
                f"TL = {curve.tl:.2f}",
            ]
        return []

    def _write_curve_block(self, curve, idx, labels):
        block_name = f"IP_Block_{idx}"
        block = self.doc.blocks.new(name=block_name)
        spacing = self.cfg.ip_block_line_spacing
        lyr = self.style.layer_ip_table

        for i, label in enumerate(labels):
            off = -i * spacing * self.style.scale_factor
            coord = (curve.ip_xy[1], curve.ip_xy[0] + off)
            block.add_text(label, dxfattribs={
                "insert": coord,
                "height": self.style.text_height,
                "color": lyr.color,
                "layer": lyr.name,
            })
        self.msp.add_blockref(block_name, insert=(0, 0))

# ============================================================
# 측점 심볼 Writer
# ============================================================
class StationSymbolWriter:
    def __init__(self, msp, style: DxfStyle, unit: int):
        self.msp = msp
        self.style = style
        self.unit = unit
        self.cfg = style.config

    def write(self, station_groups, curves):
        for i, group in enumerate(station_groups):
            if i >= len(curves):
                continue
            curve = curves[i]
            for subgroup in group:
                rows = subgroup[1:] if i != 0 else subgroup
                for row in rows:
                    self._dispatch(row, curve)

    def _dispatch(self, row: StationRow, curve: CurveParams) -> None:
        cfg = self.cfg
        sta_int = int(row.sta)

        # 1순위: main_tick (큰 원 + km 문자)
        if cfg.main_tick > 0 and sta_int % cfg.main_tick == 0:
            self._write_main_symbol(row)
            return

        # 2순위: sub_symbol (작은 원 + m 숫자)
        #   1000m 배수 지점은 제외 (main_tick 영역)
        if (cfg.sub_symbol > 0
                and sta_int % cfg.sub_symbol == 0
                and sta_int % 1000 != 0):
            self._write_sub_symbol(row)
            return

        # 3순위: sub_tick (선만)
        if cfg.sub_tick > 0 and sta_int % cfg.sub_tick == 0:
            self._write_aux_tick(row)
            return

        # 4순위: 곡선 제원 문자
        if cfg.show_curve_label:
            self._write_curve_leader(row, curve)

    def _write_main_symbol(self, row: StationRow) -> None:
        x, y = row.coord
        coord_math = (y, x)
        ta_math = self._ta_math(row.ta)
        cfg = self.cfg

        # 큰 원
        self.msp.add_circle(
            coord_math,
            radius=cfg.km_symbol_radius * self.style.scale_factor,
            dxfattribs={"layer": self.style.layer_km_symbol.name,
                        "color": self.style.layer_km_symbol.color},
        )
        # 안쪽 원
        self.msp.add_circle(
            coord_math,
            radius=cfg.sub_symbol_radius * self.style.scale_factor,
            dxfattribs={"layer": self.style.layer_sub_symbol.name,
                        "color": self.style.layer_sub_symbol.color},
        )
        # km 문자
        if cfg.show_km_text:
            km_value = int(row.sta) // 1000
            self.msp.add_text(
                f"{km_value}km",
                dxfattribs={
                    "layer": self.style.layer_km_text.name,
                    "insert": coord_math,
                    "height": self.style.text_height,
                    "color": self.style.layer_km_text.color,
                    "rotation": ta_math,
                },
            )

    def _write_sub_symbol(self, row: StationRow) -> None:
        x, y = row.coord
        coord_math = (y, x)
        ta_math = self._ta_math(row.ta)
        cfg = self.cfg

        # 작은 원
        self.msp.add_circle(
            coord_math,
            radius=cfg.sub_symbol_radius * self.style.scale_factor,
            dxfattribs={"layer": self.style.layer_sub_symbol.name,
                        "color": self.style.layer_sub_symbol.color},
        )

        # m 숫자 문자
        if cfg.show_sub_text:
            meter = int(row.sta) % 1000
            self.msp.add_text(
                str(meter),
                dxfattribs={
                    "layer": self.style.layer_sub_text.name,
                    "insert": coord_math,
                    "height": self.style.text_height,
                    "color": self.style.layer_sub_text.color,
                    "rotation": ta_math,
                },
            )

    def _write_aux_tick(self, row: StationRow) -> None:
        x, y = row.coord
        ta_math = self._ta_math(row.ta)
        half = self.cfg.tick_half_length * self.style.scale_factor
        lyr = self.style.layer_aux

        start = calculate_destination_coordinates(y, x, ta_math + 90, half)
        end = calculate_destination_coordinates(y, x, ta_math + 90, -half)
        self.msp.add_line(
            start, end,
            dxfattribs={"layer": lyr.name, "color": lyr.color},
        )

    # ---------- 완화곡선 인출선 ----------
    def _write_curve_leader(self, row: StationRow, curve: CurveParams) -> None:
        x, y = row.coord
        coord_math = (y, x)
        ta_math = self._ta_math(row.ta)
        cfg = self.cfg

        leader_lyr = self.style.layer_curve_leader
        text_lyr = self.style.layer_curve_text

        leader_bearing = (
            ta_math + 90 if curve.direction == "LEFT CURVE" else ta_math - 90
        )
        end_point = calculate_destination_coordinates(
            y, x, leader_bearing,
            cfg.leader_length * self.style.scale_factor,
        )
        self.msp.add_line(
            coord_math, end_point,
            dxfattribs={"layer": leader_lyr.name, "color": leader_lyr.color},
        )

        # ✅ 라벨 텍스트 결정
        if not row.label:
            return  # 라벨 없으면 문자 생략

        if cfg.curve_label_mode == "label_only":
            text = row.label  # "SP" / "PC" / "CP" / "PS" 만
        else:  # full
            text = f"{row.label}={format_distance(row.sta, cfg.km_precision)}"
        text_rotation = ta_math - 90
        insert_pos = self._text_insert_point(row, curve, ta_math, end_point)

        self.msp.add_text(
            f"{row.label}={format_distance(row.sta, Config.KM_PRECISION)}",
            dxfattribs={
                "layer": text_lyr.name,
                "insert": insert_pos,
                "height": self.style.text_height,
                "color": text_lyr.color,
                "rotation": text_rotation,
            },
        )

    def _text_insert_point(
        self,
        row: StationRow,
        curve: CurveParams,
        ta_math: float,
        leader_end: tuple[float, float],
    ) -> tuple[float, float]:
        x, y = row.coord
        cfg = self.cfg

        if curve.direction == "LEFT CURVE":
            return leader_end

        reverse_rot = (
            (ta_math + 90 + 180) if curve.direction == "LEFT CURVE"
            else (ta_math - 90 + 180)
        )

        km = row.sta / 1000
        if km < 10:
            offset_m = cfg.curve_text_offset_far
        elif km < 100:
            offset_m = cfg.curve_text_offset_mid
        else:
            offset_m = cfg.curve_text_offset_near

        return calculate_destination_coordinates(
            y, x, reverse_rot, offset_m * self.style.scale_factor,
        )

    @staticmethod
    def _ta_math(ta: float) -> float:
        return (450 - ta) % 360


# ============================================================
# IP 교점선 Writer
# ============================================================
class IPJunctionWriter:
    def __init__(self, msp, style: DxfStyle):
        self.msp = msp
        self.style = style
        self.cfg = style.config

    def write(self, linestring_math: list[tuple[float, float]]) -> None:
        junc_lyr = self.style.layer_ip_junction
        text_lyr = self.style.layer_ip_text

        short_len = self.cfg.ip_intersect_short * self.style.scale_factor
        long_len = self.cfg.ip_intersect_long * self.style.scale_factor

        for i in range(len(linestring_math) - 2):
            x1, y1 = linestring_math[i]
            x2, y2 = linestring_math[i + 1]
            x3, y3 = linestring_math[i + 2]

            v1 = calculate_bearing(x1, y1, x2, y2)
            v2 = calculate_bearing(x2, y2, x3, y3)

            self.msp.add_line(
                calculate_destination_coordinates(x2, y2, v1 + 180, long_len),
                calculate_destination_coordinates(x2, y2, v1, short_len),
                dxfattribs={"layer": junc_lyr.name, "color": junc_lyr.color},
            )
            start_pt = (x2, y2)
            self.msp.add_line(
                start_pt,
                calculate_destination_coordinates(x2, y2, v2, long_len),
                dxfattribs={"layer": junc_lyr.name, "color": junc_lyr.color},
            )
            self.msp.add_text(
                f"IP NO.{i + 1}",
                dxfattribs={
                    "layer": text_lyr.name,
                    "insert": start_pt,
                    "height": self.style.text_height,
                    "color": text_lyr.color,
                    "rotation": 0,
                },
            )


# ============================================================
# DXF 문서 오케스트레이터
# ============================================================
class DxfDocument:
    def __init__(self, scale: int = Config.DEFAULT_SCALE, config: DXFConfig | None = None):
        self.config = config or DXFConfig()
        self.doc = ezdxf.new()
        self.msp = self.doc.modelspace()
        self.style = DxfStyle.from_scale(scale, self.config)
        self._register_layers()

    def _register_layers(self) -> None:
        """config의 모든 레이어를 등록."""
        for lyr in (
            self.config.layer_fl,
            self.config.layer_ip_line,
            self.config.layer_ip_intersect,
            self.config.layer_ip_text,
            self.config.layer_ip_table,
            self.config.layer_km_symbol,
            self.config.layer_sub_symbol,
            self.config.layer_km_text,
            self.config.layer_sub_text,
            self.config.layer_aux_station,
            self.config.layer_curve_leader,
            self.config.layer_curve_text,
        ):
            if lyr.name and lyr.name not in self.doc.layers:
                self.doc.layers.new(
                    name=lyr.name,
                    dxfattribs={"color": lyr.color, "linetype": lyr.linetype},
                )

    def build(
        self,
        coordinates: list[tuple[float, float]],
        linestring: LineString,
        curves: list[CurveParams],
        station_groups: list[list[list[StationRow]]],
        unit: int,
    ) -> None:
        PolylineBuilder(self.msp, self.style).build(coordinates, linestring)
        IPBlockWriter(self.doc, self.msp, self.style).write(curves)
        StationSymbolWriter(self.msp, self.style, unit).write(station_groups, curves)
        linestring_math = CoordTransform.linestring_to_math(linestring)
        IPJunctionWriter(self.msp, self.style).write(linestring_math)

    def save(self, filename: str) -> bool:
        return dxf_save_with_retry(self.doc, filename)


# ============================================================
# 편의 함수
# ============================================================
def create_dxf(
    coordinates: list[tuple[float, float]],
    linestring: LineString,
    curves: list[CurveParams],
    station_groups: list[list[list[StationRow]]],
    unit: int,
    filename: str = Config.DXF_FILENAME,
    scale: int = Config.DEFAULT_SCALE,
    config: DXFConfig | None = None,
) -> None:
    """평면선형 DXF 출력"""
    doc = DxfDocument(scale, config)
    doc.build(coordinates, linestring, curves, station_groups, unit)

    if not doc.save(filename):
        logger.error("DXF 저장 실패: %s", filename)
        raise IOError(f"DXF 저장 실패: {filename}")

    logger.info("DXF 저장 완료: %s", filename)