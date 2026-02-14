from tkinter.filedialog import asksaveasfilename
import pandas as pd
from bve.bvecsv import BVECSV
from core.pole.pole_processor import PoleProcessor
from core.wire.wire_processor import WireProcessor
from dataset.dataset_getter import DatasetGetter
from dataset.dataset_manager import load_dataset
from file_io.filemanager import read_file, load_structure_data, load_curve_data, load_pitch_data, load_coordinates, \
    write_to_file
from utils.comom_util import find_last_block, distribute_pole_spacing_flexible, define_airjoint_section, \
    generate_postnumbers
from shapely.geometry.linestring import LineString

class AutoPole:
    def __init__(self, log_widget):
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
        self.track_direction = None
        self.track_distance = None
        self.log_widget = log_widget
        self.poledata = None
        self.wire_data = None
        self._cached_df = None

    def log(self, msg):
        if self.log_widget:
            self.log_widget.insert("end", msg + "\n")
            self.log_widget.see("end")
        else:
            print(msg)

    def run(self):
        """전체 작업을 관리하는 메인 함수"""

        # 파일 읽기 및 데이터 처리

        data = read_file()
        last_block = find_last_block(data)
        start_km = 0
        end_km = last_block // 1000


        # 구조물 정보 로드
        self.structure_list = load_structure_data()
        if self.structure_list:
            print("구조물 정보가 성공적으로 로드되었습니다.")

        # 곡선 정보 로드
        self.curvelist = load_curve_data()
        if self.curvelist:
            print("곡선 정보가 성공적으로 로드되었습니다.")
        # 기울기 정보 로드
        self.pitchlist = load_pitch_data()
        if self.pitchlist:
            print("기울기선 정보가 성공적으로 로드되었습니다.")
        # BVE 좌표 로드
        polyline = load_coordinates()
        self.polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]

        #데이터셋 로드,
        dataset = load_dataset(self.designspeed, self.iscustommode)
        spans, self.pole_positions = distribute_pole_spacing_flexible(start_km, end_km, spans=dataset['span_list'])
        self.airjoint_list = define_airjoint_section(self.pole_positions ,airjoint_span=1600)

        # 전주번호 추가
        post_number_lst = generate_postnumbers(self.pole_positions)
        # 데이터 처리
        self.dataprocessor = DatasetGetter(dataset)

        ######트랙별 처리###### todo
        #현재는 두 트랙이 동일하다고 가정(즉 pos와 모든 구조물을 공유함)
        #선형만 별도로 존재(offset 적용)
        #선형 오프셋

        # LineString 생성

        line = LineString(polyline)
        # 오프셋 적용
        if self.track_direction == "본선 L / 상선 R":
            direction = 'right'
        else:
            direction = 'left'
        offset_line = line.parallel_offset(abs(self.track_distance), direction, join_style=2)
        #다시 분해후 재결합
        offset_polyline = offset_line.coords
        self.offset_line_with_25 = [(i * 25, *values) for i, values in enumerate(offset_polyline)]
        positions_by_track = {
            "main": self.pole_positions,
            "sub": self.pole_positions  # double일 때만
        }
        structure_list_by_track = {
            "main": self.structure_list,
            "sub": self.structure_list
        }
        curve_list_by_track = {
            "main": self.curvelist,
            "sub": self.curvelist
        }
        pitchlist_by_track = {
            "main": self.pitchlist,
            "sub": self.pitchlist
        }
        alignment_by_track = {
            "main": self.polyline_with_sta,
            "sub": self.offset_line_with_25
        }
        self.pole_processor = PoleProcessor()

        self.poledata = self.pole_processor.process_pole_multitrack(
            positions_by_track, structure_list_by_track, curve_list_by_track, pitchlist_by_track,
            self.dataprocessor, self.airjoint_list, alignment_by_track, self.idxlib,
            self.track_mode, self.track_direction,
        )

        self.wire_processor = WireProcessor(self.dataprocessor, alignment_by_track, self.poledata)
        self.wire_data = self.wire_processor.process_to_wire()

        # 본선 저장
        self.polesaver_main = BVECSV(self.poledata["main"], self.wire_data["main"])
        pole_text_main = self.polesaver_main.create_pole_csv()
        wire_text_main = self.polesaver_main.create_wire_csv()
        self.pole_path_main = asksaveasfilename(title='본선 전주 데이터 저장')
        self.wire_path_main = asksaveasfilename(title='본선 전차선 데이터 저장')
        write_to_file(self.pole_path_main, pole_text_main)
        write_to_file(self.wire_path_main, wire_text_main)

        # 상선 저장 (이중 트랙일 때만)
        if self.track_mode == "double":
            self.polesaver_sub = BVECSV(self.poledata["sub"], self.wire_data["sub"])
            pole_text_sub = self.polesaver_sub.create_pole_csv()
            wire_text_sub = self.polesaver_sub.create_wire_csv()
            self.pole_path_sub = asksaveasfilename(title='상선 전주 데이터 저장')
            self.wire_path_sub = asksaveasfilename(title='상선 전차선 데이터 저장')
            write_to_file(self.pole_path_sub, pole_text_sub)
            write_to_file(self.wire_path_sub, wire_text_sub)

        self.log("전주와 전차선 txt가 성공적으로 저장되었습니다.")
        if self.is_create_dxf:
            print("도면 작성중.")

        # 최종 출력
        main_count = len(self.poledata.get("main", []))
        sub_count = len(self.poledata.get("sub", []))
        if self.track_mode == "single":
            self.log(f"전주 개수: 본선={main_count}개")
        else:
            self.log(f"전주 개수: 본선={main_count}개, 상선={sub_count}개")
        self.log(f"마지막 전주 위치: {positions_by_track['main'][-1]}m (종점: {int(end_km * 1000)}m)")
        self.log('모든 작업 완료')