# bveauto/context.py
from dataclasses import dataclass, field
from pathlib import Path

from .config import PathConfig, DEFAULT_PATHS, RAILTYPE_MAP


@dataclass
class BuildContext:
    designspeed: int = 150
    linecount: int = 1
    offset: float = 0.0
    brokenchain: float = 0.0
    iscustommode: bool = False

    paths: PathConfig = field(default_factory=lambda: DEFAULT_PATHS)

    # load_info 이후 채워지는 데이터
    curve_info: list = field(default_factory=list)
    pitch_info: list = field(default_factory=list)
    structure_list: list = field(default_factory=list)
    bve_coord: list = field(default_factory=list)
    start_block: float = 0.0
    last_block: float = 0.0

    @property
    def alignment_type(self) -> str:
        return RAILTYPE_MAP.get(self.designspeed, '')

    @property
    def loaded(self) -> bool:
        return bool(self.curve_info and self.structure_list)