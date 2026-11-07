# core/component/branch_condition.py
from dataclasses import dataclass

@dataclass(frozen=True)
class BranchCondition:
    """자선 분기 조건 컴포넌트"""
    start_station: int
    end_station: int
    target_track: int
    length: float = 0.0

    def __post_init__(self):
        if self.end_station <= self.start_station:
            raise ValueError(f"end_station({self.end_station})은 start_station({self.start_station})보다 커야 합니다.")
        # frozen=True 우회하여 length 설정
        object.__setattr__(self, 'length', float(self.end_station - self.start_station))