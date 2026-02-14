from core.wire.af_wire.af_processor import AFWireProcessor
from core.wire.common_processor import CommonWireProcessor
from core.wire.extra_wire.extra_wire_processor import ExtraWireProcessor
from core.wire.fpw_wire.fpw_processor import FPWWireProcessor
from core.wire.section_handler import WireSectionHandler
from core.wire.wire_data import WireData
from utils.math_util import change_permile_to_degree


class WireProcessor:
    def __init__(self, dataprocessor, polyline_by_track, poledata_by_track):
        self.pro = dataprocessor
        self.polyline_by_track = polyline_by_track   # {"main": [...], "sub": [...]}
        self.poledata_by_track = poledata_by_track   # {"main": [...], "sub": [...]}
        self.com = CommonWireProcessor()
        self.afp = AFWireProcessor(self.pro)
        self.fpwp = FPWWireProcessor(self.pro)
        self.etcp = ExtraWireProcessor(self.pro)

    def process_to_wire(self):
        results = {}
        for track_name, poles in self.poledata_by_track.items():
            wires = []
            wirehandler = WireSectionHandler(self.com, self.pro, self.polyline_by_track[track_name])
            for pole in poles:
                try:
                    pitch_angle = change_permile_to_degree(pole.pitch)
                    wire = WireData(pole.pos, pole.span, wires=[], track_name=track_name)
                    # 본선/에어조인트 구간 전차선 처리
                    wirehandler.run(pole, wire, pitch_angle)
                    # AF
                    wire.add_wire(self.afp.process(pole, self.polyline_by_track[track_name], pitch_angle))
                    # FPW
                    wire.add_wire(self.fpwp.process(pole, self.polyline_by_track[track_name], pitch_angle))
                    # 추가 전선 처리 (필요시)
                    # wire.add_wire(self.etcp.process(pole, self.polyline_by_track[track_name], pitch_angle))

                    wires.append(wire)
                except Exception as e:
                    print(f"[{track_name}] process_to_wire 실행 중 에러 발생: {e}")
                    continue
            results[track_name] = wires
        return results
