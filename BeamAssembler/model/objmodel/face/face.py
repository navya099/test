# core/geometry/face.py
from dataclasses import dataclass

@dataclass(frozen=True)
class Face:
    a: int
    b: int
    c: int

    def indices(self) -> tuple[int, int, int]:
        return self.a, self.b, self.c