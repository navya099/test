from dataclasses import dataclass


@dataclass
class SingleWire:
    """한 개의 wire 객체"""
    index: int                # 전선 인덱스
    offset: tuple[float, float] = (0, 0)  # (x, y) 오프셋
    adjusted_angle: float = 0.0           # 평면각도
    topdown_angle: float = 0.0            # 상하각도
    label: str = ""                       # 전선 이름 (급전선, FPW, 특고압 등)
    station: float = None
    end_point: tuple[float, float] = (0, 0)  # 끝점 (x, y) 좌표
