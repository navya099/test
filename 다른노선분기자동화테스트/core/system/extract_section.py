from core.component.branch_condition import BranchCondition
from core.component.section import Section

class ExtractSystem:
    """자선 구간 추출 시스템"""
    def execute(self, entities, components):
        """condition = components.get("branch_condition")
        tracks = entities.get("tracks")

        if condition and tracks:
            section = self.extract(condition, tracks)
            components["section"] = section"""
        pass
    def extract(self, condition, tracks):
        coords = []
        for sta in range(condition.start_station, condition.end_station+1, 25):
            if sta in tracks:
                coords.append(tracks[sta])
        return Section(coords)