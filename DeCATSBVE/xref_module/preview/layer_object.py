from dataclasses import dataclass
from typing import Optional

from xref_module.objmodel.csvobject import CSVObject


@dataclass
class PreviewLayerObject:
    mesh: Optional["CSVObject"] = None  # Mesh가 없는 경우 TrackLabel처럼 점만 표시 가능
    pivot: Optional[tuple[float, float, float]] = None  # 점/라벨용 좌표
    category: str = "Default"  # Beam, Column, Bracket, Track, Structure 등
    color: Optional[str] = None
    label: Optional[str] = None    # 표시용 텍스트
