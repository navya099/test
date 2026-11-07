from dataclasses import dataclass


@dataclass
class CrossTurnoutSpecComponent:
    """건넘선 분기기 제원 컴포넌트 (곡선-직선-곡선)"""
    start_length: float = 0.0      # 곡선장 (cl)
    middle_length: float = 0.0     # 직선장 (sl)
    end_length: float = 0.0        # 곡선장 (cl)
    cross_angle: float = 0.0       # 접선각 (rad)
    radius: float = 0.0            # 곡선 반지름 (R)