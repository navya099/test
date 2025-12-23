from dataclasses import dataclass

from .bracket import Bracket

@dataclass
class RailData:
    name: str
    index: int
    brackets: list[Bracket]
