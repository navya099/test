from core.pole.poledata import PoleDATA
from core.wire.base_wire_procsseor import BaseWireProcessor


class AFWireProcessor(BaseWireProcessor):
    def collect_data(self, pole: PoleDATA):
        x_offset, y_offset = self.pro.get_af_offset(pole.structure)
        x_offset_next, y_offset_next = self.pro.get_af_offset(pole.next_structure)
        if pole.side == "L":
            x_offset *= -1
            x_offset_next *= -1
        idx = self.pro.get_feeder_span(pole.span)
        return idx, (x_offset, y_offset), (x_offset_next, y_offset_next), "AF"