from core.structure.define_structure import apply_brokenchain_to_structure
from file_io.filemanager import load_structure_data, load_curve_data, load_pitch_data, load_coordinates
from shapely.geometry.linestring import LineString
class ManualPoleRunner:
    """수동 모드용 메인러너
    Atrributes:
        offset_line_with_25: 상선 선형객체
        track_distance: 선로중심간격
        track_direction: 선로방향
        track_mode: 단선 복선 모드
        polyline_with_sta: 본선 선형객체
        pitchlist: 기울기 리스트
        curvelist: 곡선 리스트
        structure_list: 구조물 리스트[]{}
        brokenchain: 파정
    """
    def __init__(self, brokenchain=0.0):
        self.log_widget = None
        self.offset_line_with_25 = []
        self.track_distance = 0.0
        self.track_direction = -1
        self.track_mode = ''
        self.polyline_with_sta = []
        self.pitchlist = []
        self.curvelist = []
        self.structure_list = []
        self.brokenchain = brokenchain
        self.poledata = {'main':[], 'sub':[]}
        self.wire_data = {'main':[], 'sub':[]}
        self.airjoint_list = []
        self.pole_processor = None
        self.wire_processor = None
        self.wire_path_sub = ''
        self.wire_path_main = ''
        self.polesaver_main =   None
        self.polesaver_sub = None
        self.pole_path_main = ''
        self.pole_path_sub = ''
        self._cached_df = None

    def log(self, msg):
        if self.log_widget:
            self.log_widget.insert("end", msg + "\n")
            self.log_widget.see("end")
        else:
            print(msg)
    def run(self):
        self.load_plugin()

    def load_plugin(self):
        """플러그인 로드"""
        # 구조물 정보 로드
        self.structure_list = load_structure_data()

        if self.structure_list:
            self.log("구조물 정보가 성공적으로 로드되었습니다.")
            self.structure_list = apply_brokenchain_to_structure(self.structure_list, self.brokenchain)  # 파정 적용
        # 곡선 정보 로드
        self.curvelist = load_curve_data()
        if self.curvelist:
            self.log("곡선 정보가 성공적으로 로드되었습니다.")
        # 기울기 정보 로드
        self.pitchlist = load_pitch_data()
        if self.pitchlist:
            self.log("기울기선 정보가 성공적으로 로드되었습니다.")
        # BVE 좌표 로드
        polyline = load_coordinates()
        self.polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]

        # LineString 생성
        line = LineString(polyline)
        # 오프셋 적용
        if self.track_direction == "mainL_subR":
            direction = 'right'
        else:
            direction = 'left'
        offset_line = line.parallel_offset(abs(self.track_distance), direction, join_style=2)
        # 다시 분해후 재결합
        offset_polyline = offset_line.coords
        self.offset_line_with_25 = [(i * 25, *values) for i, values in enumerate(offset_polyline)]

        self.log('플러그인 로드가 완료되었습니다. 이제 수동으로 전주를 배치하세요')

    def unload_plugin(self):
        """플러그인 언로드(초기화용)"""
        self.polyline_with_sta = None
        self.pitchlist = None
        self.curvelist = None
        self.structure_list = None
        self.brokenchain = 0.0

