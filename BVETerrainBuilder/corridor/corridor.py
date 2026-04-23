from corridor.corridor_section import CorridorSection


class Corridor:
    def __init__(self, segment_id, coords, station_start=0.0):
        self.segment_id = segment_id
        self.coords = coords
        self.sections = []
        self.station_start = station_start
        self.station_end = station_start + self._compute_length()

    def _compute_length(self):
        length = 0.0
        for i in range(len(self.coords)-1):
            x1, y1, z1 = self.coords[i]
            x2, y2, z2 = self.coords[i+1]
            dx, dy = x2-x1, y2-y1
            length += np.sqrt(dx**2 + dy**2)
        return length

    def build_sections(self, freq_rule=None):
        """
        freq_rule: dict 형태로 곡선구간에서 샘플링 간격을 더 촘촘하게 설정 가능
        예: {"curve": 10, "straight": 25}
        """
        current = []
        station = self.station_start
        for pt in self.coords:
            if is_bridge_tunnel(pt):
                if current:
                    self.sections.append(CorridorSection(current, seg_type="earthwork",
                                                         station_range=(station, station+len(current)*25)))
                    current = []
                self.sections.append(CorridorSection([pt], seg_type="structure",
                                                     station_range=(station, station)))
            else:
                current.append(pt)
            station += 25  # 기본 간격, freq_rule 적용 가능
        if current:
            self.sections.append(CorridorSection(current, seg_type="earthwork",
                                                 station_range=(station-len(current)*25, station)))

    def extract_section(self, seg_type=None, station_range=None):
        """조건에 맞는 구간만 추출"""
        result = []
        for sec in self.sections:
            if seg_type and sec.seg_type != seg_type:
                continue
            if station_range:
                s0, s1 = sec.station_range
                if not (station_range[0] <= s0 and s1 <= station_range[1]):
                    continue
            result.append(sec)
        return result