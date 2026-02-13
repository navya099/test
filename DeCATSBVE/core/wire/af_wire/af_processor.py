from core.pole.poledata import PoleDATA
from core.wire.base_wire_procsseor import BaseWireProcessor


class AFWireProcessor(BaseWireProcessor):
    def collect_data(self, pole: PoleDATA):
        x_offset, y_offset, _, _ = self.pro.get_wire_offset(pole.structure)
        x_offset_next, y_offset_next, _, _ = self.pro.get_wire_offset(pole.next_structure)
        _,idx,_ = self.pro.get_wire_span_data(pole.span, pole.structure)
        return idx, (x_offset, y_offset), (x_offset_next, y_offset_next), "AF"