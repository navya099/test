from core.pole.poledata import PoleDATA
from core.wire.base_wire_procsseor import BaseWireProcessor


class ExtraWireProcessor(BaseWireProcessor):
    def collect_data(self, pole: PoleDATA):
        extra_wire_dict = self.pro.get_extra_wire_dictionary()
        for key, value in extra_wire_dict.items():
            x_offset, y_offset = value[pole.structure].get('x'), value[pole.structure].get('y')
            x_offset_next, y_offset_next = value[pole.next_structure].get('x'), value[pole.next_structure].get('y')
            idx = self.pro.get_feeder_span(pole.span)
            # 현재 구조물 처리
            if pole.structure == '터널':
                x_offset *= -pole.side  # 터널은 항상 side 반대
            else:
                x_offset *= pole.side

            # 다음 구조물 처리
            if pole.next_structure == '터널':
                x_offset_next *= -pole.next_side  # 터널은 항상 side 반대
            else:
                x_offset_next *= pole.next_side

            return idx, (x_offset, y_offset), (x_offset_next, y_offset_next), key