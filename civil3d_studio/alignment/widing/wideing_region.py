# ==============================================================================
# 1. 확폭 구간(Widening Region) 정의 데이터 구조체
# ==============================================================================
from dataclasses import dataclass


@dataclass
class WideningRegion:
    """
    Civil 3D Offset Alignment의 확폭(Widening) 및 테이퍼(Transition) 구간 정의
    - 진입 테이퍼: start_station ~ (start_station + entry_transition_len)
    - 최대 확폭 유지: (start_station + entry_transition_len) ~ (end_station - exit_transition_len)
    - 복귀 테이퍼: (end_station - exit_transition_len) ~ end_station
    """
    name: str
    start_station: float            # 확폭 테이퍼 시작 측점 (m)
    end_station: float              # 확폭 복귀 완료 측점 (m)
    widening_width: float           # 추가 확폭량 (m, 바깥쪽으로 넓어지는 양수 크기)
    entry_transition_len: float     # 진입 테이퍼 길이 (m)
    exit_transition_len: float      # 진출(복귀) 테이퍼 길이 (m)
    transition_type: str = "Smooth" # "Linear" (직선 테이퍼) 또는 "Smooth" (S자 곡선 테이퍼)