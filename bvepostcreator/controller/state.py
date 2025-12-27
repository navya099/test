# controller/state.py
class AppState:
    def __init__(self):
        self.start_station = 0.0
        self.end_station = 0.0
        self.reverse_start = 0.0
        self.is_reverse = False
        self.brokenchain = 0.0
        self.isbrokenchain = False
        self.alignment_type = ''
        self.structure_excel_path = ''
        self.offset = 0.0
        self.target_directory = ''
        self.work_directory = ''
        self.base_source_directory = ''
        self.posttype = ''