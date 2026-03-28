from core.wire.common_processor import CommonWireProcessor
from utils.comom_util import initialrize_tenstion_device
from utils.math_util import calculate_curve_angle, calculate_curve_stagger
class AirjointWireProcessor:
    def __init__(self, compros: CommonWireProcessor, datap, al):
        self.common = compros
        self.datap = datap
        self.al = al

    def run(self, pole, next_pole, wire, pitch_angle ,offset, cw_index):
        # 에어조인트 구간 처리
        # 전차선 정보 가져오기,
        system_heigh, contact_height = self.datap.get_contact_wire_and_massanger_wire_info(pole.structure)
        imw_index = self.datap.get_inactive_mw_span(pole.span - 7)
        icw_index = self.datap.get_inactive_cw_span(pole.span - 7)
        # 평행구간 전차선 오프셋
        aj_start_x, aj_start_y = self.datap.get_airjoint_offset('AJ형_시점').get('x'),self.datap.get_airjoint_offset('AJ형_시점').get('y')
        f_start_x, f_start_y = self.datap.get_airjoint_offset('F형_시점').get('x'), self.datap.get_airjoint_offset('F형_시점').get('y')
        aj_middle1_x, aj_middle1_y = self.datap.get_airjoint_offset('AJ형_중간1').get('x') , self.datap.get_airjoint_offset('AJ형_중간1').get('y')
        aj_middle2_x, aj_middle2_y = self.datap.get_airjoint_offset('AJ형_중간2').get('x'), self.datap.get_airjoint_offset('AJ형_중간2').get('y')
        aj_end_x, aj_end_y = self.datap.get_airjoint_offset('AJ형_끝').get('x'), self.datap.get_airjoint_offset('AJ형_끝').get('y')
        f_end_x, f_end_y = self.datap.get_airjoint_offset('F형_끝').get('x'), self.datap.get_airjoint_offset('F형_끝').get('y')

        # 방향(side) + 터널 여부에 따라 X 좌표 반전

        # 일반 구간
        if pole.side == -1:
            aj_start_x *= -1
            f_start_x *= -1
            aj_middle1_x *= -1
        else:
            aj_middle2_x *= -1
            aj_end_x *= -1
            f_end_x *= -1

        if pole.section == '에어조인트 시작점 (1호주)':
            # 본선
            start_offset = pole.brackets[0].stagger
            start_cw_height = self.datap.get_contact_wire_height(pole.structure)
            end_cw_height = self.datap.get_contact_wire_height(next_pole.structure)
            start_system_height = self.datap.get_system_height(pole.structure)
            end_system_height = self.datap.get_system_height(next_pole.structure)
            wire.add_wire(self.common.run(
                self.al, cw_index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (start_offset,start_cw_height),(aj_start_x,end_cw_height), pitch_angle, label='본선전차선')
            )
            # 무효선
            #slope_degree1=전차선 각도, slope_degree2=조가선 각도, H1=전차선높이, H2=조가선 높이
            slope_degree1, slope_degree2, h1, h2, pererall_d, sta2 = initialrize_tenstion_device(
                pole.pos, pole.gauge, pole.span,contact_height,system_heigh, f_start_y)

            mw = self.common.run(
                self.al, imw_index, sta2, pole.next_pos, pole.z, pole.next_z,
                (pererall_d,h2),(f_start_x,end_cw_height + end_system_height), pitch_angle, label='무효조가선')

            mw.station = sta2
            wire.add_wire(mw)

            cw = self.common.run(
                self.al, icw_index, sta2, pole.next_pos, pole.z, pole.next_z,
                (pererall_d, h1), (f_start_x, end_cw_height + f_start_y), pitch_angle, label='무효전차선')
            cw.station = sta2
            wire.add_wire(cw)
        elif pole.section == '에어조인트 (2호주)':
            # 본선
            start_cw_height = self.datap.get_contact_wire_height(pole.structure)
            end_cw_height = self.datap.get_contact_wire_height(next_pole.structure)
            start_system_height = self.datap.get_system_height(pole.structure)
            end_system_height = self.datap.get_system_height(next_pole.structure)
            wire.add_wire(self.common.run(
                self.al, cw_index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (aj_start_x, start_cw_height), (aj_middle2_x, end_cw_height), pitch_angle, label='본선전차선')
            )
            # 무효선
            imw_index = self.datap.get_inactive_mw_span(pole.span)
            icw_index = self.datap.get_inactive_mw_span(pole.span)
            wire.add_wire(self.common.run(
                self.al, imw_index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (f_start_x, start_cw_height + start_system_height), (aj_middle1_x, end_cw_height + end_system_height), pitch_angle, label='무효조가선')
            )
            wire.add_wire(self.common.run(
                self.al, icw_index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (f_start_x, start_cw_height + f_start_y), (aj_middle1_x, end_cw_height), pitch_angle, label='무효전차선')
            )
        elif pole.section == '에어조인트 중간주 (3호주)':
            # 본선 >무효선 상승
            start_cw_height = self.datap.get_contact_wire_height(pole.structure)
            end_cw_height = self.datap.get_contact_wire_height(next_pole.structure)
            start_system_height = self.datap.get_system_height(pole.structure)
            end_system_height = self.datap.get_system_height(next_pole.structure)
            #본선 -> 무효전차선
            imw_index = self.datap.get_inactive_mw_span(pole.span)
            icw_index = self.datap.get_inactive_mw_span(pole.span)
            wire.add_wire(self.common.run(
                self.al, icw_index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (aj_middle2_x, start_cw_height), (f_end_x, end_cw_height + f_start_y), pitch_angle, label='무효전차선')
            )
            wire.add_wire(self.common.run(
                self.al, imw_index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (aj_middle2_x, start_cw_height + start_system_height), (f_end_x, end_cw_height + end_system_height), pitch_angle, label='무효조가선')
            )

            # 무효선 > 본선
            wire.add_wire(self.common.run(
                self.al, cw_index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (aj_middle1_x, start_cw_height), (aj_end_x, end_cw_height), pitch_angle, label='무효->본선전차선')
            )

        elif pole.section == '에어조인트 (4호주)':
            # 본선
            end_offset = next_pole.brackets[0].stagger
            start_cw_height = self.datap.get_contact_wire_height(pole.structure)
            end_cw_height = self.datap.get_contact_wire_height(next_pole.structure)
            wire.add_wire(self.common.run(
                self.al, cw_index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (aj_end_x, start_cw_height), (end_offset, end_cw_height), pitch_angle, label='본선전차선')
            )
            # 무효선
            imw_index = self.datap.get_inactive_mw_span(pole.span - 6)
            icw_index = self.datap.get_inactive_cw_span(pole.span - 6)

            # slope_degree1=전차선 각도, slope_degree2=조가선 각도, H1=전차선높이, H2=조가선 높이
            slope_degree1, slope_degree2, h1, h2, pererall_d, sta2 = initialrize_tenstion_device(
                pole.pos, pole.gauge, pole.span, contact_height, system_heigh, f_start_y)

            wire.add_wire(self.common.run(
                self.al, imw_index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (f_end_x, start_cw_height + system_heigh), (pole.next_gauge, h2), pitch_angle, label='무효조가선')
            )
            wire.add_wire(self.common.run(
                self.al, icw_index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (f_end_x, start_cw_height + f_start_y), (pole.next_gauge, h1), pitch_angle, label='무효전차선')
            )
        elif pole.section == '에어조인트 끝점 (5호주)':
            # 본선
            start_offset = pole.brackets[0].stagger
            end_offset = next_pole.brackets[0].stagger
            start_cw_height = self.datap.get_contact_wire_height(pole.structure)
            end_cw_height = self.datap.get_contact_wire_height(next_pole.structure)

            wire.add_wire(self.common.run(
                self.al, cw_index, pole.pos, pole.next_pos, pole.z, pole.next_z,
                (start_offset, start_cw_height), (end_offset, end_cw_height), pitch_angle, label='본선전차선')
            )