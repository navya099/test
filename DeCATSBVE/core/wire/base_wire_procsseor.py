from core.pole.poledata import PoleDATA
from core.wire.common_processor import CommonWireProcessor
from core.wire.singlewire import SingleWire


class BaseWireProcessor:
    def __init__(self, dataprocessor):
        self.pro = dataprocessor
        self.common = CommonWireProcessor()

    def process(self, pole: PoleDATA, polyline_with_sta, pitch_angle) -> SingleWire:
        idx, start, end, label = self.collect_data(pole)
        return self.common.run(polyline_with_sta, idx,
                               pole.pos, pole.next_pos,
                               pole.z, pole.next_z,
                               start=start, end=end,
                               pitch_angle=pitch_angle,
                               label=label)

    def collect_data(self, pole: PoleDATA):
        """구체적인 wire별 데이터 수집은 하위 클래스에서 구현"""
        raise NotImplementedError