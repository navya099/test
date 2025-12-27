from infrastructure.structuresystem import StructureProcessor


class BaseObjectGenerator:
    def __init__(self, state, logger):
        self.state = state
        self.log = logger

    def generate(self):
        raise NotImplementedError

    def calculate_stations(self):
        bc = self.state.brokenchain or 0
        return self.state.start_station + bc, self.state.end_station + bc

    def load_structures(self):
        processor = StructureProcessor(self.state.structure_excel_path)
        processor.process_structure(self.state.brokenchain or 0)
        return processor
