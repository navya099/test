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
from xref_module.index_libmgr import IndexLibrary

SHEET_ID = "1z0aUcuZCxOQp2St3icbQMbOkrSPfJK_8iZ2JKFDbW8c"
SHEET_NAME = "freeobj"  # ← 원하는 시트 이름
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"


class AutoPole:
    def __init__(self, log_widget):
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
        if self._cached_df is None:
            self._cached_df = pd.read_csv(URL)
        df = self._cached_df
        self.idxlib = IndexLibrary(df)
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
        spans, pole_positions = distribute_pole_spacing_flexible(start_km, end_km, spans=dataset['span_list'])
        self.airjoint_list = define_airjoint_section(pole_positions ,airjoint_span=1600)

        # 전주번호 추가
        post_number_lst = generate_postnumbers(pole_positions)
        # 데이터 처리
        self.dataprocessor = DatasetGetter(dataset)

        self.pole_processor = PoleProcessor()
        self.poledata = self.pole_processor.process_pole(pole_positions, self.structure_list, self.curvelist, self.pitchlist, self.dataprocessor, self.airjoint_list, self.polyline_with_sta, self.idxlib)
        self.wire_processor = WireProcessor(self.dataprocessor, self.polyline_with_sta, self.poledata)
        self.wire_data = self.wire_processor.process_to_wire()
        self.pole_path = asksaveasfilename(title='전주 데이터 저장')
        self.wire_path = asksaveasfilename(title='전차선 데이터 저장')
        self.polesaver = BVECSV(self.poledata, self.wire_data)
        pole_text = self.polesaver.create_pole_csv()
        wire_text = self.polesaver.create_wire_csv()
        write_to_file(self.pole_path, pole_text)
        write_to_file(self.wire_path, wire_text)

        self.log("전주와 전차선 txt가 성공적으로 저장되었습니다.")
        if self.is_create_dxf:
            print("도면 작성중.")

        # 최종 출력
        self.log(f"전주 개수: {len(pole_positions)}")
        self.log(f"마지막 전주 위치: {pole_positions[-1]}m (종점: {int(end_km * 1000)}m)")
        self.log('모든 작업 완료')