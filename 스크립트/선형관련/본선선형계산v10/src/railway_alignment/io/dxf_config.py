"""
DXF 도면 출력 설정
====================
레이어 이름/색상/선종류, 문자 높이, 심볼 크기, 오프셋 등을
사용자가 커스텀할 수 있도록 dataclass로 캡슐화.

저장 위치: ~/.railway_alignment/dxf_config.json
프리셋: 임의 경로에 JSON 저장/불러오기
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict, fields
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _default_config_path() -> Path:
    return Path.home() / ".railway_alignment" / "dxf_config.json"


# ACI 색상 (드롭다운용)
ACI_COLORS: list[tuple[int, str]] = [
    (1, "빨강"),
    (2, "노랑"),
    (3, "초록"),
    (4, "청록"),
    (5, "파랑"),
    (6, "자홍"),
    (7, "흰/검"),
    (9, "BYLAYER"),
]
ACI_BY_VALUE: dict[int, str] = dict(ACI_COLORS)


@dataclass
class LayerStyle:
    """레이어 하나의 스타일"""
    name: str
    color: int = 7           # ACI 인덱스
    linetype: str = "CONTINUOUS"


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

    # ── 크기 (m 단위, 축척 반영 전) ──
    text_height: float = 3.0
    km_symbol_radius: float = 2.0
    sym200_radius: float = 1.5
    tick_half_length: float = 1.5
    leader_length: float = 50.0
    ip_intersect_short: float = 3.0
    ip_intersect_long: float = 7.0

    # ── IP 제원표 오프셋 ──
    ip_block_line_spacing: float = 10.0

    # ── 곡선 문자 오프셋 (측점/1000 구간별) ──
    curve_text_offset_far: float = -20.0    # sta < 10km
    curve_text_offset_mid: float = -16.0    # 10~100km
    curve_text_offset_near: float = -12.0   # 100km+

    # ── 측점 간격 ──
    km_interval: int = 1000
    sym200_interval: int = 200

    # ------------------------------------------------------------------
    # 직렬화
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DXFConfig":
        kwargs: dict[str, Any] = {}
        layer_field_names = {
            f.name for f in fields(cls) if f.name.startswith("layer_")
        }
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
            logger.info("DXF 설정 파일 없음, 기본값 사용: %s", path)
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls.from_dict(data)
        except Exception:
            logger.exception("DXF 설정 로드 실패, 기본값 사용")
            return cls()

    @classmethod
    def load_or_default(cls) -> "DXFConfig":
        """앱 시작 시 자동 로드. 없으면 기본값 반환."""
        return cls.load()