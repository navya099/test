from dataclasses import dataclass


@dataclass
class CrossTurnoutSpecComponent:
    """건넘선 분기기 제원 컴포넌트
    Attributes:
        start_length: 시작 길이
        middle_length: 중간 길이
        end_length: 끝 길이
        cross_angle: 분기각도
    """
    start_length: float = 0.0
    middle_length: float = 0.0
    end_length: float = 0.0
    cross_angle: float = 0.0