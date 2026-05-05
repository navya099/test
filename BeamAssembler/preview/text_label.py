from dataclasses import dataclass

@dataclass
class TextLabel:
    text: str
    point: tuple[float, float]  # 화면 좌표 (x, y)
    color: str = "black"
    fontsize: int = 10
    ha: str = "center"
    va: str = "bottom"
