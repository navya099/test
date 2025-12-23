from dataclasses import dataclass, field
from .bracket import Bracket

@dataclass
class Rail:
    name: str
    index: int
    brackets: list[Bracket] = field(default_factory=list)
