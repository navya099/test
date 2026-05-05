from dataclasses import dataclass

from model.objmodel.transform import Transform
from preview.category import PreviewCategory


@dataclass
class PreviewItem:
    path: str
    transform: Transform
    category: PreviewCategory

