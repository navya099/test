class CorridorSection:
    """영역 분할된 코리더 섹션
    1개의 코리더에서 다중 코리더 섹션으로 분할됨
    각 센션은 아래 정보를 포함
    start_station: 시작 측점
    end_station: 끝 측점
    section_name: 영역 이름
    structure: 영역 내 구조물
    길이: 프로터피
    """
    def __init__(self, coords, start_station, end_station, section_name, structure):
        self.coords = coords
        self.section_name = section_name
        self.structure = structure      # "earthwork", "bridge", "tunnel"
        self.start_station = start_station  # (start_station, end_station)
        self.end_station = end_station
        self.meshes = {}