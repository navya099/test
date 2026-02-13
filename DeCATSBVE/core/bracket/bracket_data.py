from dataclasses import dataclass, field

from core.bracket.fitting_data import FittingDATA


@dataclass
class BracketDATA:
    bracket_type: str
    index: int
    offset: tuple[float, float] = (0, 0)
    bracket_name: str = ""
    fittings: list[FittingDATA] = field(default_factory=list)