from core.pole.poledata import PoleDATA
from core.wire.base_wire_procsseor import BaseWireProcessor


class FPWWireProcessor(BaseWireProcessor):
    def collect_data(self, pole: PoleDATA):
        x_offset, y_offset = self.pro.get_fpw_offset(pole.structure)
        x_offset_next, y_offset_next = self.pro.get_fpw_offset(pole.next_structure)
        idx = self.pro.get_protection_wire_span(pole.span)
        if pole.side == 'L':
            x_offset *= -1
            x_offset_next *= -1
        return idx, (x_offset, y_offset), (x_offset_next, y_offset_next), "FPW"