from dataclasses import dataclass

from xref_module.objmodel.transform import Transform
from xref_module.preview.category import PreviewCategory


@dataclass
class PreviewItem:
    path: str
    transform: Transform
    category: PreviewCategory

