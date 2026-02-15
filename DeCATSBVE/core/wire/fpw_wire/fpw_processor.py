from core.pole.poledata import PoleDATA
from core.wire.base_wire_procsseor import BaseWireProcessor


class FPWWireProcessor(BaseWireProcessor):
    def collect_data(self, pole: PoleDATA):
        _, _, x_offset, y_offset = self.pro.get_wire_offset(pole.structure)
        _, _, x_offset_next, y_offset_next = self.pro.get_wire_offset(pole.next_structure)
        _, _, idx = self.pro.get_wire_span_data(pole.span, pole.structure)
        if pole.side == 'L':
            x_offset *= -1
            x_offset_next *= -1
        return idx, (x_offset, y_offset), (x_offset_next, y_offset_next), "FPW"