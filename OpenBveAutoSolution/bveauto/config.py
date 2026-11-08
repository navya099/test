# bveauto/config.py
from dataclasses import dataclass, field
from pathlib import Path

RAILTYPE_MAP = {120: '도시철도', 150: '일반철도', 250: '준고속철도', 350: '고속철도'}


@dataclass(frozen=True)
class PathConfig:
    """모든 경로를 한 곳에서 관리. 환경 이식성을 위해 파일/JSON으로 분리 가능."""
    base_source: Path = Path('c:/temp/')
    route: Path = Path('D:/BVE/루트/Railway/Route/연습용루트/')
    obj: Path = Path('D:/BVE/루트/Railway/Object/abcdefg/')

    def work(self, sub: str) -> Path:
        return Path('c:/temp') / sub / 'result'

    def source(self, sub: str, alignment_type: str) -> Path:
        return self.base_source / sub / '소스' / alignment_type

    def target(self, sub: str) -> Path:
        return self.obj / sub

    def ensure(self, p: Path) -> Path:
        p.mkdir(parents=True, exist_ok=True)
        return p


DEFAULT_PATHS = PathConfig()