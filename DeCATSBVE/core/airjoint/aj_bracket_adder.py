from core.airjoint.aj_data_context import AirjointDataContext
from core.bracket.bracket_data import BracketDATA
from core.bracket.fitting_data import FittingDATA
from core.equipment.equipment_data import EquipmentDATA
from core.mast.mastdata import Mast
from core.pole.normal_section_processor import NormalSectionProcessor
from core.pole.poledata import PoleDATA
from enums.airjoint_section import AirJoint
from utils.math_util import calculate_curve_angle


class AirjointBracketAdder:
    def __init__(self, params: AirjointDataContext ,dataprocessor, normal_processor):
        self.params = params
        self.prosc = dataprocessor
        self.nps = normal_processor
    def add_airjoint_brackets(self, pole: PoleDATA, polyline_with_sta, idxlib):
        """에어조인트 각 구간별 브래킷 추가"""
        if pole.section == AirJoint.START.value:
            # START 구간 처리

            self.nps.process(pole, self.prosc, idxlib)
            x1, y1 = self.prosc.get_bracket_coordinates('F형_시점')
            start_angle = calculate_curve_angle(polyline_with_sta, pole.pos, pole.next_pos, pole.gauge, x1)
            pole.equipments.append(EquipmentDATA(name='스프링식 장력조절장치', index=1247, offset=(pole.gauge,0),rotation=start_angle))

        elif pole.section == AirJoint.POINT_2.value:
            # POINT_2 구간 처리
            self.add_common_equipts(pole)
            self.add_F_and_AJ_brackets(pole)

        elif pole.section == AirJoint.MIDDLE.value:
            # MIDDLE 구간 처리
            self.add_common_equipts(pole)
            self.add_AJ_brackets_middle(pole)

        elif pole.section == AirJoint.POINT_4.value:
            # POINT_4 구간 처리
            self.add_common_equipts(pole)
            self.add_F_and_AJ_brackets(pole, end=True)

        elif pole.section == AirJoint.END.value:
            # END 구간 처리
            self.nps.process(pole, self.prosc, idxlib)
            x5, y5 = self.prosc.get_bracket_coordinates('F형_끝')
            end_angle = calculate_curve_angle(polyline_with_sta, pole.pos, pole.next_pos, x5, pole.next_gauge,start=False)
            pole.equipments.append(EquipmentDATA(name='스프링식 장력조절장치', index=1247, offset=(pole.gauge,0),rotation=180 + end_angle))



    def add_F_and_AJ_brackets(self, pole, end=False):
        """F형 및 AJ형 브래킷을 추가하는 공통 함수"""
        f_i, f_o = self.params.f_bracket_valuse
        aj_i,aj_o = self.params.aj_bracket_values
        #기본 브래킷 제거
        pole.brackets.clear()
        # F형 가동 브래킷 추가
        x1, y1 = self.prosc.get_bracket_coordinates('F형_시점' if not end else 'F형_끝')
        self.add_F_bracket(pole, f_i,"가동브래킷 F형", x1, y1)

        # AJ형 가동 브래킷 추가
        x1, y1 = self.prosc.get_bracket_coordinates('AJ형_시점' if not end else 'AJ형_끝')
        self.add_AJ_bracket(pole, aj_i, '가동브래킷 AJ형', x1, y1)

    def add_F_bracket(self, pole: PoleDATA, bracket_code, bracket_name, x1, y1):
        """F형 가동 브래킷 및 금구류 추가"""
        idx1, idx2 = self.params.flat_fitting
        h = self.params.f_bracket_height
        # 브래킷 추가
        bracket = BracketDATA(
            bracket_type='F',
            index=bracket_code,
            bracket_name=bracket_name,
            offset=(0,h)
        )
        # 금구류 추가
        bracket.fittings.append(FittingDATA(index=idx1, label='조가선지지금구-F용', offset=(x1, y1)))
        bracket.fittings.append(FittingDATA(index=idx2, label='전차선지지금구-F용', offset=(x1, y1)))

        # PoleDATA에 브래킷 등록
        pole.brackets.append(bracket)

    def add_AJ_bracket(self, pole: PoleDATA, bracket_code, bracket_name, x1, y1, end=False):
        """AJ형 가동 브래킷 및 금구류 추가"""

        idx1 = self.params.airjoint_fitting
        idx2 = self.params.steady_arm_fitting[0] if not end else self.params.steady_arm_fitting[1]

        # 브래킷 추가
        bracket = BracketDATA(
            bracket_type='AJ',
            index=bracket_code,
            bracket_name=bracket_name,
            offset=(0, y1)
        )
        # 금구류 추가
        bracket.fittings.append(FittingDATA(index=idx1, label='조가선지지금구-AJ용', offset=(x1, y1)))
        bracket.fittings.append(FittingDATA(index=idx2, label='곡선당김금구', offset=(x1, y1)))

        # PoleDATA에 브래킷 등록
        pole.brackets.append(bracket)


    def add_AJ_brackets_middle(self, pole):
        """MIDDLE 구간에서 AJ형 브래킷 추가"""
        # 기본 브래킷 제거
        pole.brackets.clear()

        aj_i, aj_o = self.params.aj_bracket_values
        # AJ형 가동 브래킷 및 금구류 추가
        x1, y1 = self.prosc.get_bracket_coordinates('AJ형_중간1')
        self.add_AJ_bracket(pole, aj_i, '가동브래킷 AJ형', x1, y1)

        # AJ형 가동 브래킷 및 금구류 추가
        x1, y1 = self.prosc.get_bracket_coordinates('AJ형_중간2')
        self.add_AJ_bracket(pole, aj_o, '가동브래킷 AJ형', x1, y1)

    def add_common_equipts(self, pole):
        pole.mast = Mast(self.params.mast_name, self.params.mast_type, pole.gauge)
        feederidx = self.params.feeder_idx
        spreaderidx = self.params.spreader_idx
        pole.equipments.append(
            EquipmentDATA(name='급전선 현수 조립체', index=feederidx, offset=(pole.gauge, 0)))
        pole.equipments.append(
            EquipmentDATA(name='평행틀', index=spreaderidx, offset=(pole.gauge, 0)))