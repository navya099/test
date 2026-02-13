from core.wire.aj_wire_processor import AirjointWireProcessor


class WireSectionHandler:
    def __init__(self, commonprocessor ,dataprocseor, polyline_with_sta):
        self.compros = commonprocessor
        self.datapro = dataprocseor
        self.al = polyline_with_sta
        self.airpro = AirjointWireProcessor(self.compros, self.datapro, self.al)

    def run(self, pole, wire, pitch_angle):
        """일반개소 및 에어조인트개소 구분처리"""
        sign = -1 if pole.base_type == 'I' else 1
        next_sign = -1 if pole.next_base_type == 'I' else 1
        start_offset = sign * 0.2
        end_offset = next_sign * 0.2
        # 전차선 인덱스 얻기
        cw_index,_,_ = self.datapro.get_wire_span_data(wire.span, pole.structure)

        if pole.section is None:
            self.process_normal_section(pole, wire, pitch_angle, start_offset, end_offset, cw_index)
        else:
            self.process_airjoint_section(pole, wire, pitch_angle, start_offset, cw_index)

    def process_normal_section(self, pole, wire, pitch_angle ,offset1 ,offset2 , index):

        wire.add_wire(self.compros.run(self.al, index ,
            pole.pos, pole.next_pos ,pole.z, pole.next_z, start=(offset1,0)
            ,end=(offset2,0), pitch_angle=pitch_angle, label='전차선'))

    def process_airjoint_section(self, pole, wire, pitch_angle , offset, index):
        self.airpro.run(pole, wire, pitch_angle ,offset, index)