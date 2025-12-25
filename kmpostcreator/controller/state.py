# controller/state.py
class AppState:
    def __init__(self):
        self.start_station = None
        self.end_station = None
        self.reverse_start = None
        self.is_reverse = False

        self.alignment_type = None
        self.target_directory = None
        self.structure_excel_path = None
