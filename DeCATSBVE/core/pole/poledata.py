from dataclasses import dataclass, field

from core.bracket.bracket_data import BracketDATA
from core.equipment.equipment_data import EquipmentDATA
from core.mast.mastdata import Mast


@dataclass
class PoleDATA:
    post_number: str
    pos: int
    next_pos: int
    span: int
    gauge: float
    next_gauge: float
    structure: str
    next_structure: str
    radius: float
    cant: float
    pitch: float
    section: str
    z: float
    next_z: float
    mast: Mast
    brackets: list[BracketDATA] = field(default_factory=list)
    equipments: list[EquipmentDATA] = field(default_factory=list)
    base_type: str = ''
    next_base_type: str = ''
    coord: tuple[float, float] = (0, 0)