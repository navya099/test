from core.airjoint.aj_bracket_adder import AirjointBracketAdder
from core.airjoint.aj_data_context import AirjointDataContext
from core.equipment.equipment_data import EquipmentDATA
from core.pole.normal_section_processor import NormalSectionProcessor
from core.pole.tunnel_section_processor import TunnelSectionProcessor
from dataset.dataset_getter import DatasetGetter
from utils.math_util import calculate_curve_angle


class AirSectionProcessor:
    @staticmethod
    def process(pole, polyline_with_sta, dataprocessor: DatasetGetter, idxlib):
        """에어섹션 구간별 전주 데이터 생성"""
        # 데이터 가져오기
        contact_wire_fitting, messenger_wire_fittings, steady_arm_fittings = dataprocessor.get_fittings()
        mast_idx = dataprocessor.get_mast_index(pole.structure, pole.section)
        mast_name = idxlib.get_name(mast_idx)
        f_bracket_valuse = dataprocessor.get_bracket_codes(pole.structure, type='F')
        aj_bracket_values = dataprocessor.get_bracket_codes(pole.structure, type='AJ')

        # 급전선 설비 인덱스 가져오기
        feeder_idx = dataprocessor.get_feeder_insulator_idx(pole.structure)
        feeder_name =idxlib.get_name(feeder_idx)
        # 평행틀 설비 인덱스 가져오기
        spreader_idx = dataprocessor.get_spreader_idx(pole.structure, pole.section)
        spreader_name = idxlib.get_name(spreader_idx)
        #F브래킷 인상높이
        f_bracket_height = dataprocessor.get_f_bracket_height()

        # 모든 필요한 값들을 전달
        context = AirjointDataContext(
            contact_wire_fitting=contact_wire_fitting,
            messenger_wire_fittings=messenger_wire_fittings,
            steady_arm_fitting=steady_arm_fittings,
            mast_type=mast_idx,
            mast_name=mast_name,
            aj_bracket_values=aj_bracket_values,
            f_bracket_valuse=f_bracket_valuse,
            feeder_idx=feeder_idx,
            feeder_name=feeder_name,
            spreader_name=spreader_name,
            spreader_idx=spreader_idx,
            f_bracket_height=f_bracket_height
        )
        # 에어조인트 구간별 처리(2호주 ,3호주, 4호주)
        adder = AirjointBracketAdder(context, dataprocessor, idxlib)
        if pole.section == '에어섹션1구간_1호주':
            # START 구간 처리
            if pole.structure == '터널':
                TunnelSectionProcessor.process(pole, dataprocessor, idxlib)
            else:
                NormalSectionProcessor.process(pole, dataprocessor, idxlib)
            f_start_coord = dataprocessor.get_bracket_coordinates('F형_시점')
            x1, y1 = f_start_coord['x'], f_start_coord['y']
            if pole.side == -1:
                x1 *= -1
            start_angle = calculate_curve_angle(polyline_with_sta, pole.pos, pole.next_pos, pole.gauge, x1)
            en = idxlib.get_name(1247)
            pole.equipments.append(
                EquipmentDATA(name=en, index=1247, offset=(pole.gauge, 0), rotation=start_angle, type='장력장치'))
            if pole.structure != '터널':
                jiseon = idxlib.get_name(674)
                pole.equipments.append(
                    EquipmentDATA(name=jiseon, index=674, offset=(pole.gauge, 0), rotation=0, type='지선설비'))
        elif pole.section == '에어섹션1구간_2호주':
            adder.add_common_equipts(pole)
            adder.add_f_and_aj_brackets(pole)
        elif pole.section == '에어섹션1구간_3호주':
            adder.add_common_equipts(pole)
            adder.add_aj_brackets_middle(pole)
        elif pole.section == '에어섹션1구간_4호주':
            adder.add_common_equipts(pole)
            adder.add_f_and_aj_brackets(pole, end=True)
            # START 구간 처리
            if pole.structure == '터널':
                TunnelSectionProcessor.process(pole, dataprocessor, idxlib)
            else:
                NormalSectionProcessor.process(pole, dataprocessor, idxlib)
            f_start_coord = dataprocessor.get_bracket_coordinates('F형_시점')
            x1, y1 = f_start_coord['x'], f_start_coord['y']
            if pole.side == -1:
                x1 *= -1
            start_angle = calculate_curve_angle(polyline_with_sta, pole.pos, pole.next_pos, pole.gauge, x1)
            en = idxlib.get_name(1247)
            pole.equipments.append(
                EquipmentDATA(name=en, index=1247, offset=(pole.gauge, 0), rotation=start_angle, type='장력장치'))
            if pole.structure != '터널':
                jiseon = idxlib.get_name(674)
                pole.equipments.append(
                    EquipmentDATA(name=jiseon, index=674, offset=(pole.gauge, 0), rotation=0, type='지선설비'))

        elif pole.section == '에어섹션2구간_1호주':
            adder.add_common_equipts(pole)
            adder.add_f_and_aj_brackets(pole)
        elif pole.section == '에어섹션2구간_2호주':
            adder.add_common_equipts(pole)
            adder.add_aj_brackets_middle(pole)
        elif pole.section == '에어섹션2구간_3호주':
            adder.add_common_equipts(pole)
            adder.add_f_and_aj_brackets(pole, end=True)
        elif pole.section == '에어섹션2구간_4호주':
            # END 구간 처리
            en = idxlib.get_name(1247)
            if pole.structure == '터널':
                TunnelSectionProcessor.process(pole, dataprocessor, idxlib)
            else:
                NormalSectionProcessor.process(pole, dataprocessor, idxlib)
            x5, y5 = dataprocessor.get_bracket_coordinates('F형_끝').get('x'), dataprocessor.get_bracket_coordinates(
                'F형_끝').get('y')
            if pole.side == 1:
                x5 *= -1
            end_angle = calculate_curve_angle(polyline_with_sta, pole.pos, pole.next_pos, x5, pole.next_gauge)
            pole.equipments.append(
                EquipmentDATA(name=en, index=1247, offset=(pole.gauge, 0), rotation=180 + end_angle, type='장력장치'))
            if pole.structure != '터널':
                jiseon = idxlib.get_name(674)
                pole.equipments.append(
                    EquipmentDATA(name=jiseon, index=674, offset=(pole.gauge, 0), rotation=180, type='지선설비'))