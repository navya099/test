
class BranchCondition:
    """자선 분기 조건 컴포넌트
    Attributes:
        start_station: 시작 측점
        end_station: 끝 측점
        length: 길이
        target_track: 대상 선로번호
    """
    def __init__(self, start_station: int, end_station: int, target_track: int):
        self.start_station = start_station
        self.end_station = end_station
        self.length = end_station - start_station
        self.target_track = target_track