from core.alignment.define_funtion import iscurve
from core.wire.aj_wire_processor import AirjointWireProcessor
from utils.math_util import calculate_curve_stagger, change_permile_to_degree


class WireSectionHandler:
    def __init__(self, commonprocessor ,dataprocseor, polyline_with_sta, curve_list):
        self.compros = commonprocessor
        self.datapro = dataprocseor
        self.al = polyline_with_sta
        self.airpro = AirjointWireProcessor(self.compros, self.datapro, self.al)
        self.curve_list = curve_list
    def run(self, pole, next_pole, wire, pitch_angle):
        """일반개소 및 에어조인트개소 구분처리"""
        if pole.side == 'L':
            sign = -1 if pole.base_type == 'I' else 1
            next_sign = -1 if pole.next_base_type == 'I' else 1
        else:
            sign = 1 if pole.base_type == 'I' else -1
            next_sign = 1 if pole.next_base_type == 'I' else -1

        start_offset = sign * 0.2
        end_offset = next_sign * 0.2
        # 전선 인덱스 얻기
        cw_index = self.datapro.get_contact_wire_span(wire.span, pole.structure)



        if pole.section is None:
            self.process_normal_section(pole,next_pole, wire, pitch_angle, start_offset, end_offset, cw_index)
        else:
            self.process_airjoint_section(pole, next_pole,wire, pitch_angle, start_offset, cw_index)

    def process_normal_section(self, pole,next_pole,  wire, pitch_angle, offset1, offset2, index):
        # 브래킷에서 stagger 직접 가져오기
        if pole.brackets and hasattr(pole.brackets[0], "stagger"):
            start_offset = pole.brackets[0].stagger
            start_cw_height = self.datapro.get_contact_wire_height(pole.structure)
        else:
            # fallback: 기본값
            start_offset = offset1
            start_cw_height = self.datapro.get_contact_wire_height(pole.structure)
        # 다음 pole도 동일하게 처리
        if next_pole.brackets and hasattr(next_pole.brackets[0], "stagger"):
            end_offset = next_pole.brackets[0].stagger
            end_cw_height = self.datapro.get_contact_wire_height(next_pole.structure)
        else:
            end_offset = offset2
            end_cw_height = self.datapro.get_contact_wire_height(next_pole.structure)
        wire.add_wire(self.compros.run(
            self.al, index,
            pole.pos, pole.next_pos, pole.z, pole.next_z,
            start=(start_offset, start_cw_height), end=(end_offset, end_cw_height),
            pitch_angle=pitch_angle, label='전차선'
        ))

    def process_airjoint_section(self, pole, next_pole, wire, pitch_angle , offset, index):
        self.airpro.run(pole, next_pole, wire, pitch_angle ,offset, index)