# ==============================================================================
# 1. 순수 도메인 객체 (Domain Models / Entities)
# ==============================================================================
class ProfileEntity:
    """종단 선형 구성 요소의 최상위 베이스 클래스"""
    def __init__(self, start_sta: float, end_sta: float):
        self.start_sta = float(start_sta)
        self.end_sta = float(end_sta)

    def elevation_and_grade_at(self, station: float):
        raise NotImplementedError