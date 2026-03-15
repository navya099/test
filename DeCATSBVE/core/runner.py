from core.base_runner import BaseRunner
from core.equipment.anticreepingdevice.anticreeping_device_processor import AnticreepingDeviceProcessor
from core.pole.pole_processor import PoleProcessor
from core.wire.wire_processor import WireProcessor
from utils.comom_util import distribute_pole_spacing_flexible, define_airjoint_section

class AutoRunner(BaseRunner):
    def __init__(self):
        super().__init__()

    def run(self):
        """전체 작업을 관리하는 메인 함수"""
        self.base_info_load()
        self.pole_positions = distribute_pole_spacing_flexible(self.start_station, self.end_station, curvelist=self.curvelist,structure_list=self.structure_list)
        self.create_dictionary_by_track()

        self.airjoint_list = define_airjoint_section(self.pole_positions ,airjoint_span=1600)
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