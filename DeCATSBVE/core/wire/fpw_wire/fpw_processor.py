from core.pole.poledata import PoleDATA
from core.wire.base_wire_procsseor import BaseWireProcessor


class FPWWireProcessor(BaseWireProcessor):
    def collect_data(self, pole: PoleDATA):
        x_offset, y_offset = self.pro.get_fpw_offset(pole.structure)
        x_offset_next, y_offset_next = self.pro.get_fpw_offset(pole.next_structure)
        idx = self.pro.get_protection_wire_span(pole.span)

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

        return idx, (x_offset, y_offset), (x_offset_next, y_offset_next), "FPW"