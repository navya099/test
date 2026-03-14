from tkinter.filedialog import asksaveasfilename
import pandas as pd
from bve.bvecsv import BVECSV
from core.equipment.anticreepingdevice.anticreeping_device_processor import AnticreepingDeviceProcessor
from core.pole.pole_processor import PoleProcessor
from core.structure.define_structure import apply_brokenchain_to_structure
from core.wire.wire_processor import WireProcessor
from dataset.dataset_getter import DatasetGetter
from dataset.dataset_manager import load_dataset
from file_io.filemanager import load_structure_data, load_curve_data, load_pitch_data, load_coordinates, \
    write_to_file
from utils.comom_util import find_last_block, distribute_pole_spacing_flexible, define_airjoint_section, \
    generate_postnumbers
from shapely.geometry.linestring import LineString

class AutoPole:
    def __init__(self):
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
        self.track_direction = {'main':None,'sub':None}
        self.track_distance = 0.0
        self.log_widget = None
        self.poledata = None
        self.wire_data = None
        self._cached_df = None
        self.start_station = 0.0
        self.end_station = 0.0
        self.brokenchain = 0.0
        self.tunnel_direction = {'main':None,'sub':None}

    def log(self, msg):
        if self.log_widget:
            self.log_widget.insert("end", msg + "\n")
            self.log_widget.see("end")
        else:
            print(msg)

    def run(self):
        """전체 작업을 관리하는 메인 함수"""

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
        polyline = self.safe_load(
            load_coordinates,
            self.coord_file_path,
            "좌표 정보가 성공적으로 로드되었습니다.",
            "좌표 정보가 비어 있습니다.",
            "좌표 정보 로드가 실패했습니다."
        )
        if not polyline:
            return

        self.polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]

        self.pole_positions = distribute_pole_spacing_flexible(self.start_station, self.end_station, curvelist=self.curvelist,structure_list=self.structure_list)
        self.airjoint_list = define_airjoint_section(self.pole_positions ,airjoint_span=1600)

        ######트랙별 처리###### todo
        #현재는 두 트랙이 동일하다고 가정(즉 pos와 모든 구조물을 공유함)
        #선형만 별도로 존재(offset 적용)
        #선형 오프셋

        # LineString 생성
        if self.track_mode == 'double':
            line = LineString(polyline)
            # 오프셋 적용
            if self.track_direction['main'] == -1:
                direction = 'right'
            else:
                direction = 'left'
            offset_line = line.parallel_offset(abs(self.track_distance), direction, join_style=2)
            #다시 분해후 재결합
            offset_polyline = offset_line.coords
            self.offset_line_with_25 = [(i * 25, *values) for i, values in enumerate(offset_polyline)]
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
        self.pole_processor = PoleProcessor()

        self.poledata = self.pole_processor.process_pole_multitrack(
            self.positions_by_track, self.structure_list_by_track, self.curve_list_by_track, self.pitchlist_by_track,
            self.dataprocessor, self.airjoint_list, self.alignment_by_track, self.idxlib,
            self.track_mode, self.track_direction,tunnel_direction=self.tunnel_direction
        )

        self.wire_processor = WireProcessor(self.dataprocessor, self.alignment_by_track, self.poledata, self.curvelist)
        self.wire_data = self.wire_processor.process_to_wire()

        #추가설비(흐름방지장치)
        self.anticreeping_pr = AnticreepingDeviceProcessor(self.poledata, self.wire_data, self.airjoint_list, self.wire_processor)
        self.anticreeping_pr.process()

        # 최종 출력
        main_count = len(self.poledata.get("main", []))
        sub_count = len(self.poledata.get("sub", []))
        if self.track_mode == "single":
            self.log(f"전주 개수: 본선={main_count}개")
        else:
            self.log(f"전주 개수: 본선={main_count}개, 상선={sub_count}개")
        self.log(f"마지막 전주 위치: {self.positions_by_track['main'][-1]}m (종점: {int(self.end_station)}m)")
        self.log('모든 작업 완료')

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