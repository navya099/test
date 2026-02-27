from alignment_geometry.alignment import Alignment
from alignment_geometry.rail import Rail


class AlignmentCalculator:
    def __init__(self):

        self.alignments: list[Alignment] = []

    def create_mainline(self, min_station, max_station):
        al = Alignment(name='자선')
        count = int((max_station - min_station) // 25)
        for i in range(count):
            current_station = min_station + i * 25
            al.raildata.append(Rail(current_station,railindex=0, rail_x=0.0, rail_y=0.0,object_index=0))
        return al
