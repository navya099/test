from core.structure.define_structure import apply_brokenchain_to_structure
from file_io.filemanager import load_structure_data, load_curve_data, load_pitch_data, load_coordinates
from shapely.geometry.linestring import LineString

class BaseRunner:
    def __init__(self):
        self.polyline = None
        self.coord_file_path = None
        self.pitch_file_path = None
        self.curve_file_path = None
        self.structure_file_path = None
        self.alignment_by_track = None
        self.pitchlist_by_track = None
        self.curve_list_by_track = None
        self.structure_list_by_track = None
        self.positions_by_track = None
        self.anticreeping_pr = None
        self.polesaver_sub = None
        self.polesaver_main = None
        self.wire_path_sub = None
        self.pole_path_sub = None
        self.pole_path_main = None
        self.wire_path_main = None
        self.offset_line_with_25 = None
        self.pole_positions = None
        self.idxlib = None
        self.airjoint_list = None
        self.pitchlist = None
        self.curvelist = None
        self.structure_list = None
        self.polyline_with_sta = None
        self.pole_processor = None
        self.wire_processor = None
        self.polesaver = None
        self.wire_path = None
        self.pole_path = None
        self.dataprocessor = None
        self.designspeed = 0
        self.iscustommode = False
        self.is_create_dxf = False
        self.track_mode = None
        self.track_direction: dict[str, int | None] = {'main': None, 'sub': None}
        self.track_distance = 0.0
        self.log_widget = None
        self.poledata = None
        self.wire_data = None
        self._cached_df = None
        self.start_station = 0.0
        self.end_station = 0.0
        self.brokenchain = 0.0
        self.tunnel_direction: dict[str, int | None] = {'main': None, 'sub': None}

    def run(self):
        raise NotImplementedError("자식 클래스에서 구현하세요")

    def log(self, msg):
        if self.log_widget:
            self.log_widget.insert("end", msg + "\n")
            self.log_widget.see("end")
        else:
            print(msg)

    def safe_load(self, loader_func, file_path, success_msg, empty_msg, fail_msg):
        try:
            data = loader_func(file_path)
            if data:
                self.log(success_msg)
            else:
                self.log(empty_msg)
            return data
        except Exception as e:
            self.log(f"{fail_msg} {e}")
            raise

    def base_info_load(self):
        # 파일 읽기 및 데이터 처리
        # 구조물 정보 로드
        self.structure_list = self.safe_load(
            load_structure_data,
            self.structure_file_path,
            "구조물 정보가 성공적으로 로드되었습니다.",
            "구조물 정보가 비어 있습니다.",
            "구조물 정보 로드에 실패했습니다."
        )
        if self.structure_list:
            self.structure_list = apply_brokenchain_to_structure(
                self.structure_list, self.brokenchain
            )

        # 곡선 정보 로드
        self.curvelist = self.safe_load(
            load_curve_data,
            self.curve_file_path,
            "곡선 정보가 성공적으로 로드되었습니다.",
            "곡선 정보가 비어 있습니다.",
            "곡선 정보 로드가 실패했습니다."
        )

        # 기울기 정보 로드
        self.pitchlist = self.safe_load(
            load_pitch_data,
            self.pitch_file_path,
            "기울기 정보가 성공적으로 로드되었습니다.",
            "기울기 정보가 비어 있습니다.",
            "기울기 정보 로드가 실패했습니다."
        )
        if not self.pitchlist:
            return

        # 좌표 정보 로드
        self.polyline = self.safe_load(
            load_coordinates,
            self.coord_file_path,
            "좌표 정보가 성공적으로 로드되었습니다.",
            "좌표 정보가 비어 있습니다.",
            "좌표 정보 로드가 실패했습니다."
        )
        if not self.polyline:
            return
    def create_dictionary_by_track(self):
        self.polyline_with_sta = [(i * 25, *values) for i, values in enumerate(self.polyline)]

        # LineString 생성
        if self.track_mode == 'double':

            line = LineString(self.polyline)
            # 오프셋 적용
            if self.track_direction['main'] == -1:
                direction = 'right'
            else:
                direction = 'left'
            offset_line = line.parallel_offset(abs(self.track_distance), direction, join_style=2)
            # 다시 분해후 재결합
            offset_polyline = offset_line.coords
            self.offset_line_with_25 = [(i * 25, *values) for i, values in enumerate(offset_polyline)]

        ######트랙별 처리###### todo
        # 현재는 두 트랙이 동일하다고 가정(즉 pos와 모든 구조물을 공유함)
        # 선형만 별도로 존재(offset 적용)
        # 선형 오프셋

        self.positions_by_track = {
            "main": self.pole_positions,
            "sub": self.pole_positions  # double일 때만
        }
        self.structure_list_by_track = {
            "main": self.structure_list,
            "sub": self.structure_list
        }
        self.curve_list_by_track = {
            "main": self.curvelist,
            "sub": self.curvelist
        }
        self.pitchlist_by_track = {
            "main": self.pitchlist,
            "sub": self.pitchlist
        }
        self.alignment_by_track = {
            "main": self.polyline_with_sta,
            "sub": self.offset_line_with_25
        }