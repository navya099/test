from dataclasses import dataclass

from model.objmodel.transform import Transform

@dataclass
class PreviewItem:
    path: str
    transform: Transform
