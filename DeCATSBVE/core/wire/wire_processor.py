from core.wire.af_wire.af_processor import AFWireProcessor
from core.wire.common_processor import CommonWireProcessor
from core.wire.extra_wire.extra_wire_processor import ExtraWireProcessor
from core.wire.fpw_wire.fpw_processor import FPWWireProcessor
from core.wire.section_handler import WireSectionHandler
from core.wire.wire_data import WireData
from utils.math_util import change_permile_to_degree


class WireProcessor:
    def __init__(self, dataprocessor, polyline_with_sta, poledatas):
        self.pro = dataprocessor
        self.wires = []
        self.com = CommonWireProcessor()
        self.afp = AFWireProcessor(self.pro)
        self.fpwp = FPWWireProcessor(self.pro)
        self.etcp = ExtraWireProcessor(self.pro)
        self.al = polyline_with_sta
        self.polelist = poledatas

    def process_to_wire(self):
        """ 전주 위치에 wire를 배치하는 함수 """
        self.wires.clear()
        wirehandler = WireSectionHandler(self.com ,self.pro ,self.al)
        for pole in self.polelist:
            try:
                pitch_angle = change_permile_to_degree(pole.pitch)
                wire = WireData(pole.pos, pole.span, wires=[])
                #본선 /에어조인트구간 전차선 처리
                wirehandler.run(pole, wire, pitch_angle)
                #AF
                wire.add_wire(self.afp.process(pole, self.al, pitch_angle))
                #fpw
                wire.add_wire(self.fpwp.process(pole, self.al, pitch_angle))

                #추가 전선 처리(extra wire)
                #wire.add_wire(self.etcp.process(pole, self.al, pitch_angle))

                self.wires.append(wire)
            except Exception as e:
                print(f"process_to_WIRE 실행 중 에러 발생: {e}")
                continue
        return self.wires