"""
DXF 출력 설정
================
레이어/색상/크기/오프셋 + 축척 프리셋 + IP 블록 타입.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict, fields
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _default_config_path() -> Path:
    return Path.home() / ".railway_alignment" / "dxf_config.json"


# ACI 색상 (드롭다운용)
ACI_COLORS: list[tuple[int, str]] = [
    (1, "빨강"), (2, "노랑"), (3, "초록"), (4, "청록"),
    (5, "파랑"), (6, "자홍"), (7, "흰/검"), (9, "BYLAYER"),
]
ACI_BY_VALUE: dict[int, str] = dict(ACI_COLORS)


# ============================================================
# IP 블록 타입
# ============================================================
IP_BLOCK_TYPES: list[tuple[str, str]] = [
    ("default",  "기본 (1:1000 실시설계)"),
    ("compact",  "간략 (1:5000 기본계획)"),
    ("none",     "블록 없음"),
    # ── 미구현 ──
    ("예타_A",   "예타 타입A"),
    ("예타_B",   "예타 타입B"),
    ("예타_C",   "예타 타입C"),
    ("국가망_A", "국가망 타입A"),
    ("국가망_B", "국가망 타입B"),
    ("보도_A",   "보도용 타입A"),
    ("보도_B",   "보도용 타입B"),
]

IMPLEMENTED_BLOCK_TYPES: set[str] = {"default", "compact", "none"}


# ============================================================
# 스타일
# ============================================================
@dataclass
class LayerStyle:
    name: str
    color: int = 7
    linetype: str = "CONTINUOUS"


# ============================================================
# 설정
# ============================================================
@dataclass
class DXFConfig:
    """DXF 출력 전체 설정"""

    # ── 레이어 & 색상 ──
    layer_fl: LayerStyle = field(default_factory=lambda: LayerStyle("FL", 1))
    layer_ip_line: LayerStyle = field(default_factory=lambda: LayerStyle("IP라인", 9))
    layer_ip_intersect: LayerStyle = field(default_factory=lambda: LayerStyle("IP교점선", 1))
    layer_ip_text: LayerStyle = field(default_factory=lambda: LayerStyle("IP문자", 1))
    layer_ip_table: LayerStyle = field(default_factory=lambda: LayerStyle("IP제원표", 7))
    layer_km_symbol: LayerStyle = field(default_factory=lambda: LayerStyle("km심볼", 1))
    layer_200_symbol: LayerStyle = field(default_factory=lambda: LayerStyle("200심볼", 1))
    layer_km_text: LayerStyle = field(default_factory=lambda: LayerStyle("km문자", 1))
    layer_200_text: LayerStyle = field(default_factory=lambda: LayerStyle("200문자", 1))
    layer_aux_station: LayerStyle = field(default_factory=lambda: LayerStyle("보조측점", 1))
    layer_curve_leader: LayerStyle = field(default_factory=lambda: LayerStyle("곡선인출선", 1))
    layer_curve_text: LayerStyle = field(default_factory=lambda: LayerStyle("곡선제원문자", 1))

    # ── 크기 (m 단위, scale_factor 반영 전) ──
    text_height: float = 3.0
    km_symbol_radius: float = 2.0
    sym200_radius: float = 1.5
    tick_half_length: float = 1.5
    leader_length: float = 50.0
    ip_intersect_short: float = 3.0
    ip_intersect_long: float = 7.0

    # ── IP 제원표 오프셋 ──
    ip_block_line_spacing: float = 10.0

    # ── 곡선 문자 오프셋 ──
    curve_text_offset_far: float = -20.0
    curve_text_offset_mid: float = -16.0
    curve_text_offset_near: float = -12.0

    # ── 측점 간격 ──
    km_interval: int = 1000
    sym200_interval: int = 200

    # ── 축척 프리셋 ──
    scale_preset: str = "1:1000 실시설계"
    unit_floor: int = 20
    km_precision: int = 2

    # ── 표시 옵션 ──
    ip_block_type: str = "default"      # IP_BLOCK_TYPES의 id
    show_curve_label: bool = True
    curve_label_mode: str = "full"      # "full" | "label_only"
    show_200_text: bool = True
    show_km_text: bool = True

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DXFConfig":
        kwargs: dict[str, Any] = {}
        layer_field_names = {f.name for f in fields(cls) if f.name.startswith("layer_")}
        for k, v in data.items():
            if k in layer_field_names:
                kwargs[k] = LayerStyle(**v) if isinstance(v, dict) else v
            else:
                kwargs[k] = v
        return cls(**kwargs)

    def save(self, path: Path | None = None) -> Path:
        path = path or _default_config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("DXF 설정 저장: %s", path)
        return path

    @classmethod
    def load(cls, path: Path | None = None) -> "DXFConfig":
        path = path or _default_config_path()
        if not path.exists():
            return cls()
        try:
            return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            logger.exception("DXF 설정 로드 실패, 기본값 사용")
            return cls()

    @classmethod
    def load_or_default(cls) -> "DXFConfig":
        return cls.load()


# ============================================================
# 축척 프리셋
# ============================================================
@dataclass(frozen=True)
class ScalePreset:
    scale: int
    label: str
    unit_floor: int
    km_interval: int
    sym200_interval: int
    km_precision: int
    ip_block_type: str
    show_curve_label: bool
    curve_label_mode: str
    show_200_text: bool
    show_km_text: bool


SCALE_PRESETS: list[ScalePreset] = [
    ScalePreset(
        scale=1000, label="1:1000 실시설계",
        unit_floor=20, km_interval=1000, sym200_interval=200, km_precision=2,
        ip_block_type="default",
        show_curve_label=True, curve_label_mode="full",
        show_200_text=True, show_km_text=True,
    ),
    ScalePreset(
        scale=2000, label="1:2000",
        unit_floor=20, km_interval=1000, sym200_interval=200, km_precision=2,
        ip_block_type="default",
        show_curve_label=True, curve_label_mode="full",
        show_200_text=True, show_km_text=True,
    ),
    ScalePreset(
        scale=5000, label="1:5000 기본계획",
        unit_floor=40, km_interval=1000, sym200_interval=200, km_precision=1,
        ip_block_type="compact",
        show_curve_label=True, curve_label_mode="full",
        show_200_text=True, show_km_text=True,
    ),
    ScalePreset(
        scale=10000, label="1:10000",
        unit_floor=100, km_interval=2000, sym200_interval=400, km_precision=1,
        ip_block_type="default",       # 임시 (추후 변경)
        show_curve_label=True, curve_label_mode="label_only",
        show_200_text=False, show_km_text=True,
    ),
    ScalePreset(
        scale=25000, label="1:25000 개략",
        unit_floor=200, km_interval=5000, sym200_interval=1000, km_precision=0,
        ip_block_type="default",       # 임시 (추후 변경)
        show_curve_label=True, curve_label_mode="label_only",
        show_200_text=False, show_km_text=True,
    ),
]


def find_nearest_preset(scale: int) -> ScalePreset:
    """축척에 가장 가까운 프리셋 반환."""
    return min(SCALE_PRESETS, key=lambda p: abs(p.scale - scale))


def apply_preset_to_config(config: DXFConfig, preset: ScalePreset) -> DXFConfig:
    """프리셋 값을 config 복사본에 반영."""
    new = DXFConfig.from_dict(config.to_dict())
    new.scale_preset = preset.label
    new.unit_floor = preset.unit_floor
    new.km_interval = preset.km_interval
    new.sym200_interval = preset.sym200_interval
    new.km_precision = preset.km_precision
    new.ip_block_type = preset.ip_block_type
    new.show_curve_label = preset.show_curve_label
    new.curve_label_mode = preset.curve_label_mode
    new.show_200_text = preset.show_200_text
    new.show_km_text = preset.show_km_text
    return new